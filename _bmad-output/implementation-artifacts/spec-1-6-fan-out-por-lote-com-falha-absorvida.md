---
title: 'Story 1.6 — Fan-out por lote com falha absorvida'
type: 'feature'
created: '2026-08-08'
status: 'done'
baseline_revision: '4874b95'
final_revision: 'b5c8888'
review_loop_iteration: 1
followup_review_recommended: true
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/1-6-fan-out-por-lote-com-falha-absorvida.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
warnings: ['oversized']
---

<intent-contract>

## Intent

**Problem:** `analisar_lote` (Story 1.5) existe mas não está conectada a nada — nada fatia a base em lotes, nada despacha em paralelo, nada absorve a falha de um lote sem derrubar os demais.

**Approach:** Criar `plataforma/grafo.py` com `construir_grafo(caminho) -> CompiledStateGraph`: nó `carregar` lê o CSV (Story 1.3); `_despachar` fatia (fundindo resíduo de 1, AD-17) e emite um `Send` por lote direto para `analisar_lote`, sem envolver em dict — a assinatura de `analisar_lote(lote) -> dict` (Story 1.5) já encaixa; `_verificar_conservacao` roda após o fan-out.

**Emenda de 2026-08-08 (achado de revisão, AD-9 revisado):** `retry_policy`/`error_handler` do `add_node` foram abandonados — investigação empírica mostrou que `error_handler` não absorve falha sob concorrência em `langgraph==1.2.10` (ver Design Notes). O retry com backoff e a absorção de falha de transporte migraram para dentro de `analise.analisar_lote` (Story 1.5, módulo emendado nesta story). `grafo.py` não declara nenhum dos dois no `add_node`.

## Boundaries & Constraints

**Always:**
- Tudo em português: módulo, função, comentário.
- `Send(node, arg)` recebe a lista de `Reclamacao` crua como `arg`, nunca envolvida em dict — é o que faz `analisar_lote(lote)` (Story 1.5) encaixar sem adaptação.
- Todas as peças (`_fatiar`, `_despachar`, `_verificar_conservacao`) são funções puras, testáveis sem invocar o grafo.
- `construir_grafo` é fábrica: recebe `caminho` como parâmetro Python, nunca como campo de `Estado` (que não tem esse campo).
- `analisar_lote` (em `plataforma/analise.py`) nunca deixa exceção escapar — falha de transporte, depois de `_chamar_com_retry` esgotar, vira `Falha` como retorno normal.

**Block If:**
- Alguma AC exigir `main.py`, `pontuar`, `agregar` ou qualquer nó do Épico 2 — fora de escopo.
- A suíte existente falhar por motivo não previsto nas tasks.

**Never:**
- Não invocar o grafo compilado (`.invoke()`) em nenhum teste — chamaria `analisar_lote` de verdade, rede.
- Não tocar `plataforma/ingestao.py`, `plataforma/config.py`, `plataforma/evidencia.py`, `docs/reclamacoes_reclameaqui.csv`, `baseline.py`, `classificador.py`.
- Não criar `main.py`, `pontuacao.py`, `agregacao.py`, `relatorio.py`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fatiamento exato | 50 itens, `tamanho_lote=10` | 5 lotes de 10 | — |
| Resíduo de 1 | 50 itens, `tamanho_lote=7` | 7 lotes (6×7 + 1×8), nenhum de tamanho 1 | — |
| Resíduo no teto | 51 itens, `tamanho_lote=25` | 3 lotes, nenhum >25 nem ==1 (rebalanceado) | — |
| Despacho | `_despachar` sobre N lotes | `list[Send]`, `arg` = lista crua de `Reclamacao` | — |
| Falha de transporte transitória | `_chamar_com_retry` com erro 5xx/429 | Repete até `_TENTATIVAS`, devolve resultado se recuperar | — |
| Falha de transporte permanente | `_chamar_com_retry` com erro 401/400 | Levanta na 1ª tentativa, sem repetir | Propaga para `analisar_lote` absorver como `Falha` |
| Conservação ok | `Estado` onde a soma bate | Não levanta | — |
| Conservação quebrada | `Estado` onde a soma não bate | — | `AssertionError` nomeando os três números |

</intent-contract>

## Code Map

- `plataforma/grafo.py` — **NOVO**. `_fatiar`, `_despachar`, `_verificar_conservacao`, `_carregar`, `construir_grafo`.
- `plataforma/analise.py` — **emendado nesta story**: `analisar_lote(lote) -> dict` ganhou `_chamar_com_retry`/`_deve_repetir` (retry com backoff e absorção de falha de transporte, movidos de `grafo.py` depois do achado de que `error_handler` do LangGraph não funciona sob concorrência).
- `plataforma/ingestao.py` — `carregar(caminho) -> list[Reclamacao]`, chamado dentro do nó `carregar` do grafo.
- `plataforma/config.py` — `carregar().tamanho_lote`, lido dentro de `_despachar`.
- `.venv/Lib/site-packages/langgraph/types.py:664` (`Send`), `:416` (`RetryPolicy`) — confirmados nesta sessão.
- `.venv/Lib/site-packages/langgraph/graph/state.py` (`add_node` com `retry_policy=`/`error_handler=`), `.venv/Lib/site-packages/langgraph/graph/_node.py:85` (`StateNodeSpec`, usado para introspecção em teste).
- `.venv/Lib/site-packages/langgraph/errors.py:149` (`NodeError`), `.venv/Lib/site-packages/langgraph/pregel/_algo.py:1236` (confirma que o handler recebe `failed_task.input`, o mesmo argumento do nó que falhou).
- `pyproject.toml` — `langgraph>=1.2.10` já instalado nesta sessão (`Task 0`).
- `tests/test_grafo.py` — **NOVO**.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`/`uv.lock` — `langgraph>=1.2.10` instalado (`langgraph==1.2.10` resolvido).
- [x] `plataforma/grafo.py` — `_fatiar(reclamacoes, tamanho_lote) -> list[list[Reclamacao]]` (funde resíduo de 1 ao lote anterior, rebalanceando se estourar o teto); `_despachar(reclamacoes, tamanho_lote) -> list[Send]` (`Send("analisar_lote", lote)`, lote cru); `_verificar_conservacao(estado: Estado) -> dict` (assert de conservação, devolve `{}`); `construir_grafo(caminho) -> CompiledStateGraph` monta `StateGraph(Estado)`, registra os nós, liga `START -> carregar -(conditional)-> Send*N -> analisar_lote -> _verificar_conservacao -> END`, **sem** `retry_policy`/`error_handler` (ver emenda abaixo).
- [x] `plataforma/analise.py` (emendado) — `_deve_repetir(erro) -> bool` classifica transitório vs. permanente; `_chamar_com_retry(chamar) -> T` repete com backoff exponencial; `analisar_lote` nunca deixa exceção escapar.
- [x] `tests/test_grafo.py` — cobrir a I/O Matrix inteira com dados fabricados à mão; introspecção estrutural de `construir_grafo` sem invocar (inclusive que `analisar_lote` **não** tem `retry_policy`/`error_handler`); teste de import sem credencial.
- [x] `tests/test_analise.py` (emendado) — `_deve_repetir` parametrizado sobre erros transitórios/permanentes; `_chamar_com_retry` repete até sucesso, não repete erro permanente, esgota e levanta a última exceção.

**Acceptance Criteria:**
- Given 50 reclamações e `tamanho_lote=10`, when `_despachar` roda, then devolve 5 `Send` para `"analisar_lote"` (AD-8).
- Given 50 reclamações e `tamanho_lote=7`, when `_fatiar` roda, then nenhum lote tem tamanho 1 (AD-17).
- Given 51 reclamações e `tamanho_lote=25` (o teto), when `_fatiar` roda, then nenhum lote excede 25 nem tem tamanho 1 (AD-17, achado de revisão).
- Given uma falha de transporte que esgota `_chamar_com_retry`, when `analisar_lote` roda, then devolve uma `Falha` com todos os ids do lote, a causa e o nó, sem levantar (AD-9 revisado, AD-5).
- Given um `Estado` cuja soma não bate, when `_verificar_conservacao` roda, then levanta `AssertionError` nomeando os números observados (AD-6).
- Given o grafo compilado, when inspecionado, then o nó `"analisar_lote"` **não** tem `retry_policy` nem `error_handler_node` (a responsabilidade migrou para dentro do nó).
- Given a suíte, when roda sem `GOOGLE_API_KEY`/`GEMINI_API_KEY`, then `import plataforma.grafo` funciona.

## Spec Change Log

### 2026-08-08 — AD-9 revisado: retry migra de `add_node` para dentro de `analisar_lote`

- **Gatilho:** ao escrever o teste que faltava (achado de revisão "ausência de teste que exercite o roteamento real de `error_handler`"), a implementação desse teste revelou que `error_handler` do LangGraph **não absorve falha sob concorrência** em `langgraph==1.2.10` — testado em 6 configurações, todas com o mesmo resultado (handler roda, exceção propaga mesmo assim). Investigação completa registrada nas Dev Notes abaixo.
- **O que foi emendado:** `Boundaries & Constraints` (`Always`/`Never`) e o `Approach` do `<intent-contract>` — a menção a `retry_policy=`/`error_handler=` no `add_node` foi substituída pela descrição do desenho novo (retry dentro de `analisar_lote`). `ARCHITECTURE-SPINE.md#AD-9` também foi revisado, marcado `[REVISADO 2026-08-08]`.
- **Estado ruim evitado:** sem a correção, uma falha de transporte num único lote derrubaria a execução inteira — o oposto do que AC3 promete ("os demais lotes seguem executando normalmente") — apesar da suíte passar 100%, porque nenhum teste anterior forçava esse caminho.
- **Por que não ficou só bloqueado:** apresentei três saídas ao usuário (mais investigação, retry manual dentro do nó, dispatch sequencial sem `Send`); o usuário escolheu retry manual dentro do nó. Não é inferência unilateral — é decisão do usuário registrada nesta sessão.
- **KEEP:** `_fatiar`, `_despachar`, `_verificar_conservacao` e a montagem estrutural de `construir_grafo` — nada disso mudou de forma, só o `add_node` de `analisar_lote` perdeu os dois kwargs. `analise._montar_delta`, `_montar_payload`, `_montar_instrucao` (Story 1.5) — intocados, só ganharam vizinhos novos (`_deve_repetir`, `_chamar_com_retry`) no mesmo módulo.

## Review Triage Log

## Review Triage Log

### 2026-08-08 — Review pass (bloqueio encontrado e resolvido nesta mesma sessão — ver Spec Change Log)

- intent_gap: 0
- bad_spec: 0
- patch: 5: (high 1, medium 1, low 3)
- defer: 0
- reject: 8: (high 0, medium 0, low 8)
- addressed_findings:
  - `[high]` `[patch]` `_fatiar` produzia lote de 26 com `tamanho_lote=25` (teto AD-17 estourado) — reproduzido diretamente (`_fatiar(51 itens, 25) == [25, 26]`). Corrigido: quando a fusão simples estouraria o teto, empresta um item do lote anterior em vez de somar o resíduo inteiro. `[25, 24, 2]` depois do fix, nenhum lote >25 nem ==1.
  - `[medium]` `[patch]` Docstring de `_falha_lote` afirmava que a injeção de `NodeError` casa só por tipo — falso, confirmado em `langgraph/_internal/_runnable.py`: casa por **nome do parâmetro (`error`) e tipo juntos**. Renomear o parâmetro quebraria a injeção silenciosamente (vira `None`). Docstring corrigida, comentário de alerta acrescentado.
  - `[low]` `[patch]` `causa=str(error.error)` podia ficar vazia para exceção sem mensagem (`ConnectionError()`) — fallback para `type(error.error).__name__` acrescentado.
  - `[low]` `[patch]` Testes de introspecção usavam o caminho real do CSV sem motivo funcional — trocado por placeholder, já que `construir_grafo` não abre o arquivo enquanto não invocado.
  - `[low]` `[patch]` Ausência de teste que exercite o roteamento real de `error_handler` — ao escrever esse teste, descoberto o achado abaixo (não é mais "ausência de teste", é bloqueio).
- **BLOQUEIO DESCOBERTO DURANTE A REVISÃO, NÃO LISTADO ACIMA:** ver seção "Investigação: error_handler não absorve falha sob concorrência" nas Dev Notes da story. `error_handler` roda mas a exceção original ainda propaga e `.invoke()` levanta quando há **mais de uma task no mesmo step** (fan-out via `Send`, ou mesmo duas arestas estáticas de `START`) — testado em 5 configurações diferentes (`invoke` puro, com `checkpointer`, `durability=sync/exit`, `.stream()`), todas com o mesmo resultado. Isso é exatamente o caso de uso desta story (AC1 pede 5 `Send`). Sem resolver isso, AC3/AC5/AC6 não são verdadeiras na execução real, só na introspecção estrutural — apesar da suíte estar 100% verde, porque nenhum teste força esse caminho (é o próprio "ausência de teste" acima que, ao ser corrigido, revelou o problema).

## Design Notes

### BLOQUEIO (RESOLVIDO) — `error_handler` não absorve falha sob concorrência (investigação empírica desta revisão)

Ao tentar escrever o teste que faltava (roteamento real de `error_handler` até o nó seguinte), a suposição de que "o `error_handler` roda e a execução segue normalmente" (documentada no `<intent-contract>` e nas Dev Notes originais, baseada em pesquisa de documentação de terceiros) **não se sustentou contra o comportamento real do pacote instalado.**

**O que foi testado, com `langgraph==1.2.10` instalado, sem mock nenhum:**

1. Um `StateGraph` com **um único nó**, sem fan-out (`START -> "falha" -> END`, uma só task por step): `error_handler` roda (confirmado por `print`) **e** `.invoke()` devolve o estado atualizado, sem levantar. Este é o caso que o exemplo da documentação mostra, e é o único que funciona.
2. O mesmo grafo com **duas arestas estáticas de `START`** (`START -> "a"` e `START -> "b"`, duas tasks no mesmo step, `"b"` levanta): `error_handler` de `"b"` roda (`print` confirma) **mas `.invoke()` levanta a exceção original mesmo assim.**
3. Fan-out via `Send` (`add_conditional_edges(START, despachar)` emitindo `Send` para 3 itens, um deles levanta): **mesmo resultado do item 2** — handler roda, exceção propaga.
4. Repetido o item 3 com `checkpointer=InMemorySaver()` e `thread_id` — mesmo resultado.
5. Repetido com `durability="sync"` e `durability="exit"` — mesmo resultado (`"sync"` ainda produz um `AttributeError` interno diferente: `'SyncPregelLoop' object has no attribute '_put_checkpoint_fut'`).
6. Trocado `.invoke()` por `.stream(..., stream_mode="values")`, consumindo os chunks manualmentre — mesmo resultado: um chunk inicial aparece, depois a exceção original propaga do gerador.

**Conclusão:** em todas as configurações com mais de uma task concorrente no mesmo step — que é a definição do fan-out que esta story existe para implementar — `error_handler` executa (o efeito colateral dele acontece) mas **não impede a exceção original de abortar a execução**. Isso contradiz diretamente AC3 ("os demais lotes seguem executando normalmente") e AD-9 ("error_handler é obrigatório... sem ele, retry esgotado propaga exceção e aborta o grafo inteiro" — a leitura implícita de AD-9 é que **com** ele isso não aconteceria, o que não bateu com o teste).

**Resolvido nesta mesma sessão.** Três caminhos foram levantados e apresentados ao usuário: (1) mais investigação do LangGraph, sem garantia de prazo; (2) mover a absorção de falha para **dentro** de `analisar_lote`, reabrindo AD-9; (3) reportar como bug upstream. **O usuário escolheu o caminho 2.** `AD-9` foi revisado (`ARCHITECTURE-SPINE.md`, marcado `[REVISADO 2026-08-08]`): `analise.analisar_lote` (Story 1.5) ganhou `_deve_repetir`/`_chamar_com_retry` — retry com backoff exponencial, classificando erro transitório (5xx, 429) de permanente (401, 400, etc.), nunca deixando exceção escapar. `grafo.py` não declara `retry_policy`/`error_handler` no `add_node` de `analisar_lote` — ficariam inertes, o nó nunca levanta. Testado: `_fatiar` e `_despachar` intocados; `_deve_repetir`/`_chamar_com_retry` cobertos em `tests/test_analise.py` sem tocar o SDK (função `chamar` injetada, fabricada à mão).

**O que ficou implementado e correto:** `_fatiar` (incluindo o fix do teto), `_despachar`, `_verificar_conservacao`, a montagem estrutural do grafo (`construir_grafo`), e agora também o retry/absorção de falha real dentro de `analisar_lote` — a promessa central desta story (AC3/AC5/AC6) está provada por teste de unidade da lógica de retry, não mais só por introspecção estrutural do grafo.

**Por que `Send` recebe a lista crua:** `analise.analisar_lote(lote: list[Reclamacao]) -> dict` (Story 1.5) já tem a forma exata que um nó LangGraph recebe como input. `Send("analisar_lote", lote)` — não `Send("analisar_lote", {"lote": lote})`. Confirmado no exemplo do docstring de `Send` no pacote instalado.

**`error_handler` é nó de verdade, injeção por nome + tipo (histórico — mecanismo abandonado nesta story):** confirmado em `langgraph/_internal/_runnable.py` (`KWARGS_CONFIG_KEYS`) — o parâmetro precisava se chamar **exatamente `error`** e ser anotado `NodeError`. Confirmado em `langgraph/pregel/_algo.py:1236` que o handler recebia `failed_task.input` — o mesmo argumento que o nó falho teria recebido (o lote), não o `Estado` inteiro. **Mas, como o bloqueio acima documenta, receber esse argumento corretamente não bastava — a exceção original ainda propagava sob concorrência.** `_falha_lote` e o registro de `error_handler` foram removidos de `grafo.py`; este parágrafo fica só como registro do que foi investigado.

**Onde o CSV entra:** `Estado` não tem campo para o caminho. `construir_grafo(caminho)` é fábrica; o caminho vira closure do nó `carregar`. `main.py` (Story 1.7) chama `construir_grafo(caminho).invoke({})`.

**O nó de conservação é provisório na posição:** `analisar_lote -> _verificar_conservacao -> END` nesta story; quando `pontuar` nascer (Story 2.1), a aresta final muda para `_verificar_conservacao -> pontuar`.

## Verification

**Commands:**
- `uv run pytest` — expected: suíte inteira verde, incluindo `test_grafo.py` novo (baseline 95 testes antes desta story).
- `uv run python -c "import plataforma.grafo"` sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` — expected: sem erro.

**Manual checks (if no CLI):**
- Ler `construir_grafo` e confirmar visualmente que nenhum `.invoke()` aparece em `grafo.py` fora de exemplo/comentário — quem invoca é `main.py`, Story 1.7.

## Auto Run Result

**O que foi implementado:** `plataforma/grafo.py` com `_fatiar`, `_despachar`, `_verificar_conservacao` (todas puras) e `construir_grafo(caminho) -> CompiledStateGraph` (fábrica). `plataforma/analise.py` (Story 1.5, emendado aqui) ganhou `_deve_repetir`/`_chamar_com_retry`: retry com backoff exponencial dentro do próprio nó, classificando falha transitória (5xx, 429) de permanente (401, 400, ...), nunca deixando exceção escapar de `analisar_lote`.

**Por que o desenho mudou no meio da revisão:** a implementação original usava `retry_policy=`/`error_handler=` no `add_node`, como a arquitetura original de AD-9 mandava. Ao escrever o teste que faltava (roteamento real do `error_handler`), a suíte revelou que esse mecanismo não absorve falha sob concorrência em `langgraph==1.2.10` — testado em 6 configurações. Apresentei o achado e três caminhos ao usuário; o usuário escolheu mover a absorção para dentro do nó. `ARCHITECTURE-SPINE.md#AD-9` foi revisado para refletir a decisão. Ver `Spec Change Log` para o registro completo.

**Arquivos tocados:**

| Arquivo | Tipo | Descrição |
|---|---|---|
| `plataforma/grafo.py` | novo | `_fatiar` (com fix de teto), `_despachar`, `_verificar_conservacao`, `construir_grafo` — sem `retry_policy`/`error_handler` |
| `plataforma/analise.py` | modificado | `_deve_repetir`, `_chamar_com_retry` acrescentados; `analisar_lote` nunca levanta |
| `tests/test_grafo.py` | novo | 11 testes: I/O Matrix + introspecção estrutural (inclusive que `analisar_lote` **não** tem retry/handler) + import sem credencial |
| `tests/test_analise.py` | modificado | +11 testes: `_deve_repetir` parametrizado, `_chamar_com_retry` (sucesso após repetir, erro permanente não repete, esgota e levanta) |
| `pyproject.toml`, `uv.lock` | modificado | `langgraph>=1.2.10` (resolvido `langgraph==1.2.10`) |
| `ARCHITECTURE-SPINE.md` | modificado | AD-9 revisado, `[REVISADO 2026-08-08]` |

**Verificação:**
- `uv run pytest -q` → `115 passed` (baseline antes desta story: 95).
- `uv run python -c "import plataforma.grafo"` sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` → sem erro.
- `construir_grafo(...)` executado de verdade sem credencial: `nodes["analisar_lote"].retry_policy is None` e `.error_handler_node is None`, confirmando o desenho novo.

**Achados da revisão.** Blind Hunter + Edge Case Hunter em paralelo. 1 achado **crítico de viabilidade arquitetural** (`error_handler` não funciona sob concorrência — não é um "patch", é uma revisão de AD-9 com decisão do usuário), 1 bug de alta severidade confirmado por execução direta (`_fatiar` estourando o teto de 25), 3 patches menores (docstring errada sobre injeção de `NodeError`, `causa` vazia sem fallback, caminho de CSV real usado sem necessidade em teste), 8 rejeitados (a maioria protegida por invariantes já validados em stories anteriores — `config.py` rejeita `tamanho_lote` fora de `[2,25]`, `ingestao.py` rejeita CSV vazio).

**Riscos residuais / decisões por ausência de fonte:**
- `_TENTATIVAS=3`, `_ESPERA_INICIAL_S=0.5`, `_FATOR_BACKOFF=2.0` — nenhuma AC/NFR pede números específicos; espelha os defaults que `RetryPolicy()` da lib usaria.
- `_deve_repetir` trata qualquer exceção fora de `ServerError`/`ClientError`/`ConnectionError`/`TimeoutError`/`OSError` como permanente (não repete) — decisão conservadora: repetir erro desconhecido às cegas é mais arriscado que falhar rápido.
- A investigação do `error_handler` ficou registrada em código (`plataforma/analise.py`, docstring de módulo) e neste spec, não como teste de regressão contra o LangGraph em si — testar comportamento de biblioteca externa não é convenção do projeto.
