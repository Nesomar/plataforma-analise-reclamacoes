"""Cobre `_contar_codigos_derrubados` e `_ler_argumento` — as únicas partes de `main.py`
testáveis sem invocar o grafo de verdade (isso chamaria `analisar_lote`, rede).
"""

import pytest

import main
from plataforma.estado import Analise, Sinal


def analise(sinais):
    return Analise(id="R1", sentimento="neutro", produto=None, sinais=sinais,
                    prazo_prometido_dias=None, data_evento=None)


def sinal(codigo, valida):
    return Sinal(codigo=codigo, citacao="citação qualquer com cinco palavras", valida=valida)


def test_contar_codigos_derrubados_sem_nenhum_invalido():
    analises = [analise([sinal("dinheiro_retido", True)])]
    assert main._contar_codigos_derrubados(analises) == 0


def test_contar_codigos_derrubados_conta_por_codigo_nao_por_par():
    # Dois Sinal do mesmo código, ambos valida=False (AD-2 já garante que chegam assim
    # agrupados) — deveria contar 1 código, não 2 pares.
    analises = [analise([
        sinal("dinheiro_retido", False),
        sinal("dinheiro_retido", False),
    ])]
    assert main._contar_codigos_derrubados(analises) == 1


def test_contar_codigos_derrubados_conta_codigos_diferentes_na_mesma_reclamacao():
    analises = [analise([sinal("dinheiro_retido", False), sinal("prazo_estourado", False)])]
    assert main._contar_codigos_derrubados(analises) == 2


def test_contar_codigos_derrubados_nao_deduplica_entre_reclamacoes():
    # AC4: soma por reclamação. O mesmo código derrubado em duas reclamações conta 2.
    analises = [
        analise([sinal("dinheiro_retido", False)]),
        analise([sinal("dinheiro_retido", False)]),
    ]
    assert main._contar_codigos_derrubados(analises) == 2


def test_mensagem_zero_analises_nomeia_eventos_e_causas_unicas():
    falhas = [
        {"ids": ["R1"], "causa": "erro de rede", "no": "analisar_lote"},
        {"ids": ["R2"], "causa": "erro de rede", "no": "analisar_lote"},
    ]
    mensagem = main._mensagem_zero_analises(falhas)
    assert "2 evento(s) de falha" in mensagem
    assert "erro de rede" in mensagem
    assert mensagem.count("erro de rede") == 1, "causa repetida não deveria duplicar na mensagem"


def test_ler_argumento_com_lista_vazia_nao_quebra_com_indexerror():
    # argv nunca deveria vir vazio na prática (sys.argv sempre tem ao menos o nome do
    # script), mas a função não deveria confiar nisso — achado de revisão.
    with pytest.raises(SystemExit, match="uso:"):
        main._ler_argumento([])


def test_ler_argumento_sem_csv_levanta_com_mensagem_de_uso():
    with pytest.raises(SystemExit, match="uso:"):
        main._ler_argumento(["main.py"])


def test_ler_argumento_com_argumento_extra_levanta():
    with pytest.raises(SystemExit, match="uso:"):
        main._ler_argumento(["main.py", "a.csv", "b.csv"])


def test_ler_argumento_devolve_o_caminho():
    assert main._ler_argumento(["main.py", "docs/reclamacoes_reclameaqui.csv"]) == \
        "docs/reclamacoes_reclameaqui.csv"
