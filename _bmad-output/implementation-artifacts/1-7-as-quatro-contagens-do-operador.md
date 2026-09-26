# Story 1.7: As quatro contagens do operador

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a operador,
I want ver ao encerrar quantas reclamações entraram, saíram, falharam e quantos sinais foram derrubados,
so that eu distinga uma execução limpa de uma execução silenciosamente degradada sem ler log.

## Acceptance Criteria

**AC1 — Caminho do CSV por argumento de linha de comando (FR-1a)**

**Given** o comando invocado com o caminho de um CSV como argumento
**When** ele executa
**Then** a execução roda sobre aquele arquivo, sem caminho embutido no código
**And** invocar sem argumento encerra com mensagem de uso
**And** esta é a metade de FR-1 que o Épico 1 precisa; escrever/nomear o HTML é FR-1b, Story 2.6

**AC2 — Quatro números impressos ao encerrar (FR-2)**

**Given** uma execução concluída
**When** o comando encerra
**Then** o terminal imprime: total lidas, total analisadas, total não analisadas, total de códigos de sinal derrubados

**AC3 — Total não analisado é reclamação afetada, não evento (AD-5)**

**Given** o total não analisado
**When** ele é calculado
**Then** vale `sum(len(f["ids"]) for f in falhas)`
**And** a contagem de eventos (`len(falhas)`) também está disponível ao operador

**AC4 — Total de derrubados conta códigos distintos, não pares (AD-2)**

**Given** o total de derrubados
**When** ele é calculado
**Then** conta, por reclamação, os códigos distintos com ao menos um `Sinal` `valida=False`, somados entre todas as reclamações
**And** não conta pares reprovados nem reclamações afetadas

**AC5 — Zero análises encerra com causa nomeada (AD-13)**

**Given** uma execução em que `len(analises) == 0`
**When** ela chega ao fim do fan-out
**Then** encerra com a causa nomeada, sem escrever arquivo algum (não há arquivo nesta altura do pipeline — Épico 2)

**AC6 — API indisponível ou credencial ausente tem causa nomeada (§6 do PRD)**

**Given** a API indisponível ou sem credencial válida
**When** a execução encerra
**Then** a causa é nomeada — indisponibilidade ou credencial ausente, não mensagem genérica
**And** informa quantos eventos de falha ocorreram, para o operador situar o tamanho do problema

**AC7 — Verificação manual sobre a base de referência (fora da suíte automatizada)**

**Given** a base de referência com a API respondendo normalmente
**When** a execução termina
**Then** reporta 50 lidas, 50 analisadas, 0 não analisadas
**And** esta é verificação manual de aceitação — exige rede e crédito reais, não é rodada por `bmad-dev-auto`

**AC8 — `main.py` não importa `google.genai` diretamente (AD-7)**

**Given** o módulo `main.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai` diretamente

## Tasks / Subtasks

- [x] **Task 1 — Criar `main.py`** (AC: 1, 2, 3, 4, 5, 6, 8)
  - [x] `sys.stdout.reconfigure(encoding="utf-8")` logo no topo de `if __name__ == "__main__"` — convenção de todo entrypoint executável do repo (console do Windows não é UTF-8 por padrão)
  - [x] Ler `sys.argv`: sem argumento (ou mais de um) → mensagem de uso em `stderr`, `sys.exit(1)` (AC1)
  - [x] `estado_final = grafo.construir_grafo(caminho).invoke({})` — **`invoke({})` funciona com estado inicial vazio**, confirmado nesta sessão rodando de verdade contra um caminho inexistente (`FileNotFoundError` surge do nó `carregar`, prova que o `invoke` passa da validação inicial sem exigir todas as chaves de `Estado` — a dívida registrada em `1-1-contrato-de-estado-e-catalogo-de-sinais.md` sobre `Estado` ser `total=True` não se materializou como bloqueio na prática)
  - [x] Capturar `ValueError` (config/CSV inválidos — Stories 1.2/1.3, já nomeiam a causa sozinhas) e qualquer outra exceção que escape do `invoke` (infraestrutura não prevista) — imprimir a causa em `stderr`, `sys.exit(1)`. **Não capturar exceção dentro de `analisar_lote`** — Story 1.6 já garante que esse nó nunca levanta; o que chega aqui de exceção é de `carregar` (CSV) ou de config, ambos síncronos e já nomeados
  - [x] `_contar_codigos_derrubados(analises: list[Analise]) -> int` — para cada `Analise`, o conjunto de `codigo` distintos com `valida=False` entre seus `sinais`; soma entre todas as `Analise`. Função pura, testável com `Analise` fabricada à mão (AC4)
  - [x] Calcular as quatro contagens: `lidas = len(estado["reclamacoes"])`, `analisadas = len(estado["analises"])`, `nao_analisadas = sum(len(f["ids"]) for f in estado["falhas"])`, `derrubados = _contar_codigos_derrubados(estado["analises"])`
  - [x] Se `analisadas == 0`: imprimir causa nomeada em `stderr` — juntar as `causa` distintas de `estado["falhas"]` (não uma mensagem genérica; se todo `Falha.causa` for igual, é sinal forte de causa sistêmica, ex. credencial ausente) e `len(estado["falhas"])` eventos — `sys.exit(1)` (AC5, AC6)
  - [x] Senão, imprimir as quatro contagens em tabela alinhada por f-string, no padrão de `baseline.py`/`classificador.py` (saída de terminal é a observabilidade do sistema — `project-context.md`) — inclui também `eventos_falha` ao lado de `nao_analisadas`, para o operador ver os dois números de AD-5
  - [x] Docstring de módulo: propósito, `Rode: uv run python main.py <caminho.csv>` (linha `Rode:` obrigatória em módulo executável)
  - [x] Imports: `sys`, `plataforma.grafo`, `plataforma.estado` (só para o type hint de `Analise` em `_contar_codigos_derrubados`) — **nunca** `google.genai`, nem `plataforma.config`/`plataforma.analise` diretamente (quem os usa é `grafo.py`, já importado)

- [x] **Task 2 — Criar `tests/test_main.py`** (AC: 1, 2, 3, 4, 8)
  - [x] `_contar_codigos_derrubados`: `Analise` com 2 sinais do mesmo código, um válido um não → o grupo já viria homogêneo de `evidencia.verificar` (AD-2), mas o teste cobre a contagem em si — código conta 1 vez se `valida=False`; `Analise` com 2 códigos diferentes, ambos derrubados → conta 2; `Analise` sem sinal derrubado → conta 0; duas `Analise` cada uma com o mesmo código derrubado → soma 2 (não deduplica entre reclamações — AC4 explicitamente conta por reclamação)
  - [x] Teste de uso sem argumento: invocar a lógica de parsing de `sys.argv` (extraída como função testável, ex. `_ler_argumento(argv) -> str`) com lista vazia → levanta ou devolve sinal de erro de uso, sem chamar `grafo.construir_grafo`
  - [x] `test_somente_analise_importa_o_sdk_do_modelo` (`tests/test_analise.py`, já existe) — acrescentar `main.py` ao `pacote.glob` varrido, ou criar checagem equivalente para a raiz do projeto, confirmando que `main.py` não cita `"google"` no código-fonte (AC8)
  - [x] **Não** testar `main()` inteiro com `grafo.construir_grafo(...).invoke(...)` de verdade — chamaria `analisar_lote`, rede. Testar só as funções puras extraídas (`_contar_codigos_derrubados`, parsing de argumento) e deixar a integração ponta a ponta para a verificação manual da AC7

## Dev Notes

### O que esta story NÃO resolve — e por quê está tudo bem

**"Quantos lotes haviam concluído" (AC6) não é reconstruído com precisão de lote.** `Estado` não amarra `Analise`/`Falha` ao lote que as produziu — essa informação nunca atravessa o grafo (por desenho: cada lote escreve só em `analises`/`falhas` via redutor `add`, sem id de lote). Reportar `len(estado["falhas"])` (eventos) ao lado de `nao_analisadas` (reclamações afetadas) dá ao operador sinal suficiente do tamanho do problema sem inventar um mecanismo de rastreamento de lote que nenhuma AC pede explicitamente. Decisão por ausência de fonte — se for insuficiente na prática, é conversa de correção de curso.

**Nenhum pré-check de credencial antes de rodar.** Seria possível checar `os.environ.get("GOOGLE_API_KEY")` antes de despachar os lotes, economizando o desperdício de cada lote falhando independentemente. Não implementado: nenhuma AC/NFR pede, e o comportamento sem o pré-check já é correto — `genai.Client()` sem credencial levanta `ValueError` (confirmado nesta sessão: `"No API key was provided..."`), que `_deve_repetir` (Story 1.6) classifica corretamente como **não-transitório** — falha rápido, sem desperdiçar tentativas de retry. O pré-check economizaria só o tempo de montar `_montar_instrucao()`/`_montar_payload()` por lote, marginal.

**Story 1.6 já eliminou o cenário "execução aborta no meio".** A leitura original de AC6 ("a execução encerra... informando quantos lotes haviam concluído") presumia um mundo onde falha de infraestrutura podia interromper o `invoke()` no meio. Depois da revisão da Story 1.6, `analisar_lote` nunca deixa exceção escapar — toda falha de transporte, inclusive credencial ausente, vira `Falha` e o `invoke()` sempre roda até o fim. "A execução encerra" nesta story significa "o processo Python termina", não "o grafo aborta no meio" — e a causa nomeada vem de inspecionar `falhas`, não de capturar uma exceção que interrompeu o fan-out.

### Contrato de saída do `invoke()`

`grafo.construir_grafo(caminho).invoke({})` devolve um `dict` com as chaves que algum nó escreveu — não necessariamente todas as de `Estado` (`pontuacoes`, `agregados`, `caminho_html` nunca são escritas nesta altura do pipeline, Épico 2 as escreve). `main.py` só lê `reclamacoes`, `analises`, `falhas` — as três que `carregar`/`analisar_lote`/`_verificar_conservacao` de fato produzem.

### O que esta story NÃO faz

**Não escreve relatório.** `caminho_html` não é tocado — FR-1b é Story 2.6.
**Não pontua nem agrega.** `pontuacoes`/`agregados` seguem vazios após esta story; o operador só vê as quatro contagens brutas do Épico 1.
**Não roda a AC7 automaticamente.** É verificação manual — exige `GOOGLE_API_KEY` real e gasta crédito. Documentar o comando (`uv run python main.py docs/reclamacoes_reclameaqui.csv`) e deixar para o usuário rodar quando quiser, não simular nem inventar números.

### Estrutura de arquivos

```text
main.py                 # NOVO — CLI, as quatro contagens
tests/
  test_main.py           # NOVO
```

**Não tocar:** `plataforma/*.py` (só importar `grafo` e `estado`), `docs/`, `baseline.py`, `classificador.py`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-7** | `main.py` não importa `google.genai`, direta nem transitivamente por escrita própria (só via `grafo`, que já importa `analise`) |
| **AD-13** | `analisadas == 0` encerra com causa nomeada; não escreve arquivo (não há arquivo nesta altura) |
| **FR-1a** | Caminho do CSV por `sys.argv`, sem argumento encerra com uso |
| **FR-2** | Quatro números impressos |
| **AD-5** | `nao_analisadas` = reclamações afetadas; eventos disponíveis à parte |
| **AD-2** | `_contar_codigos_derrubados` conta código distinto por reclamação, não par |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.7] — ACs originais
- [Source: _bmad-output/implementation-artifacts/1-6-fan-out-por-lote-com-falha-absorvida.md] — por que `analisar_lote` nunca levanta, e o que isso muda para a leitura de AC6
- [Source: plataforma/grafo.py, plataforma/estado.py] — `construir_grafo`, forma de `Estado`
- [Source: project-context.md] — `sys.stdout.reconfigure`, saída em tabela alinhada, docstring com `Rode:`
- [Source: verificado nesta sessão] — `invoke({})` com estado inicial vazio funciona; `genai.Client()` sem credencial levanta `ValueError("No API key was provided...")`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-auto) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run pytest -q` → `122 passed` (baseline pré-story: 115).
- `uv run python main.py` sem argumento → mensagem de uso, `exit 1`.
- `uv run python main.py arquivo-inexistente.csv` → traceback cru vazando (achado); corrigido com `try/except` em volta do `invoke()`; depois: `"encerrado: [Errno 2] No such file or directory: ..."`, `exit 1`.
- `uv run python main.py docs/reclamacoes_reclameaqui.csv` sem credencial → acentos quebrados em stderr (achado); corrigido reconfigurando `stderr` também; depois: mensagem limpa nomeando a causa real do SDK, `exit 1`.
- Pós-revisão (Blind Hunter + Edge Case Hunter): `124 passed`. `_ler_argumento([])` corrigido (quebrava com `IndexError`); acesso ao estado movido para dentro do `try/except`; fallback morto removido; lógica de mensagem extraída para `_mensagem_zero_analises`, testável.

### Completion Notes List

- Dois achados de teste manual, ambos corrigidos antes de fechar: (1) exceção de `carregar` (CSV inválido/inexistente) vazava traceback cru do LangGraph — `main()` não tinha `try/except` em volta do `invoke()`, apesar da story já ter previsto isso na Task 1; (2) `sys.stdout.reconfigure(encoding="utf-8")` não cobre `stderr`, e `SystemExit` imprime lá — acentos das mensagens de causa (config.py/ingestao.py, em português) quebravam no console do Windows.
- Confirmado na prática que a Story 1.6 elimina "execução aborta no meio": rodando sem credencial, os 5 lotes (50 reclamações / `tamanho_lote=10`) falharam de forma independente e absorvida, produzindo uma mensagem única e limpa em vez de uma exceção interrompendo o processo no primeiro lote.
- `_contar_codigos_derrubados` soma por reclamação, não deduplica entre reclamações — testado explicitamente (mesmo código derrubado em duas `Analise` diferentes conta 2).
- AC7 (verificação manual com API real, 50/50/0) não foi executada nesta sessão — exige credencial real e gasta crédito da API. Fica para o usuário rodar: `uv run python main.py docs/reclamacoes_reclameaqui.csv` com `GOOGLE_API_KEY` válida.

### File List

| Arquivo | Tipo |
|---|---|
| `main.py` | novo |
| `tests/test_main.py` | novo |
| `tests/test_analise.py` | modificado |
