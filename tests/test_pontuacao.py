"""Cobre `pontuar`: pesos por código, saturação do grupo A, modificador de `Status`,
e a origem de cada `Motivo`. Tudo fabricado à mão — `pontuar` não toca rede nem SDK.
"""

from plataforma import pontuacao
from plataforma.estado import Analise, Reclamacao, Sinal


def reclamacao(id_, status="Não respondida"):
    return Reclamacao(
        id=id_, data="2026-01-01", empresa="Empresa", titulo="Título",
        texto="Texto qualquer.", cidade_estado="SP", status=status,
    )


def sinal(codigo, citacao="citação qualquer com cinco palavras", valida=True):
    return Sinal(codigo=codigo, citacao=citacao, valida=valida)


def analise(id_, sinais):
    return Analise(id=id_, sentimento="neutro", produto=None, sinais=sinais,
                    prazo_prometido_dias=None, data_evento=None)


def estado(reclamacoes, analises):
    return {"reclamacoes": reclamacoes, "analises": analises, "falhas": []}


def test_dinheiro_retido_valido_entra_na_fila_com_tres_pontos():
    est = estado(
        [reclamacao("R1")],
        [analise("R1", [sinal("dinheiro_retido")])],
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == 3
    assert resultado["na_fila"] is True
    assert resultado["motivos"] == [
        {"origem": "sinal", "citacao": "citação qualquer com cinco palavras",
         "rotulo": "dinheiro_retido"},
    ]


def test_dinheiro_retido_com_status_respondida_fica_fora_da_fila():
    # AC4: o caso que dá precisão de 100% à regra medida.
    est = estado(
        [reclamacao("R1", status="Respondida")],
        [analise("R1", [sinal("dinheiro_retido")])],
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == 2
    assert resultado["na_fila"] is False


def test_grupo_a_satura_em_tres_nao_seis():
    est = estado(
        [reclamacao("R1")],
        [analise("R1", [sinal("ameaca_explicita"), sinal("lei_citada")])],
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == 3, "AC3: grupo A deveria saturar em 3, não somar 6"
    assert len(resultado["motivos"]) == 2, "cada código do grupo ainda gera seu Motivo"


def test_grupo_a_com_um_so_codigo_presente_tambem_pontua():
    # O caminho de um código só do grupo A era exercitado só como subconjunto do teste
    # de dois códigos — achado de revisão, testado isolado agora.
    est = estado(
        [reclamacao("R1")],
        [analise("R1", [sinal("ameaca_explicita")])],
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == 3
    assert len(resultado["motivos"]) == 1


def test_duas_citacoes_do_mesmo_codigo_somam_peso_uma_vez():
    est = estado(
        [reclamacao("R1")],
        [analise("R1", [
            sinal("dinheiro_retido", citacao="primeira citação com cinco palavras"),
            sinal("dinheiro_retido", citacao="segunda citação também com cinco"),
        ])],
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == 3, "peso do código não deveria dobrar"
    assert len(resultado["motivos"]) == 2, "cada citação ainda deveria gerar um Motivo"


def test_sinal_invalido_nao_soma_pontos_mesmo_com_par_valido_do_mesmo_codigo():
    est = estado(
        [reclamacao("R1")],
        [analise("R1", [
            sinal("dano_continuado", valida=True),
            sinal("dano_continuado", valida=False),
        ])],
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    # AD-2 já garante, na prática (evidencia.verificar), que os dois sairiam com o
    # mesmo valida — mas pontuar() não deveria confiar nisso: só soma o que está
    # valida=True, código a código.
    assert resultado["pontos"] == 2, "só o Sinal válido deveria contar"


def test_modificador_status_respondida_sempre_produz_motivo_atributo():
    est = estado(
        [reclamacao("R1", status="Respondida")],
        [analise("R1", [])],  # sem nenhum sinal — só o modificador
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == -1
    assert resultado["motivos"] == [
        {"origem": "atributo", "citacao": None, "rotulo": "Status: Respondida (-1)"},
    ]


def test_registro_contraditorio_mais_prazo_estourado_soma_tres_entra_na_fila():
    # Linha da tabela de conferência de risk-signals.md.
    est = estado(
        [reclamacao("R1")],
        [analise("R1", [sinal("registro_contraditorio"), sinal("prazo_estourado")])],
    )
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == 3
    assert resultado["na_fila"] is True


def test_parcelas_nao_exercidas_pela_base_pontuam_sem_rede():
    # AC9/Q-4: ameaca_explicita, dano_continuado e registro_contraditorio, cada uma
    # isolada, precisam produzir pontuação — a base real não exercita nenhuma delas.
    for codigo, peso_esperado in [
        ("ameaca_explicita", 3), ("dano_continuado", 2), ("registro_contraditorio", 2),
    ]:
        est = estado([reclamacao("R1")], [analise("R1", [sinal(codigo)])])
        resultado = pontuacao.pontuar(est)["pontuacoes"][0]
        assert resultado["pontos"] == peso_esperado, f"{codigo} deveria valer {peso_esperado}"


def test_sem_sinais_e_status_nao_respondida_pontua_zero_fora_da_fila():
    est = estado([reclamacao("R1")], [analise("R1", [])])
    resultado = pontuacao.pontuar(est)["pontuacoes"][0]
    assert resultado["pontos"] == 0
    assert resultado["na_fila"] is False
    assert resultado["motivos"] == []


def test_status_diferente_de_respondida_nao_aplica_modificador():
    # Só "Respondida" aciona o modificador — os outros quatro valores do Literal não.
    for status in ("Não respondida", "Resolvido", "Não resolvido", "Em réplica"):
        est = estado([reclamacao("R1", status=status)],
                      [analise("R1", [sinal("prazo_estourado")])])
        resultado = pontuacao.pontuar(est)["pontuacoes"][0]
        assert resultado["pontos"] == 1, f"status {status!r} não deveria acionar o modificador"
        assert not any(m["origem"] == "atributo" for m in resultado["motivos"])


def test_pontuar_preserva_a_ordem_das_analises():
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [analise("R2", []), analise("R1", [])],
    )
    ids = [p["id"] for p in pontuacao.pontuar(est)["pontuacoes"]]
    assert ids == ["R2", "R1"]


def test_import_pontuacao_sem_credencial(monkeypatch):
    import importlib
    import sys

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "plataforma.pontuacao", raising=False)
    modulo = importlib.import_module("plataforma.pontuacao")
    assert modulo.__name__ == "plataforma.pontuacao"
