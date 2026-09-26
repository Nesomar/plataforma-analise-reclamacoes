"""Cobre `_contar_codigos_derrubados`, `_ler_argumento` e `_nome_saida` — as únicas
partes de `main.py` testáveis sem invocar o grafo de verdade (isso chamaria
`analisar_lote`, rede).
"""

import datetime
from pathlib import Path

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


def test_ler_argumento_com_argumento_extra_que_nao_e_a_flag_levanta():
    with pytest.raises(SystemExit, match="uso:"):
        main._ler_argumento(["main.py", "a.csv", "b.csv"])


def test_ler_argumento_com_flag_errada_levanta():
    with pytest.raises(SystemExit, match="uso:"):
        main._ler_argumento(["main.py", "a.csv", "--flag-errada"])


def test_ler_argumento_devolve_o_caminho_e_sobrescrever_falso():
    assert main._ler_argumento(["main.py", "docs/reclamacoes_reclameaqui.csv"]) == \
        ("docs/reclamacoes_reclameaqui.csv", False)


def test_ler_argumento_com_flag_sobrescrever_devolve_true():
    assert main._ler_argumento(["main.py", "a.csv", "--sobrescrever"]) == ("a.csv", True)


def test_ler_argumento_com_apenas_a_flag_levanta():
    # Achado de revisão: sem isto, ["main.py", "--sobrescrever"] era lido como
    # caminho_csv="--sobrescrever" com sobrescrever=False, em vez de erro de uso.
    with pytest.raises(SystemExit, match="uso:"):
        main._ler_argumento(["main.py", "--sobrescrever"])


def test_nome_saida_comeca_com_relatorio_e_fica_ao_lado_do_csv():
    caminho = main._nome_saida("docs/reclamacoes_reclameaqui.csv")
    data_hoje = datetime.date.today().isoformat()
    assert caminho == Path(f"docs/relatorio-reclamacoes_reclameaqui-{data_hoje}.html")
    assert caminho.parent == Path("docs")
    assert caminho.name.startswith("relatorio-")


def test_main_com_arquivo_de_saida_existente_encerra_sem_invocar_o_grafo(tmp_path, monkeypatch):
    # AC3: o desvio de custo precisa acontecer antes de .invoke() — este teste falharia
    # se uma regressão movesse o cheque para depois, porque construir_grafo levantaria.
    csv = tmp_path / "reclamacoes.csv"
    csv.write_text("id\n", encoding="utf-8")
    saida = main._nome_saida(str(csv))
    saida.write_text("relatório antigo", encoding="utf-8")

    def _construir_grafo_nao_deveria_ser_chamado(*args, **kwargs):
        raise AssertionError("grafo.construir_grafo não deveria ser chamado quando o arquivo já existe")

    monkeypatch.setattr(main.grafo, "construir_grafo", _construir_grafo_nao_deveria_ser_chamado)
    monkeypatch.setattr("sys.argv", ["main.py", str(csv)])
    with pytest.raises(SystemExit, match="arquivo de saída já existe"):
        main.main()
    assert saida.read_text(encoding="utf-8") == "relatório antigo", "não deveria sobrescrever sem a flag"


def test_main_com_sobrescrever_ignora_arquivo_existente_e_invoca_o_grafo(tmp_path, monkeypatch):
    csv = tmp_path / "reclamacoes.csv"
    csv.write_text("id\n", encoding="utf-8")
    saida = main._nome_saida(str(csv))
    saida.write_text("relatório antigo", encoding="utf-8")

    class _GrafoFalso:
        def invoke(self, _):
            return {
                "reclamacoes": [], "analises": [], "falhas": [],
                "caminho_html": str(saida),
            }

    chamadas = []

    def _construir_grafo_falso(caminho, caminho_saida):
        chamadas.append((caminho, caminho_saida))
        return _GrafoFalso()

    monkeypatch.setattr(main.grafo, "construir_grafo", _construir_grafo_falso)
    monkeypatch.setattr("sys.argv", ["main.py", str(csv), "--sobrescrever"])
    with pytest.raises(SystemExit) as excinfo:
        main.main()
    # analisadas == 0 encerra com _mensagem_zero_analises — não é o que este teste prova;
    # o que importa é que construir_grafo FOI chamado, provando que a flag liberou o fluxo.
    assert len(chamadas) == 1
    assert "nenhuma reclamação analisada" in str(excinfo.value)
