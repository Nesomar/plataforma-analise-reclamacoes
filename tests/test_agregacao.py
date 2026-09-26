"""Cobre `agregar`: contagens diretas, ranking, degradação e ordem da fila.

Tudo fabricado à mão — `agregar` não toca rede nem SDK (AD-12).
"""

import re

from plataforma import agregacao
from plataforma.estado import Analise, Falha, Pontuacao, Reclamacao, Sinal


def reclamacao(id_, data="2026-01-01", status="Não respondida"):
    return Reclamacao(
        id=id_, data=data, empresa="Empresa", titulo="Título",
        texto="Texto qualquer.", cidade_estado="SP", status=status,
    )


def analise(id_, produto=None, sentimento="neutro", sinais=None):
    return Analise(id=id_, sentimento=sentimento, produto=produto,
                    sinais=sinais or [], prazo_prometido_dias=None, data_evento=None)


def sinal(codigo, valida=True, citacao="citação qualquer com cinco palavras"):
    return Sinal(codigo=codigo, citacao=citacao, valida=valida)


def falha(ids, causa="x", no="analisar_lote"):
    return Falha(ids=ids, causa=causa, no=no)


def pontuacao(id_, pontos=0, na_fila=False):
    return Pontuacao(id=id_, pontos=pontos, na_fila=na_fila, motivos=[])


def estado(reclamacoes, analises, falhas=None, pontuacoes=None):
    return {
        "reclamacoes": reclamacoes, "analises": analises,
        "falhas": falhas or [], "pontuacoes": pontuacoes or [],
    }


def test_contagens_diretas_batem_com_a_fixture():
    est = estado(
        [reclamacao("R1"), reclamacao("R2"), reclamacao("R3")],
        [analise("R1"), analise("R2")],
        falhas=[falha(["R3"])],
    )
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["lidas"] == 3
    assert resultado["analisadas"] == 2
    assert resultado["nao_analisadas"] == 1
    assert resultado["eventos_falha"] == 1


def test_codigos_propostos_e_derrubados_nao_deduplicam_entre_reclamacoes():
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [
            analise("R1", sinais=[sinal("dinheiro_retido", valida=False)]),
            analise("R2", sinais=[sinal("dinheiro_retido", valida=False)]),
        ],
    )
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["codigos_propostos"] == 2, "dois códigos propostos, um por reclamação"
    assert resultado["codigos_derrubados"] == 2, "AC: mesmo código derrubado 2x conta 2, não 1"


def test_produto_none_vira_nao_identificado_com_total():
    est = estado([reclamacao("R1")], [analise("R1", produto=None)])
    ranking = agregacao.agregar(est)["agregados"]["ranking_produtos"]
    assert ranking == [{"rotulo": "não identificado", "total": 1, "generico": False}]


def test_produto_vazio_ou_so_espacos_tambem_vira_nao_identificado():
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [analise("R1", produto=""), analise("R2", produto="   ")],
    )
    ranking = agregacao.agregar(est)["agregados"]["ranking_produtos"]
    assert ranking == [{"rotulo": "não identificado", "total": 2, "generico": False}]


def test_produto_literal_nao_identificado_nao_se_funde_com_o_balde_de_nulo():
    # Achado de revisão: produto=None e produto="não identificado" são populações
    # diferentes — a segunda é o que o modelo leu, a primeira é ausência de leitura.
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [analise("R1", produto=None), analise("R2", produto="não identificado")],
    )
    ranking = agregacao.agregar(est)["agregados"]["ranking_produtos"]
    assert sum(item["total"] for item in ranking) == 2, \
        "as duas populações não podem se fundir num único total"


def test_produto_com_espaco_externo_agrupa_com_a_forma_sem_espaco():
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [analise("R1", produto="Celular"), analise("R2", produto=" Celular ")],
    )
    ranking = agregacao.agregar(est)["agregados"]["ranking_produtos"]
    assert ranking == [{"rotulo": "Celular", "total": 2, "generico": False}]


def test_produto_generico_marcado_por_agregar():
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [analise("R1", produto="produto"), analise("R2", produto="Celular")],
    )
    ranking = agregacao.agregar(est)["agregados"]["ranking_produtos"]
    por_rotulo = {item["rotulo"]: item for item in ranking}
    assert por_rotulo["produto"]["generico"] is True, "AC3: termo da lista canônica"
    assert por_rotulo["Celular"]["generico"] is False


def test_taxa_produto_nao_nomeado_soma_nulo_e_generico():
    est = estado(
        [reclamacao("R1"), reclamacao("R2"), reclamacao("R3")],
        [
            analise("R1", produto=None),
            analise("R2", produto="produto"),
            analise("R3", produto="Celular"),
        ],
    )
    taxa = agregacao.agregar(est)["agregados"]["taxa_produto_nao_nomeado"]
    assert taxa == 2 / 3, "CM-3: nulo + genérico, não só o nulo"


def test_ranking_ordenado_por_total_decrescente_desempate_alfabetico():
    est = estado(
        [reclamacao(f"R{i}") for i in range(4)],
        [
            analise("R0", produto="Zebra"),
            analise("R1", produto="Abelha"),
            analise("R2", produto="Abelha"),
            analise("R3", produto="Zebra"),
        ],
    )
    ranking = agregacao.agregar(est)["agregados"]["ranking_produtos"]
    assert [item["rotulo"] for item in ranking] == ["Abelha", "Zebra"], \
        "ambos com total 2 — desempate alfabético"


def test_distribuicao_sentimento_conta_as_tres_categorias():
    est = estado(
        [reclamacao("R1"), reclamacao("R2"), reclamacao("R3")],
        [
            analise("R1", sentimento="positivo"),
            analise("R2", sentimento="negativo"),
            analise("R3", sentimento="negativo"),
        ],
    )
    dist = agregacao.agregar(est)["agregados"]["distribuicao_sentimento"]
    assert dist == {"positivo": 1, "neutro": 0, "negativo": 2}


def test_degradado_por_mais_de_dez_por_cento_nao_analisadas():
    # Um único evento de Falha cobrindo 2 de 10 reclamações (20%) — prova que o número
    # usado é reclamações afetadas, não eventos (AD-5): eventos_falha=1, mas degrada.
    est = estado(
        [reclamacao(f"R{i}") for i in range(10)],
        [analise(f"R{i}") for i in range(8)],
        falhas=[falha(["R8", "R9"])],
    )
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["eventos_falha"] == 1
    assert resultado["nao_analisadas"] == 2
    assert resultado["degradado"] is True
    assert "20" not in resultado["motivo_degradacao"]  # não trava em formatação, só no conteúdo
    assert "2/10" in resultado["motivo_degradacao"]


def test_nao_degrada_com_dez_por_cento_ou_menos_nao_analisadas():
    est = estado(
        [reclamacao(f"R{i}") for i in range(10)],
        [analise(f"R{i}") for i in range(9)],
        falhas=[falha(["R9"])],
    )
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["degradado"] is False
    assert resultado["motivo_degradacao"] is None


def test_degradado_quando_todos_os_codigos_propostos_sao_derrubados():
    # AC6: zero não analisadas, mas o único código proposto foi derrubado.
    est = estado(
        [reclamacao("R1")],
        [analise("R1", sinais=[sinal("dinheiro_retido", valida=False)])],
    )
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["nao_analisadas"] == 0
    assert resultado["degradado"] is True
    assert "1 código " in resultado["motivo_degradacao"]


def test_nao_degrada_quando_nenhum_codigo_foi_proposto():
    est = estado([reclamacao("R1")], [analise("R1", sinais=[])])
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["degradado"] is False


def test_fila_ordenada_por_pontos_desc_depois_data_depois_id():
    reclamacoes = [
        reclamacao("RA", data="2026-01-05"),
        reclamacao("RB", data="2026-01-10"),
        reclamacao("RC", data="2026-01-01"),
        reclamacao("RD", data="2026-01-01"),
    ]
    pontuacoes = [
        pontuacao("RA", pontos=3, na_fila=True),
        pontuacao("RB", pontos=5, na_fila=True),  # pontos mais alto vence apesar da data
        pontuacao("RC", pontos=3, na_fila=True),  # mesmo pontos de RA/RD, data mais antiga
        pontuacao("RD", pontos=3, na_fila=True),  # mesmo pontos e data de RC, desempate por id
    ]
    est = estado(reclamacoes, [analise(r["id"]) for r in reclamacoes], pontuacoes=pontuacoes)
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["fila"] == ["RB", "RC", "RD", "RA"]
    assert resultado["total_na_fila"] == 4


def test_ocupacao_fila_bate_com_total_na_fila_sobre_analisadas():
    reclamacoes = [reclamacao(f"R{i}") for i in range(4)]
    pontuacoes = [
        pontuacao("R0", pontos=5, na_fila=True),
        pontuacao("R1", pontos=5, na_fila=True),
        pontuacao("R2", pontos=0, na_fila=False),
        pontuacao("R3", pontos=0, na_fila=False),
    ]
    est = estado(reclamacoes, [analise(r["id"]) for r in reclamacoes], pontuacoes=pontuacoes)
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["ocupacao_fila"] == 0.5


def test_agregar_respeita_na_fila_ja_decidido_sem_recalcular():
    # AD-19/AC8: agregar nunca decide na_fila a partir de pontos — só filtra o que já
    # veio marcado, mesmo que o valor pareça inconsistente com o corte de pontuacao.py.
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [analise("R1"), analise("R2")],
        pontuacoes=[
            pontuacao("R1", pontos=0, na_fila=True),
            pontuacao("R2", pontos=99, na_fila=False),
        ],
    )
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["fila"] == ["R1"]


def test_data_execucao_e_iso_8601():
    est = estado([reclamacao("R1")], [analise("R1")])
    data_execucao = agregacao.agregar(est)["agregados"]["data_execucao"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", data_execucao), \
        f"data_execucao {data_execucao!r} não é ISO-8601 (AAAA-MM-DD)"


def test_analises_vazias_nao_gera_divisao_por_zero():
    # Blind Hunter: os guardas `if analisadas else 0.0` existiam por inspeção, sem
    # nenhum teste exercitando o caminho de zero reclamações analisadas.
    est = estado(
        [reclamacao("R1"), reclamacao("R2")],
        [],
        falhas=[falha(["R1", "R2"])],
    )
    resultado = agregacao.agregar(est)["agregados"]
    assert resultado["analisadas"] == 0
    assert resultado["ocupacao_fila"] == 0.0
    assert resultado["taxa_produto_nao_nomeado"] == 0.0
    assert resultado["ranking_produtos"] == []
    assert resultado["fila"] == []
    assert resultado["degradado"] is True  # 100% não analisadas


def test_import_agregacao_sem_credencial(monkeypatch):
    import importlib
    import sys

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "plataforma.agregacao", raising=False)
    modulo = importlib.import_module("plataforma.agregacao")
    assert modulo.__name__ == "plataforma.agregacao"
