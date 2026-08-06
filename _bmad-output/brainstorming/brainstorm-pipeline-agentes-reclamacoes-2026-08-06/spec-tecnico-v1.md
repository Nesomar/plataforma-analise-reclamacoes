# Spec técnico — v1

Escopo: só o MUST. Batch CLI, sem front, sem banco, sem cache, sem cascata.
Stack: Python + LangGraph + `langchain-google-genai` (Google AI Studio).

---

## 1. Contrato de state

Esta é a **única** parte do v1 que não é aditiva. Errar aqui obriga reescrita quando cascata, cache e checkpoint entrarem — os três precisam saber de qual reclamação estão falando.

```python
from typing import TypedDict, Literal, Annotated
from operator import add

class Reclamacao(TypedDict):
    id: str            # estável, derivado do CSV (linha + hash do texto)
    empresa: str
    titulo: str
    texto: str
    data: str          # ISO-8601

class Analise(TypedDict):
    id: str                                          # liga de volta — obrigatório
    sentimento: Literal["positivo", "neutro", "negativo"]
    produto: str | None
    sinal_a: bool                                    # ameaça explícita
    sinal_b: list[str]                               # tipos de exposição factual
    evidencia: list[str]                             # citações literais do texto
    prazo_prometido_dias: int | None
    data_evento: str | None                          # ISO ou None

class Estado(TypedDict):
    reclamacoes: list[Reclamacao]
    analises: Annotated[list[Analise], add]          # acumula entre lotes
    scores: dict[str, int]                           # id -> score
    agregados: dict
    caminho_html: str
```

**Regra do `id`:** se o LLM devolver 19 itens para um lote de 20, o nó de análise precisa detectar e registrar qual sumiu — não pode assumir alinhamento posicional. Casar por `id`, sempre.

---

## 2. Nós do grafo

Divisão **por etapa do fluxo**. Linear no v1; o roteador condicional entra no v2 junto com a cascata.

```
carregar → analisar_lotes → pontuar → agregar → renderizar
```

| Nó | Tipo | Responsabilidade |
|---|---|---|
| `carregar` | determinístico | Lê o CSV, valida schema fixo, atribui `id` estável. Falha ruidosamente em coluna faltando. |
| `analisar_lotes` | **LLM** | Único nó que chama Gemini. Fatia em lotes de N, structured output, casa resposta por `id`. |
| `pontuar` | determinístico | Aplica as 3 parcelas + aritmética de prazo. Nenhuma chamada de rede. |
| `agregar` | determinístico | Contagens, ranking de produtos, distribuição de sentimento, fila ordenada. |
| `renderizar` | determinístico | Escreve o HTML único. |

`N` inicial: 10. Ajustar pelo limite de contexto e pela taxa de resposta incompleta, não por chute.

---

## 3. O que é LLM e o que é `if`

**LLM (só no `analisar_lotes`):**
- sentimento pelo texto
- produto mencionado em texto livre
- presença de ameaça explícita (sinal A) — **com citação**
- presença de exposição factual (sinal B) — **com citação**
- extração dos campos de prazo (`prazo_prometido_dias`, `data_evento`)

**Determinístico (todo o resto):**
- parse e validação do CSV
- comparação de datas / prazo estourado
- cálculo do score
- contagens, ranking, agregação
- montagem do HTML

Regra de bolso: o LLM **extrai**, o `if` **julga**.

---

## 4. Prompt do nó de análise — requisitos duros

1. **Structured output obrigatório.** Sem parse de texto livre.
2. **Citação obrigatória por sinal.** Todo `sinal_a` ou item de `sinal_b` marcado como verdadeiro exige pelo menos uma entrada em `evidencia` que seja **trecho literal do texto**.
3. **Glossário explícito no prompt.** Definir cada tipo de sinal B com exemplo. Categoria sem definição escrita degrada a classificação — é o item de maior impacto na acurácia.
4. **Pós-validação determinística:** se a citação não for substring do texto original, o sinal cai para `False`. O LLM não é confiável para se auditar; `in` é.

### Tipos de sinal B (v1)

| Código | Descrição |
|---|---|
| `cobranca_indevida` | Valor debitado sem contratação, sem notificação, ou contra o que foi prometido |
| `prazo_estourado` | Prazo legal ou prometido pela própria empresa já vencido |
| `registro_contraditorio` | Registro da empresa afirma um fato que o cliente contesta com protocolo/rastreio |
| `servico_nao_contratado` | Item na fatura que o cliente nega ter solicitado |
| `lei_citada` | Cliente invoca CDC, artigo, ou pede ressarcimento em dobro |

---

## 5. Score de priorização

```python
PESOS = {
    "dinheiro_do_cliente":     3,   # cobranca_indevida, servico_nao_contratado
    "dano_continuado":         2,   # cobrança recorrente (mensal)
    "registro_contraditorio":  2,
    "ameaca_explicita":        3,   # sinal A, só com citação válida
    "prazo_estourado":         1,   # +1 extra se estourado em mais de 2x
}
```

Corte do v1: **binário**, `score >= 5` entra na fila.

> ⚠️ Sabe-se que isso infla a fila (3 de 5 no corpus de teste). É aceito conscientemente no v1. A correção — níveis com prazo, no modelo de triagem — está no v2 e deve ser revisitada **antes** de calibrar o corte.

---

## 6. Saída HTML

Arquivo único, autocontido, sem servidor e sem CDN. Quatro seções:

1. **Cabeçalho** — total de reclamações, período, empresa(s).
2. **Sentimento** — distribuição, e a leitura de percepção de marca.
3. **Produtos** — ranking por volume. *Anotar no próprio HTML que volume ≠ gravidade: o produto mais reclamado costuma ser o mais vendido.*
4. **Fila de prioridade** — ordenada por score, cada item mostrando **a citação que sustentou a classificação**. A evidência é parte do relatório, não metadado.

Gráficos: SVG inline gerado em Python ou matplotlib embutido como base64. Nada externo.

---

## 7. Fora do v1 — não implementar

Cascata Flash→Pro · cache · guard-rails · loop de crítica · checkpoint · front/upload · níveis de criticidade · reclassificação por tempo.

O único ponto de extensão que o v1 precisa deixar pronto é o **contrato de state** acima.

---

## 8. Verificação mínima

Um `test_pipeline.py` com asserts sobre o corpus de 5 reclamações da sessão:

- `carregar` produz 5 `id`s únicos e estáveis entre execuções
- toda `evidencia` retornada é substring do texto original da respectiva reclamação
- `pontuar` coloca as reclamações 2, 3 e 4 na fila (veredito humano da sessão é o gabarito)
- `analisar_lotes` com resposta incompleta simulada não perde nem troca `id`

O terceiro é o que realmente importa: é o único teste que sabe se o sistema concorda com um humano.
