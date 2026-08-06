# Revisão de Tecnologia — ARCHITECTURE-SPINE

**Alvo:** `_bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md`
**Lente:** toda decisão comprometida foi pesquisada na web / checada contra a realidade, ou foi afirmada de memória?
**Data da verificação:** 2026-08-06 — todas as consultas feitas na sessão, contra PyPI e código-fonte no GitHub.
**Veredito:** **Aprovada com bloqueios.** As versões estão todas corretas — nenhuma foi inventada. O que falha é a camada acima: **três decisões descrevem APIs que não se comportam como a spine afirma**, e uma delas (AD-10) falha em silêncio exatamente no risco que ela existe para prevenir.

---

## 1. Stack — versões conferidas contra o PyPI

Consultadas em `https://pypi.org/pypi/<pkg>/json`, campo `info.version` (= release mais recente).

| Pacote | Spine diz | PyPI hoje | requires-python | Veredito |
| --- | --- | --- | --- | --- |
| `langgraph` | 1.2.10 | **1.2.10** | `>=3.10` | ✅ confirmado, é o latest |
| `google-genai` | ≥2.17.0 | **2.17.0** | `>=3.10` | ✅ confirmado, é o latest |
| `jinja2` | 3.1.6 | **3.1.6** | `>=3.7` | ✅ confirmado, é o latest |
| `python-dotenv` | ≥1.2.2 | **1.2.2** | `>=3.10` | ✅ confirmado, é o latest |
| `pytest` | 9.1.1 | **9.1.1** | `>=3.10` | ✅ confirmado, é o latest |
| Python | ≥3.11 | — | — | ✅ satisfaz o piso de todos (o mais alto é 3.10) |

**Compatibilidade de Python:** `>=3.11` do `pyproject.toml` é compatível com os cinco. Nenhum tem teto que exclua 3.11+. Não há conflito.

**Todas as tecnologias existem, são mantidas e servem ao uso que a spine lhes dá.** Nenhum pacote abandonado, nenhum nome inventado. `jinja2 3.1.6` é de 2025-03-05 — parece velho, mas é de fato o release corrente da Pallets, não um pin desatualizado. Sem achado.

**Modelo:** a spine não fixa modelo (delega a `config.py`). `classificador.py` usa `gemini-3.6-flash` — confirmado como ID real e GA (lançado 2026-07-21, disponível na Gemini API). Sem achado.

---

## 2. API do LangGraph — o que foi confirmado e o que não bate

Verificado contra `langchain-ai/langgraph@main` (`libs/langgraph/langgraph/graph/state.py`, `types.py`, `pregel/_executor.py`, `_internal/_retry.py`) e a doc corrente em `docs.langchain.com/oss/python/langgraph/`.

### Confirmado — a spine está certa

| Item da spine | Status |
| --- | --- |
| `Send` existe, é o mecanismo de fan-out map-reduce | ✅ `from langgraph.types import Send` — caminho correto na 1.x. `langgraph.constants` está **deprecado desde v1.0** (`LangGraphDeprecatedSinceV10`); a spine não usa o caminho velho |
| `RetryPolicy` existe e é aceita em `add_node` | ✅ `from langgraph.types import RetryPolicy`; assinatura real: `add_node(..., retry_policy: RetryPolicy \| Sequence[RetryPolicy] \| None = None, ...)`. O parâmetro **é** `retry_policy` (não `retry`) |
| `Annotated[list[T], operator.add]` como redutor | ✅ padrão documentado e corrente. AD-5 e AD-8 estão sobre terreno firme |
| `StateGraph` · `compile` | ✅ inalterados |

Nenhum nome citado pela spine foi renomeado ou depreciado. Nesse eixo a spine **não** está descrevendo API antiga.

### Não confirmado — três lugares onde a spine descreve comportamento que a API não tem

Ver achados **C-3**, **H-1** e **H-2** abaixo.

---

## 3. Jinja2 — `select_autoescape` e o default de autoescape

Verificado contra `pallets/jinja@main`, `src/jinja2/utils.py`, e a doc de API em `jinja.palletsprojects.com/en/stable/api/`.

- ✅ **A spine está certa no fato central:** `Environment(autoescape=...)` tem **default `False`**. Autoescape NÃO é padrão no Jinja2. AD-10 acerta ao exigir o parâmetro explícito.
- ✅ `select_autoescape` existe, assinatura corrente:
  ```python
  select_autoescape(enabled_extensions=('html','htm','xml'), disabled_extensions=(),
                    default_for_string=True, default=False)
  ```
- ❌ **Mas o mecanismo de casamento derruba o uso que a spine faz dele.** Ver achado **C-1**.

---

## 4. Contradições com o projeto existente

Lidos: `pyproject.toml`, `uv.lock`, `baseline.py`, `classificador.py`, `docs/reclamacoes_reclameaqui.csv`.

**Consistente com o que já existe:**
- Leitura do CSV — `utf-8-sig` + separador `;`: bate com `baseline.ler()` e com o BOM real do arquivo. ✅
- `Data` no CSV é `09/06/2026` → DD/MM/AAAA confirmado; convenção de datas da spine está correta. ✅
- `ID_Reclamacao` único: `baseline.autoteste()` já assere isso. ✅
- `tamanho_lote` piso 2 / teto 25 (AD-17): `classificador.TAMANHO_LOTE = 10` cai na faixa. ✅
- Configuração via `python-dotenv`: já é como `classificador.classifica()` carrega a chave. ✅
- AD-1 revogar `ameaca_explicita: bool` + `evidencia_ameaca` (o formato de `classificador.py`) é mudança **deliberada e declarada**, não contradição. ✅

**Inconsistente:** ver achados **C-2**, **M-1** e **M-4**.

---

## Achados

### 🔴 C-1 — CRÍTICO — `select_autoescape(["html"])` deixa o autoescape **desligado** para `relatorio.html.j2`

**Onde:** AD-10, e `templates/relatorio.html.j2` no Structural Seed.

A spine especifica, com ênfase:

> `autoescape=select_autoescape(["html"])` **explícito** — o Jinja2 não liga autoescape por padrão.

O raciocínio está certo. A implementação não funciona. Fonte verbatim de `jinja2/utils.py`:

```python
enabled_patterns = tuple(f".{x.lstrip('.').lower()}" for x in enabled_extensions)

def autoescape(template_name: str | None) -> bool:
    if template_name is None:
        return default_for_string
    template_name = template_name.lower()
    if template_name.endswith(enabled_patterns):   # <-- endswith, não "contém"
        return True
    ...
    return default                                  # default = False
```

O casamento é `endswith(".html")`. O template da spine chama-se **`relatorio.html.j2`** — termina em `.j2`. Não casa. Cai em `default=False`. **Autoescape desligado.**

O que AD-10 diz que previne: *"escape de HTML esquecido num campo que carrega texto livre de consumidor"*. O `Descricao` do CSV é exatamente isso — texto livre de consumidor brasileiro, que num relatório real contém `<`, `&`, aspas. Seguindo a spine ao pé da letra, o implementador escreve a linha que parece a defesa e não tem defesa nenhuma, e não há teste natural que pegue: a base de exemplo do projeto não tem HTML nas descrições. Falha silenciosa, exatamente o padrão que AD-11 é escrita para evitar em outro eixo.

**Correções, em ordem de preguiça:**
1. `Environment(autoescape=True)` — há **um** template e ele é HTML. `select_autoescape` resolve o problema de escolher por extensão, e este projeto não tem escolha para fazer. Uma palavra, zero armadilha.
2. Se quiser manter `select_autoescape`: `select_autoescape(["html", "j2"])` ou `select_autoescape(default=True)`.
3. Renomear o template para `relatorio.html` (perde o sinal de que é template).

A opção 1 é a que se recomenda, e AD-10 deveria dizer `autoescape=True` em vez de `select_autoescape`, porque a ressalva *"o Jinja2 não liga autoescape por padrão"* continua valendo e a regra fica inquebrável.

---

### 🔴 C-2 — CRÍTICO — AD-16 manda o `titulo` ao modelo; `classificador.py` o exclui de propósito, e a comparação com a baseline depende disso

**Onde:** AD-16 — *"o payload enviado ao modelo carrega `id`, `titulo` e `texto`."*

`classificador.py`, no docstring do módulo (linhas 3-6):

> *"Diferença deliberada em relação a baseline.py: o modelo vê **apenas o texto livre** da reclamação, nunca o título. O título desta base é canônico (18 valores fixos) e entrega a resposta; base real não tem isso. Ganhar sem o título é ganhar de verdade."*

E o payload real, linha 81:

```python
entrada = [{"id": r["ID_Reclamacao"], "texto": r["Descricao"]} for r in reclamacoes]
```

`baseline.py` classifica **exclusivamente por match exato de `Titulo`** contra `CATEGORIAS_DINHEIRO`. Mandar `titulo` ao modelo entrega ao LLM o gabarito da baseline. O F1 do pipeline sobe, M-1 passa, e o número deixa de significar qualquer coisa — o modelo não estará extraindo, estará lendo a resposta.

AD-16 é escrita com o raciocínio certo (*"o que não é enviado não pode ser inferido"*) e aplica-o à `empresa`. Aplica-o de menos: o campo que realmente contamina é o `titulo`, e ele foi **incluído**. A spine não registra em lugar nenhum que está revertendo uma decisão documentada do projeto — o que sugere que o `titulo` entrou por omissão, não por escolha.

**Correção:** payload = `id` + `texto`, alinhado a `classificador.py`. Se o `titulo` for realmente desejado, AD-16 precisa dizer explicitamente que reverte a decisão de `classificador.py` e explicar por que M-1 continua interpretável — o ônus é dela, não do implementador.

---

### 🔴 C-3 — CRÍTICO — `RetryPolicy` sozinha não produz `Falha`; retry esgotado **aborta o grafo**

**Onde:** AD-9 (*"`RetryPolicy` no `add_node` ... O código do nó não tem laço de repetição"*) contra AD-5 (*"Uma execução de lote esgotada produz **uma** `Falha` com os ids daquele lote"*) e AD-13.

As duas não podem ser verdadeiras ao mesmo tempo com o que AD-9 especifica. Comportamento real do LangGraph: quando `max_attempts` se esgota, a exceção **propaga** e a execução do grafo termina com erro. Nada é escrito no estado. Não existe `Falha`, não existe `analises` parcial, não existe relatório degradado — existe traceback. AD-5, AD-6, AD-13, FR-2, FR-14, NFR-5 e NFR-6 dependem todos de um caminho que a spine não especificou.

A peça que falta **existe e está disponível na versão fixada** — é `error_handler=`, adicionado em `add_node` na **langgraph 1.2** (confirmado na assinatura real: `error_handler: StateNode[Any, ContextT] | None = None`). Ele roda depois de esgotados os retries, recebe um `NodeError` e devolve um `Command` que atualiza o estado:

```python
from langgraph.errors import NodeError
from langgraph.types import Command, RetryPolicy

def falha_do_lote(state, error: NodeError) -> Command:
    return Command(update={"falhas": [{"ids": [...], "causa": str(error.error), "no": "analisar_lote"}]})

builder.add_node("analisar_lote", analisar_lote,
                 retry_policy=RetryPolicy(...), error_handler=falha_do_lote)
```

Que o pin em 1.2.10 seja exatamente a versão que traz `error_handler` é uma coincidência feliz — mas a spine não o nomeia, e `grafo.py` no Structural Seed lista só `StateGraph · Send · RetryPolicy · compile`. Quem implementar ao pé da letra escreve um grafo que morre no primeiro lote ruim.

**Correção:** AD-9 precisa nomear `error_handler` como o mecanismo que converte esgotamento em `Falha`, e o inventário de `grafo.py` precisa incluí-lo. Alternativa mais preguiçosa e igualmente válida: `try/except` dentro de `analisar_lote` devolvendo o delta de `Falha` — não é "laço de repetição", não viola AD-9, e dispensa `error_handler`. Escolha uma e escreva-a.

---

### 🟠 H-1 — ALTO — um nó não pode "emitir um `Send`"; `Send` sai de aresta condicional

**Onde:** AD-8 — *"`carregar` emite um `Send` por lote para `analisar_lote`"* — e o Structural Seed (`A[carregar] -->|Send por lote| B1`).

A API corrente não permite que um nó devolva `Send` no seu update de estado. `Send` sai de uma função de roteamento passada a `add_conditional_edges` (doc corrente, verbatim):

```python
def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

graph.add_conditional_edges("node_a", continue_to_jokes)
```

A alternativa é `Command(goto=[Send(...)])` a partir do nó, que não aparece na doc de map-reduce. O inventário de `grafo.py` no Structural Seed omite `add_conditional_edges` — sinal de que a spine descreve o fan-out por intuição, não por leitura da API.

**Correção:** AD-8 deve dizer que `carregar` devolve o estado e uma **função de aresta condicional** emite a lista de `Send` — e `grafo.py` ganha `add_conditional_edges` no inventário. A distinção não é cosmética: o lugar onde o lote é fatiado muda, e com ele quem sabe os ids de cada lote (que AD-5 exige para montar a `Falha`).

---

### 🟠 H-2 — ALTO — "concorrência do fan-out, padrão 1" não existe como botão, e o único que existe é ignorado no modo síncrono

**Onde:** AD-9 — *"Concorrência do fan-out é configurável, **padrão 1**"* — e "Deferred: Concorrência maior que 1. Botão já exposto por AD-9."

Não há parâmetro de concorrência em `StateGraph`, `add_node`, `compile` ou `RetryPolicy`. O único mecanismo é `max_concurrency`, e ele tem **duas** propriedades que a spine não registra:

1. **Vive no topo do `RunnableConfig`, no `invoke`** — não em `configurable`, não no `compile`. Fonte, `pregel/_executor.py`:
   ```python
   if max_concurrency := config.get("max_concurrency"):
       self.semaphore = asyncio.Semaphore(max_concurrency)
   ```
   (A doc pública em `use-graph-api` mostra `{"configurable": {"max_concurrency": 10}}` — divergente da fonte. Siga a fonte: chave de topo.)

2. **Só o executor assíncrono o honra.** O trecho acima está em `AsyncBackgroundExecutor`. O `BackgroundExecutor` **síncrono** não lê `max_concurrency` nem aplica semáforo — delega tudo a `get_executor_for_config(config)`. A spine não menciona `async` em lugar nenhum; AD-12 descreve funções puras síncronas, `classificador.py` é síncrono. Num pipeline síncrono, **`max_concurrency` não faz nada** e o fan-out roda com a concorrência do thread pool, não com 1.

E o default do LangGraph não é 1 — é ilimitado. "Padrão 1" só acontece se alguém o escrever.

Isso não é acadêmico: NFR-1 (tempo), o custo por chamada paga e a Q-8 do PRD ("cronometrar com o cache desligado") dependem do botão existir. A spine defere a decisão para um botão que, do jeito descrito, não está ligado a nada.

**Correção:** AD-9 deve nomear `max_concurrency` no `RunnableConfig` do `invoke`, e declarar se o grafo é `invoke` ou `ainvoke` — porque só no segundo o botão funciona. Se o v1 é síncrono, a maneira honesta de garantir "padrão 1" é fatiar em um `Send` só ou aceitar que a concorrência é a do pool e dizer isso.

---

### 🟠 H-3 — ALTO — `RetryPolicy` default repete quase tudo, inclusive 4xx permanente

**Onde:** AD-9 — *"`RetryPolicy` no `add_node` de `analisar_lote` **cobre falha de transporte**."*

O default de `retry_on` é `default_retry_on`, e ele não se limita a transporte. Fonte (`_internal/_retry.py`): retorna `True` para `ConnectionError`, para `httpx`/`requests` com 5xx, e **`True` como fallback para qualquer exceção não listada**. A lista de exclusão é só de bugs de programação (`ValueError`, `TypeError`, `RuntimeError`, `OSError`, etc.).

`google-genai` levanta `google.genai.errors.APIError` e subclasses (`ClientError` para 4xx, `ServerError` para 5xx), que herdam de `Exception` — não de `httpx.HTTPStatusError`, não de `ConnectionError`. Consequência: **um 400 de payload malformado, um 403 de chave inválida ou um 404 de modelo inexistente serão repetidos 3 vezes**, com backoff, gastando tempo e — no caso do 400 — token pago, para falhar de qualquer jeito. AD-17 existe justamente para "encerrar antes de qualquer chamada paga"; o default de `RetryPolicy` desfaz parte disso no outro extremo.

**Correção:** `retry_on` explícito. Ex.: `retry_on=(ConnectionError, TimeoutError, google.genai.errors.ServerError)` — mas atenção a AD-7, que proíbe qualquer módulo além de `analise.py` de importar `google.genai`. Se `grafo.py` monta o `RetryPolicy`, a tupla de exceções tem de vir de `analise.py`, ou a política de retry passa a ser construída lá. Essa tensão AD-7 × AD-9 não está resolvida na spine.

---

### 🟡 M-1 — MÉDIO — `pydantic` é dependência real e não está declarada em lugar nenhum

`classificador.py` faz `from pydantic import BaseModel` (linha 19). `pyproject.toml` declara apenas `google-genai` e `python-dotenv`. `uv.lock` confirma: `pydantic` só entra transitivamente. E `langgraph 1.2.10` exige `pydantic>=2.7.4` (confirmado nos metadados do PyPI).

A Stack da spine não lista `pydantic`, embora o `response_schema` do google-genai — que é como o projeto obtém saída estruturada — dependa dele. Importar uma dependência transitiva é como se quebra numa atualização de `google-genai` sem aviso.

**Correção:** declarar `pydantic>=2.7.4` no `pyproject.toml` e listá-lo na Stack.

---

### 🟡 M-2 — MÉDIO — `langgraph` traz 5+ pacotes transitivos para um grafo de 5 nós

Metadados confirmados no PyPI para 1.2.10: `langchain-core<2,>=1.4.7`, `langgraph-checkpoint<5,>=4.1.0`, `langgraph-prebuilt<1.2,>=1.1.0`, `langgraph-sdk<0.5,>=0.4.2`, `pydantic>=2.7.4`, `xxhash>=3.5.0`.

A spine defere checkpoint persistido, roteamento condicional e loop de crítica. O que sobra é: carregar → fan-out de N lotes → pontuar → agregar → renderizar, tudo sequencial e determinístico exceto o fan-out. Isso é um `ThreadPoolExecutor.map` com uma lista de resultados.

Não é um erro — é uma decisão que a spine nunca justifica. O que `langgraph` traz de concreto aqui é `RetryPolicy` + `error_handler` (a fault tolerance de AD-9/AD-5) e a estrutura para os deferrals. Isso pode muito bem valer os seis pacotes; mas registrado, não presumido. Note que H-2 tira do lado da coluna "vantagens" a concorrência configurável, que é o que boa parte das pessoas presume estar comprando.

**Correção:** um parágrafo em `Deferred` ou numa AD dizendo por que `langgraph` e não `concurrent.futures` — e o que se perderia. Se a resposta for "pelos deferrals do roadmap", isso já é resposta.

---

### 🟡 M-3 — MÉDIO — dois estilos de pin sem regra declarada

`langgraph 1.2.10`, `jinja2 3.1.6` e `pytest 9.1.1` são exatos; `google-genai ≥2.17.0` e `python-dotenv ≥1.2.2` são pisos. Nenhuma convenção explica a diferença. Como `uv.lock` já existe e trava tudo, o pin exato na Stack agrega pouco e envelhece rápido — daqui a três meses a spine estará "errada" sobre `pytest` sem que nada tenha quebrado.

**Correção:** uma linha em Consistency Conventions: piso na Stack, travamento no `uv.lock`. Ou, se o pin exato é deliberado (como o `MODELO` pinado em `classificador.py`, que traz a razão escrita ao lado), escreva a razão.

---

### 🟡 M-4 — MÉDIO — o console do Windows não é UTF-8, e `main.py` não sabe disso

`baseline.py` (linha 99) e `classificador.py` (linha 203) fazem ambos:

```python
sys.stdout.reconfigure(encoding="utf-8")  # console do Windows não é UTF-8 por padrão
```

A spine especifica `main.py` como CLI e AD-13 exige encerrar "com a causa nomeada" — texto em português, com acento, impresso no console. Em `cp1252` isso levanta `UnicodeEncodeError` e a mensagem de erro que o operador precisa ler vira um traceback sobre encoding. O projeto roda em Windows 11.

Já é padrão estabelecido em dois arquivos preexistentes. A spine não o herda.

**Correção:** uma linha em Consistency Conventions, ou no inventário de `main.py`.

---

### 🔵 L-1 — BAIXO — AD-6 fala em "gather" que não é nó

AD-6: *"verificado em asserção **após o gather** e antes de `pontuar`"*. O Structural Seed desenha `G((gather))`, mas `grafo.py` não o lista e o LangGraph não tem nó de gather — o fan-in é implícito na fronteira do superstep. Na prática a asserção mora no início de `pontuar`, o que é o mesmo lugar e funciona.

Vale saber que `add_node(..., defer=True)` existe (confirmado na assinatura) e serve exatamente para adiar um nó até todas as tarefas pendentes terminarem. Aqui os ramos têm o mesmo comprimento, então não é necessário — mas se C-3 for resolvido com `error_handler` roteando para outro lugar, os comprimentos deixam de ser iguais e `defer=True` em `pontuar` passa a importar.

---

### 🔵 L-2 — BAIXO — o inventário de `grafo.py` está incompleto

`# StateGraph · Send · RetryPolicy · compile` omite `add_conditional_edges` (H-1), `error_handler` (C-3), `START`/`END`, e `max_concurrency` no invoke (H-2). Como o Structural Seed é lido como checklist por quem implementa, a omissão propaga os achados acima. Corrigir junto com eles.

---

## Contagem por severidade

| Severidade | Contagem | IDs |
| --- | --- | --- |
| 🔴 Crítico | **3** | C-1, C-2, C-3 |
| 🟠 Alto | **3** | H-1, H-2, H-3 |
| 🟡 Médio | **4** | M-1, M-2, M-3, M-4 |
| 🔵 Baixo | **2** | L-1, L-2 |
| **Total** | **12** | |

---

## Conclusão da lente

**Onde a spine se sai bem:** as seis versões da Stack estão corretas e são as correntes no PyPI — nenhuma inventada, nenhuma desatualizada, e a compatibilidade com `>=3.11` fecha. Os nomes da API do LangGraph (`Send`, `RetryPolicy`, `retry_policy=` em `add_node`, `Annotated[list, operator.add]`) existem, não foram renomeados, e o caminho de import correto (`langgraph.types`, não o `langgraph.constants` deprecado) é o que a spine implica. O fato central sobre o Jinja2 — autoescape não é padrão — está certo. As convenções de CSV, data e id batem com o arquivo real e com `baseline.py`.

**Onde ela falha:** em três lugares a spine acerta o *nome* da API e erra o *comportamento*. `select_autoescape(["html"])` não casa `.html.j2` (C-1). `RetryPolicy` sozinha não vira `Falha`, ela mata o grafo (C-3). "Concorrência padrão 1" não é um botão que exista, e o botão que existe é ignorado no modo síncrono que a spine implica (H-2). Isso é a assinatura de decisão escrita de memória: a forma da API está certa porque é memorável, a semântica está errada porque exige leitura da fonte.

Os dois achados mais caros são os silenciosos. C-1 produz um relatório que parece escapado e não está, e a base de exemplo do projeto não tem HTML nas descrições para revelá-lo. C-2 produz um F1 que passa M-1 sem que o modelo tenha extraído nada — e ambos passam por revisão porque *a linha certa está lá*.

**Recomendação:** C-1, C-2 e C-3 antes de qualquer implementação. H-1 e H-2 antes de escrever `grafo.py`. O resto pode entrar na próxima revisão da spine.
