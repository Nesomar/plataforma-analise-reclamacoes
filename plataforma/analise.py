"""Chama o modelo para extrair sentimento, produto e sinais de risco de um lote.

Único módulo que importa `google.genai` (AD-7): o cliente nasce dentro de
`analisar_lote`, nunca em escopo de módulo, para que `import plataforma.analise`
funcione sem credencial. A parte impura fica fina — cliente, payload, chamada — e toda
decisão (casamento por id, descarte de repetido/inventado, verificação de evidência,
montagem de `Falha`) mora em `_montar_delta`, pura. Essa separação não é estilo: é o
que torna a story testável, já que o repositório proíbe mock do `google.genai` — a
única forma de exercitar "resposta incompleta" ou "fora do schema" é alimentar
`_montar_delta` com uma lista fabricada ou `None`, nunca uma resposta HTTP de verdade.

**Retry de falha de transporte vive aqui dentro (Story 1.6, revisão de 2026-08-08),
não em `retry_policy`/`error_handler` do LangGraph.** Investigação empírica contra
`langgraph==1.2.10` mostrou que `error_handler` roda mas não impede a exceção original
de abortar o `.invoke()` inteiro quando há mais de uma task concorrente no mesmo step
— exatamente o caso do fan-out via `Send` que a Story 1.6 implementa. Testado em 6
configurações (invoke puro, com checkpointer, `durability=sync/exit`, `.stream()`),
todas com o mesmo resultado; só o caso de nó único sem concorrência funciona como a
documentação descreve. Isso diverge da leitura original de AD-9 ("o código do nó não
tem laço de repetição próprio") — divergência ratificada nesta story porque o mecanismo
que AD-9 presumia (`retry_policy` do LangGraph) não entrega o que promete nesta
topologia. `analisar_lote` nunca deixa exceção escapar: qualquer falha de transporte,
depois de esgotado `_chamar_com_retry`, vira `Falha` como retorno normal, nunca
propaga — é assim que "os demais lotes seguem executando normalmente" (AC3 da Story
1.6) se torna verdade na prática, e não só na introspecção estrutural do grafo.

**Instrumentação pontual de custo (Story 3.2).** `_metricas` conta chamadas e tokens
reais gastos com o modelo — não é campo de `Estado` porque não é dado de domínio, é
contagem de infraestrutura que só a medição de M-4/NFR-3 lê. `chamadas` soma a cada
tentativa real de `_gerar()`, sucesso ou não — a quota é gasta na chamada, não no
resultado, e é por isso que `_registrar_tentativa()` roda **antes** de `generate_content`
retornar (achado de revisão: contar só depois do sucesso nunca detectaria retry).
`tokens_entrada`/`tokens_saida` só somam numa resposta bem-sucedida com
`usage_metadata` — uma tentativa que falhou não tem tokens para contar, só a tentativa
em si. `resetar_metricas()`/`ler_metricas()` são o único jeito de zerar/ler; nenhum nó
do grafo escreve nem lê essas chaves.
"""

import json
import time
from typing import Callable, Literal, TypeVar

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from plataforma import catalogo, config, evidencia
from plataforma.estado import Analise, Falha, Reclamacao, Sinal

_T = TypeVar("_T")

_TENTATIVAS = 3
_ESPERA_INICIAL_S = 0.5
_FATOR_BACKOFF = 2.0

_metricas = {"chamadas": 0, "tokens_entrada": 0, "tokens_saida": 0}


def ler_metricas() -> dict:
    """Cópia de `_metricas` — nunca a referência, para quem lê não poder mutar."""
    return dict(_metricas)


def resetar_metricas() -> None:
    """Zera os três contadores. Chamado pelo script de medição, nunca pelo pipeline."""
    _metricas.update(chamadas=0, tokens_entrada=0, tokens_saida=0)


def _registrar_tentativa() -> None:
    """+1 chamada — a cada tentativa real de `generate_content`, sucesso ou não.

    Separado de `_registrar_tokens` (achado de revisão): uma tentativa que falha
    consome quota mesmo sem devolver `usage_metadata` — não há tokens para contar,
    mas a chamada aconteceu e precisa contar como tal, senão `medir_tempo_custo.py`
    nunca detecta retry de transporte (a contagem de chamadas nunca excederia o
    número de lotes emitidos).
    """
    _metricas["chamadas"] += 1


def _registrar_tokens(resposta) -> None:
    """Soma tokens de uma resposta bem-sucedida. `usage_metadata` pode faltar
    (guard, achado de revisão) — nesse caso não há o que somar, mas isso não é
    motivo para levantar `AttributeError` e transformar uma chamada boa em `Falha`.
    """
    uso = getattr(resposta, "usage_metadata", None)
    if uso is None:
        return
    _metricas["tokens_entrada"] += uso.prompt_token_count or 0
    _metricas["tokens_saida"] += uso.candidates_token_count or 0


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


def _deve_repetir(erro: Exception) -> bool:
    """Só repete falha de transporte de verdade — nunca falha permanente (AD-9, AC4).

    `ClientError` (4xx) cobre de credencial inválida (401, permanente — repetir é só
    desperdiçar `_TENTATIVAS` com backoff) a limite de taxa (429, transitório — é
    exatamente o caso que AC4 pede para repetir). `ServerError` (5xx) e erro de conexão
    são sempre transitórios. Qualquer outra exceção é tratada como permanente por
    padrão — repetir um erro desconhecido às cegas é mais perigoso que falhar rápido.
    """
    if isinstance(erro, genai_errors.ServerError):
        return True
    if isinstance(erro, genai_errors.ClientError):
        return erro.code == 429
    return isinstance(erro, (ConnectionError, TimeoutError, OSError))


def _chamar_com_retry(chamar: Callable[[], _T]) -> _T:
    """Repete `chamar()` com backoff exponencial, só para falha classificada como transitória.

    Pura o bastante para testar sem SDK: `chamar` é injetado pelo chamador, então o
    teste passa uma função fabricada que levanta um número controlado de vezes, nunca
    uma chamada de rede de verdade. Na última tentativa, ou diante de erro não-repetível,
    a exceção sobe para `analisar_lote` decidir o que fazer (aqui, sempre absorver).
    """
    espera = _ESPERA_INICIAL_S
    for tentativa in range(1, _TENTATIVAS + 1):
        try:
            return chamar()
        except Exception as erro:
            if tentativa == _TENTATIVAS or not _deve_repetir(erro):
                raise
            time.sleep(espera)
            espera *= _FATOR_BACKOFF


def analisar_lote(lote: list[Reclamacao]) -> dict:
    """Chama o modelo sobre `lote` e devolve o delta `{"analises": ..., "falhas": ...}`.

    Nunca deixa exceção escapar (ver docstring do módulo — o motivo é empírico, não
    estético). Falha de transporte, depois de `_chamar_com_retry` esgotar as tentativas
    ou encontrar erro permanente, vira `Falha` cobrindo o lote inteiro, no mesmo formato
    que o desvio de conteúdo (`response.parsed is None`) já usava.
    """
    if not lote:
        return {"analises": [], "falhas": []}

    def _gerar():
        _registrar_tentativa()  # antes da chamada: quota é gasta mesmo se ela falhar
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
        _registrar_tokens(resposta)
        return resposta

    try:
        resposta = _chamar_com_retry(_gerar)
    except Exception as erro:
        return {
            "analises": [],
            "falhas": [Falha(
                ids=[r["id"] for r in lote],
                causa=str(erro) or type(erro).__name__,
                no="analisar_lote",
            )],
        }

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
