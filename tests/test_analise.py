"""Cobre `_montar_payload`, `_montar_delta`, `_deve_repetir` e `_chamar_com_retry`:
toda a I/O Matrix é exercitada sem tocar o SDK — nenhum teste chama `generate_content`
nem constrói `genai.Client()`.

O repositório proíbe mock do `google.genai` (project-context.md), então a única forma
de testar resposta incompleta, id repetido/inventado, ou schema fora do padrão é
alimentar `_montar_delta` diretamente com `list[_AnaliseResposta] | None` fabricado à
mão, nunca uma resposta HTTP de verdade. O mesmo vale para o retry: `_chamar_com_retry`
recebe uma função fabricada como `chamar`, nunca uma chamada de rede real — é assim que
o mecanismo de absorção de falha de transporte (Story 1.6, revisão de 2026-08-08) é
testado sem precisar simular o SDK.
"""

from pathlib import Path

import pytest
from google.genai import errors as genai_errors

from plataforma import analise, catalogo
from plataforma.estado import Reclamacao

RECLAMACAO_1 = Reclamacao(
    id="R1", data="2026-01-01", empresa="Empresa A", titulo="Título A",
    texto="Cancelei a compra há 40 dias e até hoje não recebi o estorno.",
    cidade_estado="SP", status="Não respondida",
)
RECLAMACAO_2 = Reclamacao(
    id="R2", data="2026-01-02", empresa="Empresa B", titulo="Título B",
    texto="Prometeram entrega em 5 dias úteis e já se passaram 20 dias sem nada.",
    cidade_estado="RJ", status="Respondida",
)


def resposta(id_, sentimento="neutro", produto=None, sinais=None):
    return analise._AnaliseResposta(
        id=id_, sentimento=sentimento, produto=produto,
        sinais=[analise._SinalResposta(**s) for s in (sinais or [])],
    )


def test_montar_payload_so_leva_id_e_texto():
    payload = analise._montar_payload([RECLAMACAO_1, RECLAMACAO_2])
    assert payload == [
        {"id": "R1", "texto": RECLAMACAO_1["texto"]},
        {"id": "R2", "texto": RECLAMACAO_2["texto"]},
    ], "AC1: payload deveria conter só id e texto"
    for item in payload:
        assert "empresa" not in item and "titulo" not in item, \
            f"AD-16: payload {item} vazou empresa/titulo"


def test_montar_delta_caso_feliz_roda_evidencia_verificar():
    # A citação de R1 é real (substring do texto); a de R2 é fabricada. Se
    # _montar_delta só copiasse os sinais sem chamar evidencia.verificar, as duas
    # sairiam com valida=False (default do Sinal bruto) e este teste não provaria
    # que a verificação de fato rodou (AC6).
    respostas = [
        resposta("R1", sinais=[{"codigo": "dinheiro_retido",
                                 "citacao": "até hoje não recebi o estorno"}]),
        resposta("R2", sinais=[{"codigo": "prazo_estourado",
                                 "citacao": "a empresa confessou o atraso por escrito"}]),
    ]
    delta = analise._montar_delta([RECLAMACAO_1, RECLAMACAO_2], respostas)

    assert delta["falhas"] == []
    por_id = {a["id"]: a for a in delta["analises"]}
    assert por_id["R1"]["sinais"][0]["valida"] is True, \
        "AC6: citação real deveria passar na verificação de evidência"
    assert por_id["R2"]["sinais"][0]["valida"] is False, \
        "AC6: citação fabricada deveria ser derrubada pela verificação de evidência"


def test_montar_delta_id_faltante_vira_falha():
    respostas = [resposta("R1")]
    delta = analise._montar_delta([RECLAMACAO_1, RECLAMACAO_2], respostas)
    assert len(delta["analises"]) == 1 and delta["analises"][0]["id"] == "R1"
    assert len(delta["falhas"]) == 1
    assert delta["falhas"][0]["ids"] == ["R2"], "AC3: falha deveria nomear o id faltante"


def test_montar_delta_id_repetido_mantem_so_a_primeira_ocorrencia():
    respostas = [resposta("R1", sentimento="positivo"), resposta("R1", sentimento="negativo")]
    delta = analise._montar_delta([RECLAMACAO_1], respostas)
    assert len(delta["analises"]) == 1, "AC4: id repetido não deveria duplicar a análise"
    assert delta["analises"][0]["sentimento"] == "positivo", \
        "AC4: deveria manter a primeira ocorrência do id repetido"
    assert delta["falhas"] == [], "AC4: id repetido não deveria gerar Falha"


def test_montar_delta_id_inventado_e_descartado_sem_falha():
    respostas = [resposta("R1"), resposta("ID-QUE-NAO-EXISTE")]
    delta = analise._montar_delta([RECLAMACAO_1], respostas)
    assert [a["id"] for a in delta["analises"]] == ["R1"], \
        "AC4: id inventado não deveria virar Analise"
    assert delta["falhas"] == [], "AC4: id inventado não deveria gerar Falha"


def test_montar_delta_com_none_vira_uma_falha_cobrindo_o_lote_inteiro():
    delta = analise._montar_delta([RECLAMACAO_1, RECLAMACAO_2], None)
    assert delta["analises"] == [], "AC5: schema fora do padrão não deveria produzir análise"
    assert len(delta["falhas"]) == 1, "AC5: deveria haver exatamente uma Falha para o lote"
    assert delta["falhas"][0]["ids"] == ["R1", "R2"], \
        "AC5: a Falha deveria cobrir todos os ids do lote"


def test_montar_delta_produto_none_atravessa_sem_alteracao():
    respostas = [resposta("R1", produto=None)]
    delta = analise._montar_delta([RECLAMACAO_1], respostas)
    assert delta["analises"][0]["produto"] is None, \
        "AC7: produto=None do modelo deveria atravessar sem julgamento"


def test_montar_instrucao_lista_todos_os_codigos_do_catalogo():
    instrucao = analise._montar_instrucao()
    for codigo in catalogo.CATALOGO:
        assert codigo in instrucao, f"prompt deveria citar o código {codigo!r}"


def test_analisar_lote_com_lote_vazio_nao_chama_o_modelo():
    # O guard de lote vazio devolve ANTES de genai.Client() ser construído — por isso
    # dá para chamar analisar_lote([]) direto no teste sem violar a proibição de
    # mock do SDK: nenhuma linha que toca a rede chega a executar.
    assert analise.analisar_lote([]) == {"analises": [], "falhas": []}


@pytest.mark.parametrize("erro, esperado", [
    (genai_errors.ServerError(500, {}, None), True),
    (genai_errors.ClientError(429, {}, None), True),
    (genai_errors.ClientError(401, {}, None), False),
    (genai_errors.ClientError(400, {}, None), False),
    (ConnectionError("conexão recusada"), True),
    (TimeoutError("tempo esgotado"), True),
    (ValueError("erro de programação, não de transporte"), False),
])
def test_deve_repetir_classifica_transitorio_versus_permanente(erro, esperado):
    assert analise._deve_repetir(erro) is esperado, \
        f"AD-9/AC4: {type(erro).__name__}({getattr(erro, 'code', '')}) deveria repetir={esperado}"


def test_chamar_com_retry_repete_ate_ter_sucesso(monkeypatch):
    monkeypatch.setattr(analise.time, "sleep", lambda _: None)  # backoff real deixaria o teste lento
    tentativas = {"n": 0}

    def chamar():
        tentativas["n"] += 1
        if tentativas["n"] < 3:
            raise genai_errors.ServerError(503, {}, None)
        return "ok"

    resultado = analise._chamar_com_retry(chamar)
    assert resultado == "ok"
    assert tentativas["n"] == 3, "deveria ter tentado 3 vezes até o sucesso"


def test_chamar_com_retry_nao_repete_erro_permanente():
    tentativas = {"n": 0}

    def chamar():
        tentativas["n"] += 1
        raise genai_errors.ClientError(401, {}, None)

    with pytest.raises(genai_errors.ClientError):
        analise._chamar_com_retry(chamar)
    assert tentativas["n"] == 1, "erro permanente não deveria repetir nenhuma vez"


def test_chamar_com_retry_esgota_tentativas_e_levanta_a_ultima_excecao(monkeypatch):
    monkeypatch.setattr(analise.time, "sleep", lambda _: None)
    tentativas = {"n": 0}

    def chamar():
        tentativas["n"] += 1
        raise genai_errors.ServerError(503, {}, None)

    with pytest.raises(genai_errors.ServerError):
        analise._chamar_com_retry(chamar)
    assert tentativas["n"] == analise._TENTATIVAS


def test_somente_analise_importa_o_sdk_do_modelo():
    """AD-7, em todo o pacote: analise.py é o único módulo que pode importar google.genai."""
    pacote = Path(analise.__file__).parent
    for arquivo in pacote.glob("*.py"):
        if arquivo.name in {"analise.py", "__init__.py"}:
            continue
        fonte = arquivo.read_text(encoding="utf-8")
        assert "google" not in fonte, \
            f"AD-7: {arquivo.name} referencia 'google' — só analise.py pode importar o SDK"


def test_import_analise_sem_credencial(monkeypatch):
    import importlib
    import sys

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "plataforma.analise", raising=False)
    modulo = importlib.import_module("plataforma.analise")
    assert modulo.__name__ == "plataforma.analise", \
        "AC8: import de plataforma.analise não deveria exigir credencial"
