"""Confere cada citação de sinal contra o texto original, sem chamar o modelo de novo.

A parte não-óbvia não é a comparação de string — é o agrupamento por `codigo` (AD-2):
se qualquer citação de um código falha a checagem individual, todo `Sinal` daquele
mesmo código sai `valida=False`, inclusive os que teriam passado sozinhos. Um código só
é confiável se cada citação que o sustenta resiste à conferência; um par validado ao
lado de um inventado não é evidência parcial, é evidência que não se sabe separar.
"""

from plataforma.estado import Sinal


def _passa_checagem_individual(citacao: str, texto: str) -> bool:
    # As duas condições no mesmo lugar (AD-1, FR-6): substring exata E piso de 5
    # palavras. Citação vazia é substring de qualquer texto, mas `"".split()` tem
    # comprimento zero — reprova pelo piso sem precisar de caso especial.
    return citacao in texto and len(citacao.split()) >= 5


def verificar(sinais: list[Sinal], texto: str) -> list[Sinal]:
    """Recalcula `valida` de cada `Sinal` e devolve nova lista, mesma ordem de entrada.

    Função pura: não muta `sinais`. Primeiro calcula a checagem individual de cada
    `Sinal`; depois agrupa por `codigo` e decide `valida` por grupo (AD-2) — todos os
    `Sinal` de um código só ficam `valida=True` se todas as citações daquele código
    passaram individualmente. Checar `Sinal` isolado sem esse agrupamento deixaria um
    código sustentado por uma citação fabricada parecer parcialmente válido.
    """
    individual = [_passa_checagem_individual(s["citacao"], texto) for s in sinais]

    codigo_valido: dict[str, bool] = {}
    for sinal, passou in zip(sinais, individual):
        codigo = sinal["codigo"]
        codigo_valido[codigo] = codigo_valido.get(codigo, True) and passou

    return [
        Sinal(codigo=s["codigo"], citacao=s["citacao"], valida=codigo_valido[s["codigo"]])
        for s in sinais
    ]
