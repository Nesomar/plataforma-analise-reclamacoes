# Story 1.6: Fan-out por lote com falha absorvida

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a operador,
I want que cada lote seja uma execução de nó independente com política de repetição,
so that um lote que falha não gaste token nos que já voltaram corretos nem derrube a execução inteira.

## Acceptance Criteria

**AC1 — `carregar` emite um `Send` por lote (AD-8)**

**Given** 50 reclamações e `tamanho_lote = 10`
**When** o nó `carregar` executa
**Then** ele emite 5 `Send` para `analisar_lote`

**AC2 — Lote residual de 1 é fundido, nunca despachado sozinho (AD-17)**

**Given** 50 reclamações e `tamanho_lote = 7`
**When** o fatiamento roda
**Then** o lote residual de tamanho 1 é fundido ao anterior
**And** nenhum `Send` é emitido com um único item

**AC3 — Lote esgotado produz uma `Falha`, os demais seguem (AD-9 revisado, AD-5, NFR-5)**

**Given** um lote que esgota `_chamar_com_retry` (`plataforma/analise.py`)
**When** a exceção final é capturada dentro de `analisar_lote`
**Then** ele produz uma única `Falha` com os ids daquele lote, a causa e o nó
**And** os demais lotes seguem executando normalmente
**And** nenhuma exceção escapa de `analisar_lote` para o grafo — motivo: `add_node`/`error_handler` do LangGraph não absorve falha sob concorrência em `langgraph==1.2.10` (achado de revisão, ver Dev Agent Record e `ARCHITECTURE-SPINE.md#AD-9`)

**AC4 — Repetição é política declarada, classificando transitório de permanente (AD-9 revisado, NFR-4)**

**Given** uma falha de transporte como limite de taxa (429) ou erro de servidor (5xx)
**When** ela ocorre
**Then** `_chamar_com_retry` repete a chamada com backoff exponencial, até `_TENTATIVAS`
**And** falha permanente (401, 400, ...) não é repetida — `_deve_repetir` distingue os dois casos
**And** a repetição vive dentro de `analisar_lote` (não em `add_node` do grafo) — decisão revisada nesta story, não a intenção original

**AC5 — Conservação após o gather (AD-6)**

**Given** o gather das execuções de lote concluído
**When** o fan-out termina, antes de qualquer nó posterior
**Then** uma asserção verifica `len(reclamacoes) == len(analises) + sum(len(f["ids"]) for f in falhas)`
**And** a asserção vale sozinha nesta story — não depende de `pontuar`, que só existe no Épico 2

**AC6 — Lotes independentes, acumulação por redutor (AD-8, AD-19)**

**Given** dois lotes quaisquer em execução
**When** um deles é processado
**Then** ele não lê o resultado do outro
**And** `analises` e `falhas` acumulam pelo redutor `add`

## Tasks / Subtasks

- [x] **Task 0 — Instalar `langgraph`** (AC: todas)
  - [x] `uv add "langgraph>=1.2.10"` (versão fixada em `ARCHITECTURE-SPINE.md`); confirmar `uv.lock` atualizado
  - [x] **Verificar contra o código-fonte instalado**, não contra documentação externa: as assinaturas exatas de `Send`, `RetryPolicy`, `add_node(retry_policy=..., error_handler=...)` e a forma como `error_handler` recebe `(entrada_do_nó, error: NodeError)` foram pesquisadas nesta story via docs de terceiros (`context7`, indexado até `1.0.8` — a versão instalada aqui é `1.2.10`+, sem diff conhecido mas não conferido linha a linha). Mesma disciplina que a Story 1.2 aplicou para `GOOGLE_API_KEY`/`GEMINI_API_KEY`: ler `.venv/Lib/site-packages/langgraph/types.py` (`Send`, `RetryPolicy`) e `langgraph/graph/state.py` (`add_node`) antes de fechar a implementação, e corrigir esta story se a versão instalada divergir

- [x] **Task 1 — Criar `plataforma/grafo.py`** (AC: 1, 2, 3, 4, 5, 6)
  - [x] `_fatiar(reclamacoes: list[Reclamacao], tamanho_lote: int) -> list[list[Reclamacao]]` — função pura. Fatia em blocos de `tamanho_lote`; se o último bloco tiver exatamente 1 item, funde-o ao bloco anterior (AD-17, segunda cláusula — a primeira, faixa 2–25, já foi validada em `config.carregar()` na Story 1.2, mas isso não impede um lote residual de 1 mesmo com `tamanho_lote` dentro da faixa: `50 % 7 == 1`)
  - [x] `_despachar(reclamacoes: list[Reclamacao], tamanho_lote: int) -> list[Send]` — pura, chama `_fatiar` e devolve `[Send("analisar_lote", lote) for lote in lotes]`. **`Send` recebe a lista de `Reclamacao` diretamente como `arg`, não envolvida em dict** — `analise.analisar_lote(lote: list[Reclamacao])` já tem exatamente essa assinatura (Story 1.5), então o nó recebe o argumento sem adaptação
  - [x] `_falha_lote(lote: list[Reclamacao], error: NodeError) -> dict` — é o `error_handler` do `add_node("analisar_lote", ...)`. **A anotação de tipo `NodeError` no parâmetro não é cosmética: é assim que o LangGraph injeta o erro** (`langgraph/_internal/_runnable.py`, casa por tipo de anotação, não por posição nem por nome do parâmetro) — sem o tipo certo a injeção não acontece. `from langgraph.errors import NodeError`. Recebe o mesmo argumento que `analisar_lote` teria recebido (`failed_task.input`, confirmado em `langgraph/pregel/_algo.py` — é o lote, não o `Estado` inteiro) mais `NodeError(node, error)`. Devolve `{"falhas": [Falha(ids=[r["id"] for r in lote], causa=str(error.error), no=error.node)]}` — **nunca** levanta, nunca aborta o grafo (AC3)
  - [x] `_verificar_conservacao(estado: Estado) -> dict` — nó pequeno, roda depois de `analisar_lote` no grafo desta story. `assert len(estado["reclamacoes"]) == len(estado["analises"]) + sum(len(f["ids"]) for f in estado["falhas"])`, mensagem nomeando os três números observados (AD-6, AC5). Devolve `{}` — não escreve nada no estado, só verifica. **Nesta story a aresta vai `analisar_lote -> _verificar_conservacao -> END`**; quando o Épico 2 acrescentar `pontuar`, a aresta final muda para apontar para lá — deixar isso registrado no código como comentário, não como TODO vago
  - [x] `_carregar(caminho: str) -> Callable[[Estado], dict]` ou closure equivalente: nó que devolve `{"reclamacoes": ingestao.carregar(caminho)}` — é aqui que a Story 1.3 se conecta ao grafo
  - [x] `construir_grafo(caminho: str) -> CompiledStateGraph` — monta `StateGraph(Estado)`; `add_node("carregar", ...)`; `add_node("analisar_lote", analise.analisar_lote, retry_policy=RetryPolicy(), error_handler=_falha_lote)` (parâmetros de `RetryPolicy` nos defaults da lib — nenhuma AC ou NFR pede número específico); `add_node("_verificar_conservacao", _verificar_conservacao)`; `add_edge(START, "carregar")`; `add_conditional_edges("carregar", despachar_fn)` onde `despachar_fn(estado)` chama `_despachar(estado["reclamacoes"], config.carregar().tamanho_lote)`; `add_edge("analisar_lote", "_verificar_conservacao")`; `add_edge("_verificar_conservacao", END)`; devolve `.compile()`
  - [x] Docstring de módulo: propósito, e o porquê não-óbvio de `Send` receber a lista de `Reclamacao` crua (não um dict) — é o que faz `analisar_lote` da Story 1.5 encaixar sem adaptação
  - [x] Imports esperados: `langgraph.graph` (`StateGraph`, `START`, `END`), `langgraph.types` (`Send`, `RetryPolicy`), mais `plataforma.estado`, `plataforma.ingestao`, `plataforma.analise`, `plataforma.config` — `grafo.py` é o orquestrador, não um filtro; a regra "nenhum filtro importa outro filtro" não o restringe (a spine desenha `grafo --> ingestao`, `grafo --> analise` explicitamente)

- [x] **Task 2 — Criar `tests/test_grafo.py`** (AC: 1, 2, 3, 4, 5, 6)
  - [x] `_fatiar`: 50 itens, `tamanho_lote=10` → 5 lotes de 10 (AC1). 50 itens, `tamanho_lote=7` → lotes de 7,7,7,7,7,7,8 (o resto de 1 fundido ao 7º, virando 8) — **7 lotes, nenhum de tamanho 1** (AC2)
  - [x] `_despachar`: confirma que devolve `list[Send]` do tamanho certo, cada `Send.node == "analisar_lote"` e `Send.arg` é a lista de `Reclamacao` daquele lote (não um dict envolvendo ela)
  - [x] `_falha_lote`: constrói um objeto de erro fake (ou o `NodeError` real, se o construtor for simples o bastante para instanciar em teste) com `.node`/`.error` conhecidos, chama `_falha_lote(lote_fabricado, erro_fake)`, confere que a `Falha` devolvida carrega todos os ids do lote, a causa e o nó certos (AC3) — **sem rede, sem `genai.Client()`**
  - [x] `_verificar_conservacao`: `Estado` fabricado à mão em que a soma bate → não levanta. `Estado` fabricado em que a soma NÃO bate → `AssertionError` com mensagem nomeando os três números (AC5)
  - [x] Import sem credencial: `plataforma.grafo` importa sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` — teste próprio neste arquivo, **não** em `tests/test_import_sem_credencial.py::MODULOS` (mesmo motivo de `analise.py`: `grafo.py` arrasta o SDK transitivamente por desenho, `test_nenhum_modulo_folha_arrasta_o_sdk` reprovaria)
  - [x] `construir_grafo(caminho)`: **sem invocar** (`.invoke()` chamaria `analisar_lote` de verdade, rede). Testar por introspecção, confirmada contra `langgraph==1.2.10` instalado: `grafo_compilado.builder.nodes` é um `dict[str, StateNodeSpec]` (`langgraph/graph/_node.py`) — checar que `"carregar"`, `"analisar_lote"`, `"_verificar_conservacao"` estão presentes; `builder.nodes["analisar_lote"].retry_policy is not None` e `.error_handler_node is not None`
  - [x] Nenhum teste chama `.invoke()` no grafo completo, nem `generate_content`, nem constrói `genai.Client()`

## Dev Notes

> **⚠️ Emenda pós-implementação (2026-08-08) — leia antes das seções abaixo.** As Dev Notes originais (escritas antes de codar) descrevem `retry_policy=`/`error_handler=` no `add_node` de `analisar_lote`, seguindo AD-9 como estava escrito então. **Isso não é o que foi entregue.** Ao escrever o teste de roteamento real do `error_handler`, ficou provado por execução direta que esse mecanismo do LangGraph não absorve falha sob concorrência (`langgraph==1.2.10`, 6 configurações testadas). O usuário escolheu mover retry e absorção de falha para **dentro** de `analise.analisar_lote` (`_deve_repetir`/`_chamar_com_retry`) — `grafo.py` não declara `retry_policy` nem `error_handler`. `ARCHITECTURE-SPINE.md#AD-9` foi revisado. **A verdade final está em `## Dev Agent Record` abaixo e em `spec-1-6-fan-out-por-lote-com-falha-absorvida.md#Spec Change Log`** — as seções a seguir ficam como registro do raciocínio original, não como o que rodou.

### O desenho que faz esta story encaixar sem reabrir a Story 1.5

`Send("analisar_lote", arg)` entrega `arg` como o **input direto** do nó — não envolvido em `Estado` nem em dict. `analise.analisar_lote(lote: list[Reclamacao]) -> dict` (Story 1.5) já tem exatamente essa forma: recebe a lista crua, devolve o delta `{"analises":..., "falhas":...}`. **`Send("analisar_lote", lote)`, não `Send("analisar_lote", {"lote": lote})`.** Se você envolver o lote num dict, o nó vai receber `{"lote": [...]}` em vez da lista, e `analisar_lote` vai quebrar tentando iterar um dict como se fosse `list[Reclamacao]`.

Pela mesma razão, o `error_handler` (`_falha_lote`) recebe o **mesmo argumento que o nó com falha teria recebido** — a lista de `Reclamacao` daquele lote, não o `Estado` inteiro. É assim que `_falha_lote` sabe quais ids nomear na `Falha`, sem precisar reconstruir isso de outro lugar.

### AD-17 tem duas cláusulas, e as duas já foram implementadas — em stories diferentes

| Cláusula | Onde vive | Story |
|---|---|---|
| "piso 2 e teto 25, verificados na carga da configuração" | `config.py` | 1.2 — já feita |
| "lote residual de tamanho 1 é fundido ao anterior" | `grafo.py::_fatiar` | **1.6 — esta** |

`tamanho_lote = 7` sobre 50 linhas está **dentro** da faixa 2–25 e ainda assim produz um resto de 1 (`50 = 7×7 + 1`). A validação de faixa não pega isso — só o fatiamento pega, porque só ele sabe quantas linhas o CSV tinha. Isso já estava documentado na Story 1.2 como dívida explícita para esta story.
[Source: _bmad-output/implementation-artifacts/1-2-configuracao-validada-antes-de-qualquer-chamada-paga.md#O que esta story NÃO faz]

### `error_handler` é um nó de verdade, não um callback try/except

Pesquisa contra a documentação da lib (`context7`, indexado até `1.0.8` — projeto usa `1.2.10`+, **verificar contra o instalado antes de fechar**): `add_node` aceita `retry_policy=` e `error_handler=` como parâmetros. O runtime tenta a `retry_policy` primeiro (backoff, `max_attempts`); só depois de esgotada é que despacha para `error_handler`, passando `(entrada_original_do_nó, NodeError(node=..., error=...))`. **Não é** um `try/except` escrito à mão dentro de `analisar_lote` — é um hook do framework, registrado separadamente. `analisar_lote` (Story 1.5) continua sem nenhum laço de repetição próprio, exatamente como AD-9 exige.

**Parâmetros de `RetryPolicy`:** nenhuma AC ou NFR desta story pede um número específico de tentativas ou backoff. Usar os defaults da biblioteca (`RetryPolicy()` sem argumentos) é a decisão desta story por ausência de fonte — documentar isso no código, não silenciar.

**Por que retry cego é seguro aqui:** qualquer exceção que escape de `analisar_lote` (Story 1.5) é, por desenho, falha de **transporte** — falha de **conteúdo** (schema fora do padrão) já é absorvida dentro de `_montar_delta` e nunca levanta. `RetryPolicy()` sem filtro de exceção é seguro porque não existe caminho de conteúdo que chegue a lançar.

### Onde o CSV entra no grafo — decisão por ausência de fonte

`Estado` (Story 1.1) não tem campo para o caminho do CSV — só `reclamacoes`, `analises`, `falhas`, `pontuacoes`, `agregados`, `caminho_html`. **Decisão desta story:** `construir_grafo(caminho: str)` é uma fábrica — o caminho entra como parâmetro Python normal, capturado por closure no nó `"carregar"`, nunca como campo de `Estado`. `main.py` (Story 1.7) vai chamar `grafo.construir_grafo(caminho_do_argv).invoke({})` com estado inicial vazio. Isso significa que o grafo compilado desta story **não é reutilizável entre execuções com CSVs diferentes** sem reconstruir — aceitável, porque o SPEC já declara que a execução é manual, local, um processo por rodada (`ARCHITECTURE-SPINE.md#Deferred`: "Persistência entre execuções... cada rodada é independente").

### O nó de conservação (AD-6) é provisório na posição, não na lógica

`_verificar_conservacao` roda entre `analisar_lote` e `END` **nesta story**, porque `pontuar` (Épico 2) ainda não existe. Quando a Story 2.1 nascer, a aresta final muda de `_verificar_conservacao -> END` para `_verificar_conservacao -> pontuar`. A função em si (a asserção) não muda — só o fio que sai dela. Deixar um comentário no código apontando isso, não deixar implícito.

### O que esta story NÃO faz

**Não cria `main.py`.** `construir_grafo(caminho)` fica pronta para ser chamada, mas nada nesta story a invoca de verdade — isso é Story 1.7, que também traduz falha de infraestrutura em saída de processo com contagem de lotes concluídos (§6 do PRD).

**Não conecta a `pontuar`/`agregar`/`renderizar`.** A aresta final desta story é `END`. O grafo produzido aqui é funcional e testável isoladamente, mas só cobre o Épico 1.

**Não reimplementa retry.** Backoff, número de tentativas, jitter — tudo isso é `RetryPolicy` da lib. Nenhum `time.sleep` nem laço `for tentativa in range(...)` em código nosso.

### Testando sem rede — o mesmo problema da Story 1.5, resolvido do mesmo jeito

`construir_grafo(caminho).invoke(...)` chamaria `analisar_lote` de verdade, que chamaria `genai.Client()`, que exigiria credencial e rede. **Nenhum teste desta story invoca o grafo compilado.** Cada peça (`_fatiar`, `_despachar`, `_falha_lote`, `_verificar_conservacao`) é pura e testada isoladamente, no mesmo espírito da separação `analisar_lote`/`_montar_delta` da Story 1.5. A montagem do grafo (`construir_grafo`) é testada só por introspecção estrutural (nós presentes, `retry_policy` configurado), nunca por execução.

### Estrutura de arquivos

```text
plataforma/
  grafo.py              # NOVO — _fatiar, _despachar, _falha_lote, _verificar_conservacao, construir_grafo
tests/
  test_grafo.py           # NOVO
pyproject.toml             # UPDATE — langgraph
```

**Não criar nesta story:** `pontuacao.py`, `agregacao.py`, `relatorio.py`, `main.py`, `templates/`.

**Não tocar:** `plataforma/ingestao.py`, `plataforma/config.py`, `plataforma/evidencia.py`, `plataforma/analise.py` (só importar todos, não modificar), `docs/reclamacoes_reclameaqui.csv`, `baseline.py`, `classificador.py`.

### Bibliotecas e versões

| Item | Versão | Nesta story |
|---|---|---|
| `langgraph` | `>=1.2.10` | **sim — instalar** (Task 0) |
| `google-genai`, `pydantic` | já instalados | não, só via `plataforma.analise` |

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-6** | `_verificar_conservacao` roda após o fan-out, antes de qualquer nó posterior |
| **AD-8** | `carregar` (via `_despachar`) emite um `Send` por lote; `analises`/`falhas` acumulam por redutor `add` já declarado em `Estado` (Story 1.1) |
| **AD-9** | `retry_policy` e `error_handler` no `add_node`; nenhum laço de repetição em `analisar_lote` |
| **AD-17** | Segunda cláusula (fusão de residual) implementada em `_fatiar` |
| **AD-19** | Nenhuma chave nova de `Estado` escrita por mais de um nó |
| **NFR-4** | Repetição por falha de transporte não conta como reanálise — é a mesma chamada tentada de novo, não uma nova |
| **NFR-5** | Falha em um lote não interrompe os demais |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6] — ACs originais
- [Source: ARCHITECTURE-SPINE.md#AD-6, AD-8, AD-9, AD-17, AD-19] — invariantes centrais
- [Source: ARCHITECTURE-SPINE.md#Structural Seed] — diagrama `carregar -->|Send por lote| analisar_lote --> gather --> pontuar`
- [Source: plataforma/analise.py, plataforma/estado.py] — `analisar_lote(lote) -> dict`, `Falha`, `Estado`
- [Source: _bmad-output/implementation-artifacts/1-2-configuracao-validada-antes-de-qualquer-chamada-paga.md] — dívida de AD-17 registrada para esta story
- [Source: pesquisa via context7 nesta sessão, `langgraph` `1.0.8` indexado — projeto usa `1.2.10`+] — `Send`, `RetryPolicy`, `add_node(retry_policy=, error_handler=)`, `NodeError`; **conferir contra `.venv/Lib/site-packages/langgraph/` após `uv add`**

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-auto) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv add "langgraph>=1.2.10"` → resolveu `langgraph==1.2.10`, batendo com `ARCHITECTURE-SPINE.md`.
- Implementação inicial: `uv run pytest -q` → `105 passed` com `retry_policy=`/`error_handler=` no `add_node`, seguindo AD-9 como escrito originalmente.
- **Ao escrever o teste que faltava** (roteamento real de `error_handler` até o nó seguinte), descoberto que o mecanismo não absorve falha sob concorrência em `langgraph==1.2.10` — 6 configurações testadas diretamente (`invoke` puro, com `checkpointer`, `durability=sync/exit`, `.stream()`), todas com o mesmo resultado: handler roda, exceção original propaga e `.invoke()` levanta mesmo assim. Investigação completa no spec (`Design Notes`) e na docstring de `plataforma/analise.py`.
- Apresentei o achado e três caminhos ao usuário (mais investigação / retry dentro do nó / reportar bug upstream); **usuário escolheu retry dentro do nó**.
- Reimplementado: `retry_policy`/`error_handler` removidos de `grafo.py`; `_deve_repetir`/`_chamar_com_retry` acrescentados a `plataforma/analise.py`. `ARCHITECTURE-SPINE.md#AD-9` revisado.
- `uv run pytest -q` final → `115 passed` (baseline pré-story: 95).
- `uv run python -c "import plataforma.grafo"` sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` → sem erro.
- `construir_grafo(...)` executado de verdade sem credencial: `nodes["analisar_lote"].retry_policy is None` e `.error_handler_node is None`, confirmando o desenho novo.

### Completion Notes List

- API do LangGraph (`Send`, `RetryPolicy`, `add_node`, `NodeError`) pesquisada via `context7` (indexado até `1.0.8`) e conferida linha a linha contra o código-fonte instalado (`1.2.10` exato) — a pesquisa de docs bateu com o código para `Send`/`RetryPolicy`/assinaturas, mas **não previu** a falha de absorção sob concorrência, que só apareceu testando o comportamento real, não lendo o código-fonte de definição das classes.
- `_fatiar` tinha um bug real (achado de revisão, confirmado por execução direta): com `tamanho_lote=25` e resíduo de 1, a fusão simples produzia lote de 26, estourando o teto de AD-17. Corrigido com rebalanceamento (empresta 1 item do lote anterior em vez de somar o resíduo inteiro) quando a fusão simples estouraria o teto.
- `_verificar_conservacao` liga em `END` nesta story; comentário no código aponta que a Story 2.1 vai trocar essa aresta para `pontuar`.
- Nenhum teste invoca o grafo compilado nem chama `generate_content`/`genai.Client()`. O retry (`_chamar_com_retry`) é testado com uma função `chamar` fabricada à mão, nunca uma chamada de rede real.
- `AD-9` (`ARCHITECTURE-SPINE.md`) revisado e marcado `[REVISADO 2026-08-08]` — primeira vez nesta sessão que uma decisão de arquitetura precisou ser reaberta, não só uma lacuna de spec preenchida.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/grafo.py` | novo |
| `plataforma/analise.py` | modificado (Story 1.5, emendado aqui) |
| `tests/test_grafo.py` | novo |
| `tests/test_analise.py` | modificado |
| `pyproject.toml`, `uv.lock` | modificado |
| `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` | modificado (AD-9) |
