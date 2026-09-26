"""Cobre `relatorio.renderizar`: fila como primeiro conteúdo, ordem preservada, motivo
visível e escapado. Tudo fabricado à mão — sem rede, sem grafo, sem `.invoke()` (AD-12).

Não testa gravação em disco nem nome de arquivo — isso é FR-1b, Story 2.6. `renderizar`
devolve `str`; não há I/O aqui.
"""

import re

import jinja2

from plataforma import relatorio
from plataforma.estado import Agregados, DistribuicaoSentimento, ItemRanking, Motivo, Pontuacao, Reclamacao


def reclamacao(id_, empresa="Empresa", titulo="Título", data="2026-01-01", status="Não respondida"):
    return Reclamacao(
        id=id_, data=data, empresa=empresa, titulo=titulo,
        texto="Texto qualquer.", cidade_estado="SP", status=status,
    )


def motivo_sinal(rotulo="dinheiro_retido", citacao="citação literal com cinco palavras"):
    return Motivo(origem="sinal", citacao=citacao, rotulo=rotulo)


def motivo_atributo(rotulo="Status: Respondida (-1)"):
    return Motivo(origem="atributo", citacao=None, rotulo=rotulo)


def pontuacao(id_, pontos=3, motivos=None):
    return Pontuacao(id=id_, pontos=pontos, na_fila=True, motivos=motivos or [motivo_sinal()])


def item_ranking(rotulo, total, generico=False):
    return ItemRanking(rotulo=rotulo, total=total, generico=generico)


def agregados(fila, ranking_produtos=None, distribuicao_sentimento=None, analisadas=0,
              nao_analisadas=0, degradado=False, motivo_degradacao=None, data_execucao="2026-08-09"):
    return Agregados(
        data_execucao=data_execucao, lidas=0, analisadas=analisadas, nao_analisadas=nao_analisadas,
        eventos_falha=0, codigos_propostos=0, codigos_derrubados=0,
        fila=fila, total_na_fila=len(fila), ocupacao_fila=0.0,
        taxa_produto_nao_nomeado=0.0, ranking_produtos=ranking_produtos or [],
        distribuicao_sentimento=distribuicao_sentimento or DistribuicaoSentimento(positivo=0, neutro=0, negativo=0),
        degradado=degradado, motivo_degradacao=motivo_degradacao,
    )


def estado(reclamacoes, pontuacoes, fila, ranking_produtos=None, distribuicao_sentimento=None, analisadas=0,
           nao_analisadas=0, degradado=False, motivo_degradacao=None, data_execucao="2026-08-09"):
    return {
        "reclamacoes": reclamacoes,
        "pontuacoes": pontuacoes,
        "agregados": agregados(fila, ranking_produtos, distribuicao_sentimento, analisadas,
                                nao_analisadas, degradado, motivo_degradacao, data_execucao),
    }


def test_environment_unico_com_autoescape_literal():
    assert isinstance(relatorio._ENVIRONMENT, jinja2.Environment)
    assert relatorio._ENVIRONMENT.autoescape is True


def test_data_br_reordena_iso_para_convencao_local():
    assert relatorio._data_br("2026-01-05") == "05/01/2026"


def test_fila_renderizada_preserva_ordem_de_agregados_nao_reordena():
    est = estado(
        [reclamacao("R3", titulo="Título R3"), reclamacao("R1", titulo="Título R1"),
         reclamacao("R2", titulo="Título R2")],
        [pontuacao("R3"), pontuacao("R1"), pontuacao("R2")],
        fila=["R3", "R1", "R2"],
    )
    html = relatorio.renderizar(est)
    assert html.index("Título R3") < html.index("Título R1") < html.index("Título R2")


def test_secao_da_fila_e_o_primeiro_conteudo_do_body():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    corpo = html.split("<body>", 1)[1]
    assert corpo.strip().startswith('<section id="fila-prioridade">')


def test_motivo_de_origem_sinal_exibe_citacao_visivel():
    est = estado(
        [reclamacao("R1")],
        [pontuacao("R1", motivos=[motivo_sinal(rotulo="dinheiro_retido", citacao="cliente pagou e nunca recebeu o produto")])],
        fila=["R1"],
    )
    html = relatorio.renderizar(est)
    assert "cliente pagou e nunca recebeu o produto" in html
    assert "dinheiro_retido" in html


def test_motivo_de_origem_atributo_exibe_rotulo_sem_citacao():
    est = estado(
        [reclamacao("R1")],
        [pontuacao("R1", motivos=[motivo_atributo("Status: Respondida (-1)")])],
        fila=["R1"],
    )
    html = relatorio.renderizar(est)
    assert "Status: Respondida (-1)" in html


def test_motivo_nao_e_detalhe_expansivel_nem_tooltip():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    for marcador in ("<details", "<summary", "aria-expanded", 'title="'):
        assert marcador not in html


def test_template_nao_referencia_campos_de_reclamacao_fora_de_exibicao():
    texto = (relatorio._DIR_TEMPLATES / "relatorio.html.j2").read_text(encoding="utf-8")
    for proibido in ("reclamacao.status", "reclamacao.categoria", "item.status", "item.categoria"):
        assert proibido not in texto


def test_texto_com_marcacao_html_aparece_escapado():
    est = estado(
        [reclamacao("R1", titulo="<script>alert(1)</script>")],
        [pontuacao("R1")],
        fila=["R1"],
    )
    html = relatorio.renderizar(est)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_item_com_motivos_vazios_nao_quebra_renderizacao():
    est = estado([reclamacao("R1")], [pontuacao("R1", motivos=[])], fila=["R1"])
    html = relatorio.renderizar(est)
    assert '<ul class="motivos">' in html


def test_citacao_com_marcacao_html_aparece_escapada():
    est = estado(
        [reclamacao("R1")],
        [pontuacao("R1", motivos=[motivo_sinal(citacao="<b>cliente</b> exige solução em cinco dias")])],
        fila=["R1"],
    )
    html = relatorio.renderizar(est)
    assert "<b>cliente</b>" not in html
    assert "&lt;b&gt;cliente&lt;/b&gt;" in html


def test_item_com_motivos_de_origem_mista_exibe_os_dois():
    est = estado(
        [reclamacao("R1")],
        [pontuacao("R1", motivos=[
            motivo_sinal(rotulo="dinheiro_retido", citacao="cliente pagou e nunca recebeu o produto"),
            motivo_atributo("Status: Respondida (-1)"),
        ])],
        fila=["R1"],
    )
    html = relatorio.renderizar(est)
    assert "cliente pagou e nunca recebeu o produto" in html
    assert "Status: Respondida (-1)" in html


def test_fila_vazia_e_declarada_como_informacao_nao_erro():
    est = estado([], [], fila=[])
    html = relatorio.renderizar(est)
    assert "Nenhuma reclamação atingiu o corte de prioridade" in html


def test_barras_sentimento_proporcao_do_total_analisado():
    distribuicao = DistribuicaoSentimento(positivo=6, neutro=3, negativo=1)
    barras = relatorio._barras_sentimento(distribuicao, analisadas=10)
    assert [b["rotulo"] for b in barras] == ["Positivo", "Neutro", "Negativo"]
    assert [b["largura_pct"] for b in barras] == [60.0, 30.0, 10.0]


def test_barras_sentimento_sem_analisadas_nao_quebra():
    distribuicao = DistribuicaoSentimento(positivo=0, neutro=0, negativo=0)
    barras = relatorio._barras_sentimento(distribuicao, analisadas=0)
    assert all(b["largura_pct"] == 0.0 for b in barras)


def test_barras_ranking_maior_item_preenche_100_por_cento():
    ranking = [item_ranking("Celular", 8), item_ranking("Fone", 4), item_ranking("Cabo", 2)]
    barras = relatorio._barras_ranking(ranking)
    assert barras[0]["largura_pct"] == 100.0
    assert barras[1]["largura_pct"] == 50.0
    assert barras[2]["largura_pct"] == 25.0


def test_barras_ranking_vazio_nao_quebra_com_max_de_sequencia_vazia():
    assert relatorio._barras_ranking([]) == []


def test_produto_generico_marcado_visivelmente_no_ranking_renderizado():
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        ranking_produtos=[item_ranking("produto", 5, generico=True)],
    )
    html = relatorio.renderizar(est)
    assert "termo genérico" in html


def test_nao_identificado_visivel_no_ranking_com_total():
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        ranking_produtos=[item_ranking("não identificado", 7)],
    )
    html = relatorio.renderizar(est)
    assert "não identificado" in html
    assert "(7)" in html


def test_graficos_sem_biblioteca_externa():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    for proibido in ("<script src=", "<link href=", "@import"):
        assert proibido not in html


def test_ressalva_de_sentimento_fica_dentro_da_propria_secao():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    secao_sentimento = html.split('<section id="distribuicao-sentimento">', 1)[1]
    secao_sentimento_ate_proxima = secao_sentimento.split('<section id="ranking-produtos">', 1)[0]
    assert "Ressalva:" in secao_sentimento_ate_proxima


def test_ressalva_de_ranking_fica_dentro_da_propria_secao_antes_do_body_fechar():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    secao_ranking = html.split('<section id="ranking-produtos">', 1)[1]
    antes_de_fechar_body = secao_ranking.split("</body>", 1)[0]
    assert "Ressalva:" in antes_de_fechar_body


def test_textos_de_ressalva_sao_literais_no_template():
    texto = (relatorio._DIR_TEMPLATES / "relatorio.html.j2").read_text(encoding="utf-8")
    assert "não uma medida de satisfação geral dos clientes" in texto
    assert "volume não equivale a gravidade" in texto


def test_ranking_vazio_declara_nenhum_produto_identificado():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"], ranking_produtos=[])
    html = relatorio.renderizar(est)
    assert "Nenhum produto identificado nesta execução." in html


def test_barras_ranking_proporcao_com_dizima_nao_quebra():
    ranking = [item_ranking("A", 3), item_ranking("B", 1)]
    barras = relatorio._barras_ranking(ranking)
    assert barras[0]["largura_pct"] == 100.0
    assert abs(barras[1]["largura_pct"] - (100 / 3)) < 1e-9


def test_barras_sentimento_proporcao_com_dizima_arredonda():
    distribuicao = DistribuicaoSentimento(positivo=1, neutro=1, negativo=1)
    barras = relatorio._barras_sentimento(distribuicao, analisadas=3)
    larguras = [b["largura_pct"] for b in barras]
    assert all(abs(l - 33.333333333333336) < 1e-9 for l in larguras)


def test_html_renderizado_com_dizima_nao_quebra_o_round_do_template():
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        distribuicao_sentimento=DistribuicaoSentimento(positivo=1, neutro=1, negativo=1),
        analisadas=3,
    )
    html = relatorio.renderizar(est)
    assert 'width="66.7"' in html


def test_cabecalho_converte_data_e_repassa_contagens_sem_alteracao():
    ag = agregados([], analisadas=44, nao_analisadas=6, degradado=True,
                    motivo_degradacao="mais de 10% não analisadas (6/50)", data_execucao="2026-01-05")
    cab = relatorio._cabecalho(ag)
    assert cab["data_execucao"] == "05/01/2026"
    assert cab["analisadas"] == 44
    assert cab["nao_analisadas"] == 6
    assert cab["degradado"] is True
    assert cab["motivo_degradacao"] == "mais de 10% não analisadas (6/50)"


def test_marca_de_degradacao_visivel_quando_degradado():
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        degradado=True, motivo_degradacao="mais de 10% não analisadas (6/50)",
    )
    html = relatorio.renderizar(est)
    assert 'class="degradado"' in html
    assert "mais de 10% não analisadas (6/50)" in html


def test_execucao_limpa_nao_exibe_marca_de_degradacao():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"], degradado=False)
    html = relatorio.renderizar(est)
    assert 'class="degradado"' not in html


def test_cabecalho_exibe_data_e_contagens_no_html():
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        analisadas=48, nao_analisadas=2, data_execucao="2026-03-10",
    )
    html = relatorio.renderizar(est)
    assert "10/03/2026" in html
    assert "48 reclamações analisadas" in html
    assert "2 reclamações não analisadas" in html


def test_contagem_pt_br_pluraliza_no_singular():
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        analisadas=1, nao_analisadas=1,
    )
    html = relatorio.renderizar(est)
    assert "1 reclamação analisada" in html
    assert "1 reclamação não analisada" in html
    assert "1 reclamações" not in html


def test_declaracao_de_heuristica_de_engenharia_visivel_e_literal_no_template():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    assert "heurística de engenharia" in html
    texto = (relatorio._DIR_TEMPLATES / "relatorio.html.j2").read_text(encoding="utf-8")
    assert "heurística de engenharia" in texto


def test_declaracao_de_heuristica_fica_dentro_da_ressalva_na_secao_confiabilidade():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    secao = html.split('<section id="confiabilidade">', 1)[1]
    secao_ate_proxima = secao.split('<section id="distribuicao-sentimento">', 1)[0]
    assert '<p class="ressalva">Ressalva: esta classificação de risco' in secao_ate_proxima


def test_mensagem_de_degradacao_com_duas_condicoes_concatenadas():
    motivo = "mais de 10% não analisadas (6/50); todos os 3 códigos de sinal propostos foram derrubados"
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        degradado=True, motivo_degradacao=motivo,
    )
    html = relatorio.renderizar(est)
    assert motivo in html


def test_motivo_degradacao_com_marcacao_html_aparece_escapado():
    est = estado(
        [reclamacao("R1")], [pontuacao("R1")], fila=["R1"],
        degradado=True, motivo_degradacao="<b>falha</b> de transporte",
    )
    html = relatorio.renderizar(est)
    assert "<b>falha</b>" not in html
    assert "&lt;b&gt;falha&lt;/b&gt;" in html


def test_template_nao_faz_aritmetica_ou_comparacao_sobre_cabecalho():
    """AD-22: só expressões Jinja `{{ ... }}`/`{% ... %}` contam — HTML ao redor tem `/` de fechamento de tag."""
    texto = (relatorio._DIR_TEMPLATES / "relatorio.html.j2").read_text(encoding="utf-8")
    expressoes = re.findall(r"\{[{%].*?[%}]\}", texto)
    expressoes_com_cabecalho = [e for e in expressoes if "cabecalho" in e]
    assert expressoes_com_cabecalho, "esperava ao menos uma expressão Jinja referenciando cabecalho"
    for expressao in expressoes_com_cabecalho:
        for operador in ("+", "-", "*", "/", "==", ">", "<"):
            assert operador not in expressao, f"operador {operador!r} encontrado numa expressão sobre cabecalho: {expressao!r}"


def test_secao_de_confiabilidade_fica_entre_fila_e_sentimento():
    est = estado([reclamacao("R1")], [pontuacao("R1")], fila=["R1"])
    html = relatorio.renderizar(est)
    pos_fila = html.index('<section id="fila-prioridade">')
    pos_confiabilidade = html.index('<section id="confiabilidade">')
    pos_sentimento = html.index('<section id="distribuicao-sentimento">')
    assert pos_fila < pos_confiabilidade < pos_sentimento


def test_html_completo_sem_nenhuma_referencia_a_host_externo():
    """AC6 (Story 2.6): varredura abrangente, não só as seções de gráfico (Story 2.4)."""
    est = estado(
        [reclamacao("R1")],
        [pontuacao("R1", motivos=[motivo_sinal(), motivo_atributo()])],
        fila=["R1"],
        ranking_produtos=[item_ranking("produto", 3, generico=True), item_ranking("não identificado", 2)],
        distribuicao_sentimento=DistribuicaoSentimento(positivo=1, neutro=0, negativo=0),
        analisadas=1, nao_analisadas=0, degradado=True, motivo_degradacao="mais de 10% não analisadas (1/1)",
    )
    html = relatorio.renderizar(est)
    assert not re.search(r'(src|href)\s*=\s*["\']https?://', html)
    assert not re.search(r'@import\s+url\(["\']?https?:', html)


def test_import_relatorio_sem_credencial(monkeypatch):
    import importlib
    import sys

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "plataforma.relatorio", raising=False)
    modulo = importlib.import_module("plataforma.relatorio")
    assert modulo.__name__ == "plataforma.relatorio", \
        "import de plataforma.relatorio não deveria exigir credencial"
