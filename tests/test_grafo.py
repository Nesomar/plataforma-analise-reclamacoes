"""Cobre `_fatiar`, `_despachar`, `_verificar_conservacao` — todas puras — e
`construir_grafo` só por introspecção estrutural, nunca por `.invoke()`.

`.invoke()` chamaria `analisar_lote` de verdade (Story 1.5), que chamaria
`genai.Client()` — rede e credencial. Nenhum teste aqui faz isso.

Sem `retry_policy`/`error_handler` no nó `analisar_lote` — decisão revisada em
2026-08-08, ver `plataforma/analise.py` para o registro completo da investigação que
motivou a mudança (o mecanismo do LangGraph não absorve falha sob concorrência nesta
versão). O retry e a absorção de falha de transporte agora vivem dentro de
`analise.analisar_lote`, testados em `tests/test_analise.py`.
"""

import pytest

from plataforma import grafo
from plataforma.estado import Analise, Falha, Reclamacao


def reclamacao(id_):
    return Reclamacao(
        id=id_, data="2026-01-01", empresa="Empresa", titulo="Título",
        texto=f"Texto da reclamação {id_}.", cidade_estado="SP", status="Respondida",
    )


RECLAMACOES_50 = [reclamacao(f"R{i}") for i in range(50)]


def test_fatiar_exato_produz_lotes_do_tamanho_pedido():
    lotes = grafo._fatiar(RECLAMACOES_50, 10)
    assert len(lotes) == 5, "AC1: 50/10 deveria produzir 5 lotes"
    assert all(len(lote) == 10 for lote in lotes)


def test_fatiar_com_residuo_de_um_funde_ao_lote_anterior():
    lotes = grafo._fatiar(RECLAMACOES_50, 7)
    assert all(len(lote) != 1 for lote in lotes), \
        "AD-17: nenhum lote deveria ter tamanho 1"
    assert len(lotes) == 7, "6 lotes de 7 + o resto fundido no 7º = 7 lotes, não 8"
    assert len(lotes[-1]) == 8, "o último lote deveria carregar o resíduo fundido"
    assert sum(len(lote) for lote in lotes) == 50, "nenhuma reclamação pode sumir"


def test_fatiar_lote_unico_nao_tenta_fundir_consigo_mesmo():
    lotes = grafo._fatiar([reclamacao("R1")], 10)
    assert lotes == [[reclamacao("R1")]]


def test_fatiar_com_residuo_no_teto_rebalanceia_em_vez_de_estourar():
    # 51 itens, tamanho_lote=25 (o teto): fundir sem checar produziria um lote de 26,
    # estourando o teto que AD-17 existe para proteger. Achado de revisão adversarial,
    # reproduzido antes do fix: grafo._fatiar([...51 itens...], 25) devolvia [25, 26].
    reclamacoes_51 = [reclamacao(f"R{i}") for i in range(51)]
    lotes = grafo._fatiar(reclamacoes_51, 25)
    assert all(len(lote) <= 25 for lote in lotes), \
        "AD-17: nenhum lote emitido pode exceder o teto de 25"
    assert all(len(lote) != 1 for lote in lotes), "AD-17: nenhum lote de tamanho 1"
    assert sum(len(lote) for lote in lotes) == 51, "nenhuma reclamação pode sumir"


def test_despachar_emite_um_send_por_lote_com_a_lista_crua():
    sends = grafo._despachar(RECLAMACOES_50, 10)
    assert len(sends) == 5, "AC1: deveria emitir 5 Send"
    for s in sends:
        assert s.node == "analisar_lote"
        assert isinstance(s.arg, list) and isinstance(s.arg[0], dict), \
            "Send.arg deveria ser a lista de Reclamacao crua, não um dict envolvendo ela"


def test_verificar_conservacao_passa_quando_soma_bate():
    estado = {
        "reclamacoes": [reclamacao("R1"), reclamacao("R2")],
        "analises": [Analise(id="R1", sentimento="neutro", produto=None, sinais=[],
                              prazo_prometido_dias=None, data_evento=None)],
        "falhas": [Falha(ids=["R2"], causa="x", no="analisar_lote")],
    }
    grafo._verificar_conservacao(estado)  # não deveria levantar


def test_verificar_conservacao_levanta_quando_soma_nao_bate():
    estado = {
        "reclamacoes": [reclamacao("R1"), reclamacao("R2")],
        "analises": [],
        "falhas": [],
    }
    with pytest.raises(AssertionError, match="AD-6"):
        grafo._verificar_conservacao(estado)


def test_construir_grafo_tem_os_nos_esperados_sem_invocar():
    # Caminho fictício de propósito: construir_grafo() não abre o arquivo enquanto não
    # for invocado, o caminho só vira closure do nó "carregar".
    compilado = grafo.construir_grafo("caminho-nao-usado-neste-teste.csv")
    nos = compilado.builder.nodes
    for esperado in ("carregar", "analisar_lote", "_verificar_conservacao", "pontuar", "agregar"):
        assert esperado in nos, f"nó {esperado!r} deveria existir no grafo compilado"


def test_construir_grafo_analisar_lote_sem_retry_policy_nem_error_handler():
    # Trava a decisão revisada: o LangGraph não absorve falha sob concorrência nesta
    # versão, então analisar_lote se auto-protege e o nó não declara retry_policy nem
    # error_handler. Se isto voltar a aparecer aqui, é sinal de regressão ao desenho
    # antigo (quebrado) — não um "reforço" acidental.
    compilado = grafo.construir_grafo("caminho-nao-usado-neste-teste.csv")
    spec = compilado.builder.nodes["analisar_lote"]
    assert spec.retry_policy is None
    assert spec.error_handler_node is None


def test_construir_grafo_agregar_sem_retry_policy_nem_error_handler():
    # agregar (Story 2.2), como pontuar, é síncrono e determinístico — nada de
    # transporte para absorver.
    compilado = grafo.construir_grafo("caminho-nao-usado-neste-teste.csv")
    spec = compilado.builder.nodes["agregar"]
    assert spec.retry_policy is None
    assert spec.error_handler_node is None


def test_import_grafo_sem_credencial(monkeypatch):
    import importlib
    import sys

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "plataforma.grafo", raising=False)
    modulo = importlib.import_module("plataforma.grafo")
    assert modulo.__name__ == "plataforma.grafo", \
        "import de plataforma.grafo não deveria exigir credencial"
