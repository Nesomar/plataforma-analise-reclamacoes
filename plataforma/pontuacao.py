"""Pontua cada reclamação analisada e carrega o motivo de cada pontos ganho.

Duas granularidades coexistem de propósito: pontuação é **por código distinto**
válido (duas citações do mesmo código não dobram o peso — AD-2), mas `Motivo` é
**por instância de `Sinal`** (cada citação continua evidência visível, FR-12). Grupo A
(`ameaca_explicita`/`lei_citada`) satura em uma parcela só, lida de
`catalogo.GRUPO_SINAL_A` — a regra não é reimplementada aqui, só consultada.

**`PESOS` deriva de `catalogo.CATALOGO`, nunca retipa o nome de um código.** AD-18
proíbe código de sinal como literal solto neste módulo — um mapeamento escrito aqui
com os nomes dos códigos violaria exatamente isso, e `tests/test_catalogo.py` varre o
pacote inteiro procurando por essa violação (achado de revisão: a primeira versão
deste módulo caiu nela). O peso de cada código é dado que vive junto da definição em
`catalogo.py` (Story 2.1, corrigido em revisão) — este módulo só lê `dados["peso"]`.
"""

from types import MappingProxyType

from plataforma import catalogo
from plataforma.estado import Estado, Motivo, Pontuacao

# Fonte única em catalogo.CATALOGO[codigo]["peso"] — este módulo só lê, nunca declara
# um código como string literal (AD-18).
PESOS = MappingProxyType({
    codigo: dados["peso"] for codigo, dados in catalogo.CATALOGO.items()
})

CORTE = 3

# Único atributo do CSV com peso na tabela ratificada — sempre modificador, nunca
# parcela independente. Sozinho, nunca põe uma reclamação na fila (risk-signals.md).
MODIFICADOR_STATUS_RESPONDIDA = -1


def pontuar(estado: Estado) -> dict:
    """Devolve `{"pontuacoes": [...]}`, uma `Pontuacao` por `Analise`, ordem preservada."""
    reclamacoes_por_id = {r["id"]: r for r in estado["reclamacoes"]}
    pontuacoes: list[Pontuacao] = []

    for analise in estado["analises"]:
        reclamacao = reclamacoes_por_id[analise["id"]]
        motivos: list[Motivo] = []
        codigos_validos: set[str] = set()

        for sinal in analise["sinais"]:
            if not sinal["valida"]:
                continue
            motivos.append(Motivo(
                origem="sinal", citacao=sinal["citacao"], rotulo=sinal["codigo"],
            ))
            codigos_validos.add(sinal["codigo"])

        # Grupo A satura por VALOR, não pela ordem em que os códigos apareceram — usar
        # o maior peso do grupo entre os presentes, nunca "o primeiro que eu vi", que só
        # dava certo hoje porque os dois pesos do grupo são iguais por coincidência.
        codigos_grupo_a_presentes = codigos_validos & set(catalogo.GRUPO_SINAL_A)
        codigos_fora_do_grupo_a = codigos_validos - codigos_grupo_a_presentes

        pontos = sum(PESOS.get(codigo, 0) for codigo in codigos_fora_do_grupo_a)
        if codigos_grupo_a_presentes:
            pontos += max(PESOS.get(codigo, 0) for codigo in codigos_grupo_a_presentes)

        if reclamacao["status"] == "Respondida":
            pontos += MODIFICADOR_STATUS_RESPONDIDA
            motivos.append(Motivo(
                origem="atributo", citacao=None,
                rotulo=f"Status: Respondida ({MODIFICADOR_STATUS_RESPONDIDA:+d})",
            ))

        pontuacoes.append(Pontuacao(
            id=analise["id"], pontos=pontos, na_fila=pontos >= CORTE, motivos=motivos,
        ))

    return {"pontuacoes": pontuacoes}
