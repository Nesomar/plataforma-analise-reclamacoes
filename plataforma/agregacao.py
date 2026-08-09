"""Agrega `analises` e `pontuacoes` em `Agregados`: ranking, distribuição, fila e degradação.

Duas contagens (`codigos_propostos`, `codigos_derrubados`) somam por `Analise`, sem
deduplicar entre reclamações: mesmo código derrubado em cinco reclamações diferentes
conta cinco — é a taxa que CM-2 mede, não um conjunto de códigos ruins no catálogo.
Mesma semântica que `main._contar_codigos_derrubados` (Story 1.7) já usa; duplicada
conscientemente aqui porque `agregacao.py` não pode importar `main.py` (inversão de
dependência, `main` é o entrypoint) e religar `main.py` para ler deste módulo está fora
do escopo desta story.

Marcação de "genérico" no ranking reaproveita `catalogo.nao_nomeia_produto` — a
normalização (NFC, lower, plural) já existe lá, não é reimplementada aqui.
"""

import datetime

from plataforma import catalogo
from plataforma.estado import Agregados, Analise, DistribuicaoSentimento, Estado, ItemRanking, Pontuacao, Reclamacao

_LIMIAR_NAO_ANALISADAS = 0.10


def _contar_codigos(analises: list[Analise]) -> tuple[int, int]:
    """Códigos propostos e derrubados, por reclamação, somados sem deduplicar (CM-2)."""
    propostos = 0
    derrubados = 0
    for analise in analises:
        codigos = {s["codigo"] for s in analise["sinais"]}
        invalidos = {s["codigo"] for s in analise["sinais"] if not s["valida"]}
        propostos += len(codigos)
        derrubados += len(invalidos)
    return propostos, derrubados


def _ranking_produtos(analises: list[Analise]) -> list[ItemRanking]:
    """Agrupa por texto literal de `produto` (AD-21) — sem normalizar case/acentuação.

    `produto=None` ou string vazia/só espaços vira `"não identificado"` (FR-8), agrupado
    por uma sentinela própria — nunca pela string literal `"não identificado"` — para
    que um produto real cujo texto seja essa mesma frase não se funda com o balde de
    nulo (achado de revisão). Espaço externo é removido do texto antes de agrupar:
    `"Celular"` e `" Celular "` são o mesmo produto (higiene de dado, não julgamento de
    conteúdo — AD-21 protege o *conteúdo* do texto, não espaço em volta dele). Só a
    checagem de genérico usa a normalização de `catalogo.nao_nomeia_produto`, porque é
    especificamente sobre a lista fechada de termos, não sobre o produto em geral.
    """
    _SEM_PRODUTO = object()
    contagem: dict[object, int] = {}
    for analise in analises:
        produto = analise["produto"]
        chave = _SEM_PRODUTO if produto is None or not produto.strip() else produto.strip()
        contagem[chave] = contagem.get(chave, 0) + 1

    itens = []
    for chave, total in contagem.items():
        if chave is _SEM_PRODUTO:
            itens.append(ItemRanking(rotulo="não identificado", total=total, generico=False))
        else:
            itens.append(ItemRanking(
                rotulo=chave, total=total, generico=catalogo.nao_nomeia_produto(chave),
            ))
    # Ordem determinística: total decrescente, desempate alfabético — não depende da
    # ordem de iteração do dict.
    itens.sort(key=lambda item: (-item["total"], item["rotulo"]))
    return itens


def _distribuicao_sentimento(analises: list[Analise]) -> DistribuicaoSentimento:
    distribuicao = DistribuicaoSentimento(positivo=0, neutro=0, negativo=0)
    for analise in analises:
        distribuicao[analise["sentimento"]] += 1
    return distribuicao


def _fila_ordenada(pontuacoes: list[Pontuacao], reclamacoes_por_id: dict[str, Reclamacao]) -> list[str]:
    """Fila de ids com `na_fila=True`, ordem total e determinística (NFR-8, AC7).

    `na_fila` já veio de `pontuar` (AD-19) — esta função só filtra e ordena, nunca
    recalcula a partir de `pontos`.
    """
    itens = [p for p in pontuacoes if p["na_fila"]]
    itens.sort(key=lambda p: (-p["pontos"], reclamacoes_por_id[p["id"]]["data"], p["id"]))
    return [p["id"] for p in itens]


def _motivo_degradacao(falha: bool, derrubada: bool, nao_analisadas: int, lidas: int,
                        codigos_propostos: int) -> str | None:
    """Nomeia qual das duas condições de NFR-6 disparou, com os números observados."""
    motivos = []
    if falha:
        motivos.append(f"mais de 10% não analisadas ({nao_analisadas}/{lidas})")
    if derrubada:
        plural = "s" if codigos_propostos != 1 else ""
        motivos.append(f"todos os {codigos_propostos} código{plural} de sinal propostos foram derrubados")
    return "; ".join(motivos) if motivos else None


def agregar(estado: Estado) -> dict:
    """Devolve `{"agregados": Agregados(...)}`. Só ordena e conta — `agregados` é a
    única chave que este nó escreve (AD-19)."""
    reclamacoes = estado["reclamacoes"]
    analises = estado["analises"]
    falhas = estado["falhas"]
    pontuacoes = estado["pontuacoes"]

    lidas = len(reclamacoes)
    analisadas = len(analises)
    nao_analisadas = sum(len(f["ids"]) for f in falhas)
    eventos_falha = len(falhas)

    codigos_propostos, codigos_derrubados = _contar_codigos(analises)

    ranking_produtos = _ranking_produtos(analises)
    distribuicao_sentimento = _distribuicao_sentimento(analises)

    reclamacoes_por_id = {r["id"]: r for r in reclamacoes}
    fila = _fila_ordenada(pontuacoes, reclamacoes_por_id)
    total_na_fila = len(fila)
    ocupacao_fila = total_na_fila / analisadas if analisadas else 0.0

    taxa_produto_nao_nomeado = (
        sum(catalogo.nao_nomeia_produto(a["produto"]) for a in analises) / analisadas
        if analisadas else 0.0
    )

    # NFR-6: o número usado é reclamações afetadas (nao_analisadas), não eventos de
    # Falha (AD-5) — poucos eventos podem cobrir muitas reclamações.
    degradado_falha = lidas > 0 and (nao_analisadas / lidas) > _LIMIAR_NAO_ANALISADAS
    degradado_derrubada = codigos_propostos > 0 and codigos_derrubados == codigos_propostos
    degradado = degradado_falha or degradado_derrubada

    agregados = Agregados(
        data_execucao=datetime.date.today().isoformat(),
        lidas=lidas,
        analisadas=analisadas,
        nao_analisadas=nao_analisadas,
        eventos_falha=eventos_falha,
        codigos_propostos=codigos_propostos,
        codigos_derrubados=codigos_derrubados,
        fila=fila,
        total_na_fila=total_na_fila,
        ocupacao_fila=ocupacao_fila,
        taxa_produto_nao_nomeado=taxa_produto_nao_nomeado,
        ranking_produtos=ranking_produtos,
        distribuicao_sentimento=distribuicao_sentimento,
        degradado=degradado,
        motivo_degradacao=_motivo_degradacao(
            degradado_falha, degradado_derrubada, nao_analisadas, lidas, codigos_propostos,
        ),
    )
    return {"agregados": agregados}
