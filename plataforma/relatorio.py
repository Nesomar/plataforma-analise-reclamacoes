"""Renderiza o relatório HTML: a fila de prioridade é o primeiro conteúdo do arquivo.

Único módulo do pacote com um `jinja2.Environment` (AD-10). `autoescape=True` é
literal, não `select_autoescape` — o seletor casaria `relatorio.html.j2` por extensão
`.j2` no ramo `default=False` e desligaria o escape justo na linha que parece a defesa.

`renderizar` monta a lista de itens da fila fora do template: para cada id em
`agregados["fila"]` (ordem já resolvida por `agregar`, nunca reordenada aqui), junta o
`Motivo` de `Pontuacao` com empresa/título/data de `Reclamacao`. O template só exibe —
nenhuma condicional nele consulta `Reclamacao` para decidir por que um item está na
fila (AD-4): a resposta já está pronta em `motivos` antes de chegar lá.

Os gráficos de sentimento e ranking (Story 2.4) seguem o mesmo princípio: `_barras_*`
calcula a geometria (largura proporcional) em Python — mesmo lugar que já guarda a
divisão por zero em `agregacao.py` — e devolve listas prontas para o `for` do template.
O texto de ressalva (FR-18/AD-14) não vem daqui: é literal no `.j2` (AD-10).

Esta story não escreve arquivo em disco nem decide nome de saída — isso é FR-1b, Story
2.6. `renderizar` devolve a string HTML; quem grava é o nó que a Story 2.6 acrescenta.
"""

import re
from pathlib import Path
from typing import TypedDict

from jinja2 import Environment, FileSystemLoader

from plataforma.estado import Agregados, DistribuicaoSentimento, Estado, ItemRanking, Motivo, Pontuacao, Reclamacao

_DIR_TEMPLATES = Path(__file__).parent / "templates"

# Único Environment do pacote (AD-10). autoescape=True literal — nunca select_autoescape,
# que casearia por extensão e cairia em default=False para "relatorio.html.j2" (.j2 não
# está entre as extensões padrão dele). trim_blocks/lstrip_blocks: só cosmético, cortam a
# linha em branco e a indentação que cada tag `{% %}` deixaria no HTML renderizado.
_ENVIRONMENT = Environment(
    loader=FileSystemLoader(_DIR_TEMPLATES),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

_ISO_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")


def _data_br(iso: str) -> str:
    """`"AAAA-MM-DD"` -> `"DD/MM/AAAA"` (FR-17). Troca de posição, sem parsing de data."""
    if not _ISO_DATA.fullmatch(iso):
        raise ValueError(f"data {iso!r} não está no formato ISO-8601 AAAA-MM-DD")
    ano, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{ano}"


class ItemFila(TypedDict):
    """Item de exibição da fila — junta `Reclamacao` e `Pontuacao` para o template."""
    id: str
    empresa: str
    titulo: str
    data: str  # já em pt-BR (DD/MM/AAAA)
    pontos: int
    motivos: list[Motivo]


def _itens_fila(
    fila: list[str],
    pontuacoes_por_id: dict[str, Pontuacao],
    reclamacoes_por_id: dict[str, Reclamacao],
) -> list[ItemFila]:
    """Um item de exibição por id da fila, na ordem que `agregar` já resolveu (AD-19)."""
    itens: list[ItemFila] = []
    for id_ in fila:
        pontuacao = pontuacoes_por_id[id_]
        reclamacao = reclamacoes_por_id[id_]
        itens.append(ItemFila(
            id=id_,
            empresa=reclamacao["empresa"],
            titulo=reclamacao["titulo"],
            data=_data_br(reclamacao["data"]),
            pontos=pontuacao["pontos"],
            motivos=pontuacao["motivos"],
        ))
    return itens


_ROTULOS_SENTIMENTO = (("positivo", "Positivo"), ("neutro", "Neutro"), ("negativo", "Negativo"))


class BarraSentimento(TypedDict):
    rotulo: str  # "Positivo"/"Neutro"/"Negativo" — pt-BR, nunca o Literal cru do estado
    total: int
    largura_pct: float


def _barras_sentimento(distribuicao: DistribuicaoSentimento, analisadas: int) -> list[BarraSentimento]:
    """Uma barra por categoria, ordem fixa positivo→neutro→negativo (não a de um dict).

    `largura_pct` é a proporção do total analisado — as três categorias somam
    `analisadas` (toda `Analise` tem exatamente um sentimento), por isso a proporção
    soma 100%. Guard de `analisadas == 0` no mesmo padrão que `agregacao.py` já usa em
    `ocupacao_fila`/`taxa_produto_nao_nomeado`.
    """
    return [
        BarraSentimento(
            rotulo=rotulo_br,
            total=distribuicao[chave],
            largura_pct=(distribuicao[chave] / analisadas * 100) if analisadas else 0.0,
        )
        for chave, rotulo_br in _ROTULOS_SENTIMENTO
    ]


class BarraRanking(TypedDict):
    rotulo: str
    total: int
    generico: bool
    largura_pct: float


def _barras_ranking(ranking: list[ItemRanking]) -> list[BarraRanking]:
    """Uma barra por item de `ranking_produtos`, na ordem dada — não reordena (AD-19/AD-22).

    `largura_pct` é relativa ao maior `total` do ranking (é ranking, não distribuição
    que precise somar 100%): o item mais reclamado preenche a largura útil inteira.
    """
    if not ranking:
        return []
    maior_total = max(item["total"] for item in ranking)
    return [
        BarraRanking(
            rotulo=item["rotulo"],
            total=item["total"],
            generico=item["generico"],
            largura_pct=(item["total"] / maior_total * 100) if maior_total else 0.0,
        )
        for item in ranking
    ]


class Cabecalho(TypedDict):
    data_execucao: str  # já em pt-BR (DD/MM/AAAA)
    analisadas: int
    analisadas_rotulo: str  # "1 reclamação analisada" / "N reclamações analisadas" (FR-17)
    nao_analisadas: int
    nao_analisadas_rotulo: str
    degradado: bool
    motivo_degradacao: str | None


def _contagem_pt_br(n: int, singular: str, plural: str) -> str:
    """`f"{n} {singular|plural}"` — mesma pluralização que `agregacao._motivo_degradacao` já usa."""
    return f"{n} {singular if n == 1 else plural}"


def _cabecalho(agregados: Agregados) -> Cabecalho:
    """Repassa data/contagens/degradação de `Agregados` — nenhum cálculo aqui (AD-22).

    `motivo_degradacao` já vem pronto de `agregacao._motivo_degradacao` (Story 2.2);
    a data passa por `_data_br` para virar pt-BR e as contagens ganham rótulo pluralizado
    corretamente (FR-17) — pluralização é gramática de apresentação, não um cálculo sobre
    o número reportado.
    """
    analisadas = agregados["analisadas"]
    nao_analisadas = agregados["nao_analisadas"]
    return Cabecalho(
        data_execucao=_data_br(agregados["data_execucao"]),
        analisadas=analisadas,
        analisadas_rotulo=_contagem_pt_br(analisadas, "reclamação analisada", "reclamações analisadas"),
        nao_analisadas=nao_analisadas,
        nao_analisadas_rotulo=_contagem_pt_br(nao_analisadas, "reclamação não analisada", "reclamações não analisadas"),
        degradado=agregados["degradado"],
        motivo_degradacao=agregados["motivo_degradacao"],
    )


def renderizar(estado: Estado) -> str:
    """Devolve o HTML do relatório — fila de prioridade como primeiro conteúdo (FR-11)."""
    agregados = estado["agregados"]
    pontuacoes_por_id = {p["id"]: p for p in estado["pontuacoes"]}
    reclamacoes_por_id = {r["id"]: r for r in estado["reclamacoes"]}

    template = _ENVIRONMENT.get_template("relatorio.html.j2")
    return template.render(
        itens_fila=_itens_fila(agregados["fila"], pontuacoes_por_id, reclamacoes_por_id),
        cabecalho=_cabecalho(agregados),
        barras_sentimento=_barras_sentimento(agregados["distribuicao_sentimento"], agregados["analisadas"]),
        barras_ranking=_barras_ranking(agregados["ranking_produtos"]),
    )
