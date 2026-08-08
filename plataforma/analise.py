"""Chama o modelo para extrair sentimento, produto e sinais de risco de um lote.

Único módulo que importa `google.genai` (AD-7): o cliente nasce dentro de
`analisar_lote`, nunca em escopo de módulo, para que `import plataforma.analise`
funcione sem credencial. A parte impura fica fina — cliente, payload, chamada — e toda
decisão (casamento por id, descarte de repetido/inventado, verificação de evidência,
montagem de `Falha`) mora em `_montar_delta`, pura. Essa separação não é estilo: é o
que torna a story testável, já que o repositório proíbe mock do `google.genai` — a
única forma de exercitar "resposta incompleta" ou "fora do schema" é alimentar
`_montar_delta` com uma lista fabricada ou `None`, nunca uma resposta HTTP de verdade.
"""

import json
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel

from plataforma import catalogo, config, evidencia
from plataforma.estado import Analise, Falha, Reclamacao, Sinal


class _SinalResposta(BaseModel):
    """Forma que o modelo devolve por sinal — sem `valida`: só o código decide isso."""

    codigo: str
    citacao: str


class _AnaliseResposta(BaseModel):
    """Forma que o modelo devolve por reclamação, antes do casamento por id."""

    id: str
    sentimento: Literal["positivo", "neutro", "negativo"]
    produto: str | None
    sinais: list[_SinalResposta]


class _LoteResposta(BaseModel):
    """Envelope do `response_schema`: o modelo devolve um lote inteiro por chamada."""

    analises: list[_AnaliseResposta]


def _montar_payload(lote: list[Reclamacao]) -> list[dict]:
    """Só `id` e `texto` atravessam para o modelo (AD-16).

    `empresa` e `titulo` ficam de fora por construção — o payload nunca os carrega,
    então não há instrução de prompt para o modelo desobedecer. `titulo` em especial
    entregaria a resposta: é canônico nesta base e `baseline.py` já classifica por
    match exato dele.
    """
    return [{"id": r["id"], "texto": r["texto"]} for r in lote]


def _montar_instrucao() -> str:
    """Monta o prompt a partir de `catalogo.CATALOGO` — fonte única dos sinais (AD-18).

    As definições e exemplos não são reescritos aqui: vivem em `catalogo.py`, validados
    contra o gabarito humano. Esta função só formata o que já existe lá dentro do texto
    de instrução, junto das regras de sentimento e produto.
    """
    linhas = [
        "Você analisa reclamações de consumidores brasileiros.",
        "",
        "Para cada reclamação do lote, devolva:",
        "",
        '- sentimento: "positivo", "neutro" ou "negativo".',
        "- produto: o produto ou serviço mencionado no texto, como você o leu, em uma "
        "ou duas palavras. null se o texto não permitir identificar. Não julgue se é "
        "genérico — devolva exatamente o que o texto diz.",
        "- sinais: lista de sinais de risco detectados, cada um com `codigo` e "
        "`citacao`. `citacao` precisa ser um trecho LITERAL do texto original, copiado "
        "caractere por caractere, com no mínimo cinco palavras. Nunca invente citação: "
        "se não houver trecho literal que sustente um sinal, não o inclua.",
        "",
        "Códigos de sinal disponíveis, cada um com sua definição e um exemplo:",
    ]
    for codigo, dados in catalogo.CATALOGO.items():
        linhas.append(f"\n- {codigo}: {dados['definicao']}\n  Exemplo: {dados['exemplo']}")
    return "\n".join(linhas)


def analisar_lote(lote: list[Reclamacao]) -> dict:
    """Chama o modelo sobre `lote` e devolve o delta `{"analises": ..., "falhas": ...}`.

    Falha de transporte (rede, limite de taxa) propaga daqui — não há `try/except`
    genérico em volta de `generate_content`; `retry_policy`/`error_handler` no nó do
    grafo (Story 1.6) são quem tratam isso (AD-9). O único desvio tratado aqui é de
    conteúdo: resposta que não casa com `response_schema`.
    """
    if not lote:
        return {"analises": [], "falhas": []}

    cliente = genai.Client()
    resposta = cliente.models.generate_content(
        model=config.carregar().modelo,
        contents=json.dumps(_montar_payload(lote), ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=_montar_instrucao(),
            response_mime_type="application/json",
            response_schema=_LoteResposta,
            temperature=0,
        ),
    )
    analises_modelo = resposta.parsed.analises if resposta.parsed else None
    return _montar_delta(lote, analises_modelo)


def _montar_delta(
    lote: list[Reclamacao],
    analises_modelo: list[_AnaliseResposta] | None,
) -> dict:
    """Casa a resposta do modelo com o lote por `id`. Função pura, sem SDK.

    `analises_modelo is None` significa que `response.parsed` não foi montado — a
    resposta não casou com o schema (verificado no código-fonte do SDK instalado:
    `google/genai/types.py:8708-8724` engole `ValidationError`/`JSONDecodeError` e
    simplesmente deixa `.parsed` sem valor, nunca levanta). Todo o lote vira uma única
    `Falha`, porque sem resposta casada não há como saber qual item era qual.

    Id inventado (fora do lote) e id repetido são apenas descartados — não geram
    `Falha`, porque não correspondem a uma reclamação enviada que ficou sem análise;
    são ruído do modelo. Falha existe só para reclamação que **entrou** no lote e
    **não saiu** com análise.
    """
    if analises_modelo is None:
        return {
            "analises": [],
            "falhas": [Falha(
                ids=[r["id"] for r in lote],
                causa="resposta do modelo fora do schema esperado",
                no="analisar_lote",
            )],
        }

    ids_do_lote = {r["id"] for r in lote}
    textos_por_id = {r["id"]: r["texto"] for r in lote}

    casadas: dict[str, _AnaliseResposta] = {}
    for item in analises_modelo:
        if item.id not in ids_do_lote or item.id in casadas:
            continue
        casadas[item.id] = item

    analises: list[Analise] = []
    for id_, item in casadas.items():
        sinais_brutos: list[Sinal] = [
            Sinal(codigo=s.codigo, citacao=s.citacao, valida=False) for s in item.sinais
        ]
        sinais_verificados = evidencia.verificar(sinais_brutos, textos_por_id[id_])
        analises.append(Analise(
            id=id_,
            sentimento=item.sentimento,
            produto=item.produto,
            sinais=sinais_verificados,
            prazo_prometido_dias=None,
            data_evento=None,
        ))

    faltantes = [r["id"] for r in lote if r["id"] not in casadas]
    falhas = [Falha(
        ids=faltantes,
        causa="resposta do modelo sem esse(s) identificador(es)",
        no="analisar_lote",
    )] if faltantes else []

    return {"analises": analises, "falhas": falhas}
