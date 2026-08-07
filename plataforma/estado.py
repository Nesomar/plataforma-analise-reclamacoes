"""Contrato de estado do pipeline: a forma exata que atravessa todos os nós do grafo.

Este é o único módulo do v1 cuja mudança não é aditiva — todo nó lê e escreve estas
chaves, então renomear campo aqui quebra etapa que ninguém tocou. Por isso ele não
importa nada de `plataforma/`: nenhum filtro pode influenciar a forma do dado que
todos compartilham.
"""

from operator import add
from typing import Annotated, Literal, TypedDict


class Reclamacao(TypedDict):
    id: str  # ID_Reclamacao do CSV — já único na origem
    data: str  # ISO-8601, convertido de DD/MM/AAAA na fronteira de leitura
    empresa: str
    titulo: str
    texto: str  # coluna Descricao do CSV
    cidade_estado: str
    status: Literal["Respondida", "Não respondida",
                    "Resolvido", "Não resolvido", "Em réplica"]


class Sinal(TypedDict):
    codigo: str  # um dos seis de catalogo.py
    citacao: str  # literal, piso de 5 palavras
    valida: bool
    # `valida` é bool puro, nunca bool | None: não verificado é indistinguível de
    # reprovado, e o terceiro estado só criaria caminho para esquecer de rodar a
    # verificação. TypedDict não tem default de verdade — a garantia é que todo
    # caminho que constrói um Sinal preenche `valida`, começando em False.


class Analise(TypedDict):
    id: str  # liga de volta à Reclamacao — obrigatório, casamento nunca é por posição
    sentimento: Literal["positivo", "neutro", "negativo"]
    produto: str | None  # como o modelo leu, sem julgamento de genérico
    sinais: list[Sinal]  # par indivisível código↔citação
    prazo_prometido_dias: int | None
    data_evento: str | None  # ISO-8601 ou None


class Falha(TypedDict):
    ids: list[str]  # reclamações que ficaram sem análise
    causa: str
    no: str  # nome do nó que falhou


class Motivo(TypedDict):
    origem: Literal["sinal", "atributo"]
    rotulo: str
    citacao: str | None  # não-nula sse origem == "sinal"


class Pontuacao(TypedDict):
    id: str
    pontos: int
    na_fila: bool
    motivos: list[Motivo]  # o que o relatório exibe


class ItemRanking(TypedDict):
    rotulo: str  # produto como o modelo leu, ou "não identificado"
    total: int
    generico: bool  # termo da lista canônica de catalogo.py


class DistribuicaoSentimento(TypedDict):
    positivo: int
    neutro: int
    negativo: int


class Agregados(TypedDict):
    data_execucao: str  # ISO-8601; o template formata em pt-BR
    lidas: int  # FR-2, FR-14
    analisadas: int  # FR-2, FR-14
    nao_analisadas: int  # sum(len(f["ids"]) for f in falhas)
    eventos_falha: int  # len(falhas) — AD-5 pede os dois números, não um só
    codigos_propostos: int  # denominador de CM-2 e da 2ª condição de NFR-6
    codigos_derrubados: int  # CM-2, FR-2
    fila: list[str]  # ids na ordem de exibição da fila
    total_na_fila: int
    ocupacao_fila: float  # CM-1
    taxa_produto_nao_nomeado: float  # CM-3 — nulo MAIS genérico
    ranking_produtos: list[ItemRanking]  # FR-8, FR-13
    distribuicao_sentimento: DistribuicaoSentimento
    degradado: bool  # NFR-6
    motivo_degradacao: str | None  # qual das duas condições disparou


class Estado(TypedDict):
    reclamacoes: list[Reclamacao]
    analises: Annotated[list[Analise], add]  # acumula entre execuções de lote
    falhas: Annotated[list[Falha], add]  # acumula entre execuções de lote
    pontuacoes: list[Pontuacao]
    agregados: Agregados
    caminho_html: str
