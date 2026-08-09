---
title: 'Story 1.7 — As quatro contagens do operador'
type: 'feature'
created: '2026-08-08'
status: 'done'
baseline_revision: '63ddb85'
final_revision: '3ccfa23'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/1-7-as-quatro-contagens-do-operador.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
warnings: []
---

<intent-contract>

## Intent

**Problem:** O grafo (Story 1.6) roda mas nada o invoca de verdade, e nada mostra ao operador se a execução foi limpa ou degradada — só um `Estado` em memória, sem entrypoint.

**Approach:** Criar `main.py`: lê o caminho do CSV de `sys.argv`, invoca `grafo.construir_grafo(caminho).invoke({})`, calcula e imprime quatro números (lidas, analisadas, não analisadas, códigos derrubados). `analisadas == 0` encerra com causa nomeada, inspecionando `falhas`. Como a Story 1.6 já garante que `analisar_lote` nunca deixa exceção escapar, o `invoke()` sempre roda até o fim — "a execução encerra" nesta story é o processo Python terminando após ler o resultado, não uma exceção interrompendo o grafo no meio.

## Boundaries & Constraints

**Always:**
- Tudo em português: módulo, função, mensagem.
- `sys.stdout.reconfigure(encoding="utf-8")` no entrypoint executável.
- `_contar_codigos_derrubados` conta código distinto **por reclamação**, soma entre reclamações — não deduplica globalmente (AD-2/CM-2).
- `nao_analisadas = sum(len(f["ids"]) for f in falhas)`; `len(falhas)` (eventos) reportado à parte.

**Block If:**
- Alguma AC exigir escrever relatório HTML ou pontuar/agregar — Épico 2.
- A suíte existente falhar por motivo não previsto.

**Never:**
- Não importar `google.genai` em `main.py`.
- Não testar `main()` inteiro com `invoke()` real — chamaria o modelo, rede. Só funções puras extraídas são testadas.
- Não tocar `plataforma/*.py`, `docs/`, `baseline.py`, `classificador.py`.
- Não simular/inventar a verificação manual da AC7 (exige rede e crédito reais).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Sem argumento | `sys.argv` só com o nome do script | — | Mensagem de uso, `exit(1)` |
| Execução normal | `Estado` com `analises`/`falhas` preenchidos | 4 números impressos | Nenhum erro esperado |
| Zero análises | `len(analises) == 0` | — | Causa nomeada (de `falhas`), `exit(1)` |
| Contagem de derrubados | `Analise` com códigos derrubados repetidos entre reclamações | Soma por reclamação, não deduplicada | — |

</intent-contract>

## Code Map

- `main.py` — **NOVO**. CLI, `_contar_codigos_derrubados`, `_ler_argumento`.
- `plataforma/grafo.py` — `construir_grafo(caminho).invoke({})`, confirmado nesta sessão que aceita estado inicial vazio.
- `plataforma/estado.py` — `Analise`, `Falha`, tipos usados em `main.py`.
- `tests/test_analise.py` — `test_somente_analise_importa_o_sdk_do_modelo` estendido para cobrir `main.py`.
- `tests/test_main.py` — **NOVO**.

## Tasks & Acceptance

**Execution:**
- [x] `main.py` — `_ler_argumento(argv) -> str` (uso incorreto → `SystemExit`/mensagem); `_contar_codigos_derrubados(analises) -> int`; `main()` monta `estado = grafo.construir_grafo(caminho).invoke({})` dentro de `try/except Exception`, calcula as 4 contagens, imprime tabela alinhada; `analisadas == 0` → causa nomeada de `falhas`, `exit(1)`. `sys.stderr.reconfigure(encoding="utf-8")` além de `stdout` — achado ao testar na mão: `SystemExit` imprime em stderr, sem reconfigurar os acentos quebravam no console do Windows.
- [x] `tests/test_main.py` — `_contar_codigos_derrubados` (código repetido entre reclamações soma, não dedup; múltiplos códigos por reclamação; zero derrubados); `_ler_argumento` sem argumento, com argumento extra, caso válido.
- [x] `tests/test_analise.py` — `test_somente_analise_importa_o_sdk_do_modelo` estendido para varrer `main.py` na raiz do projeto.

**Acceptance Criteria:**
- Given comando sem argumento, when executa, then mensagem de uso e `exit(1)` (AC1).
- Given execução concluída, when o comando encerra, then imprime lidas/analisadas/não-analisadas/derrubados (AC2).
- Given `falhas` preenchidas, when a contagem roda, then `nao_analisadas` soma `ids`, `len(falhas)` disponível à parte (AC3).
- Given `Analise`s com códigos derrubados repetidos entre reclamações, when `_contar_codigos_derrubados` roda, then soma por reclamação, não deduplica (AC4).
- Given `analises` vazio, when o comando processa o resultado, then encerra com causa nomeada, `exit(1)` (AC5, AC6).
- Given `main.py` inspecionado, when se procura por `google.genai`, then não há import (AC8).

## Spec Change Log

## Review Triage Log

### 2026-08-08 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 6: (high 0, medium 2, low 4)
- defer: 0
- reject: 10: (high 0, medium 0, low 10)
- addressed_findings:
  - `[medium]` `[patch]` `_ler_argumento([])` levantava `IndexError` em vez de `SystemExit` de uso — `argv[0]` acessado sem checar lista vazia. Corrigido com fallback `"main.py"`.
  - `[medium]` `[patch]` Acesso a `estado["reclamacoes"]`/`["analises"]`/`["falhas"]` ficava fora do `try/except` — um `Estado` incompleto vazaria `KeyError` cru. Movido para dentro do bloco protegido.
  - `[low]` `[patch]` Fallback morto `or ["nenhuma reclamação lida"]` — inalcançável dado AD-6 (`_verificar_conservacao`) e a guarda de CSV vazio em `ingestao.carregar`. Removido; lógica extraída para `_mensagem_zero_analises`, testável e documentando por que a lista nunca vem vazia.
  - `[low]` `[patch]` Comentário do `except` dizia que só cobria "infraestrutura não prevista", mas o próprio Auto Run Result já documentava `FileNotFoundError` de CSV inexistente sendo pego ali — o caso mais comum, não imprevisto. Comentário corrigido.
  - `[low]` `[patch]` Docstring do módulo lia como se a garantia da Story 1.6 dispensasse o `try/except`, quando na verdade é o `try/except` que protege o módulo se essa garantia regredir. Reescrita.
  - `[low]` `[patch]` Ramo `analisadas == 0` (montagem da mensagem de causa) não tinha teste, apesar de ser lógica pura — extraído para `_mensagem_zero_analises`, testado.

## Design Notes

**Por que "quantos lotes concluíram" não é reconstruído com precisão:** `Estado` não amarra `Analise`/`Falha` a um id de lote — nunca atravessou o grafo por desenho. Reportar `len(falhas)` (eventos) ao lado de `nao_analisadas` (reclamações) dá sinal suficiente sem inventar rastreamento de lote que nenhuma AC pede.

**Por que não há mais "execução aborta no meio":** a Story 1.6 garante que `analisar_lote` nunca levanta — toda falha de transporte, inclusive credencial ausente, vira `Falha`. `invoke()` sempre completa. A causa de uma execução ruim vem de inspecionar `falhas`, não de capturar uma exceção que interrompeu o fan-out.

## Verification

**Commands:**
- `uv run pytest` — expected: suíte inteira verde, incluindo `test_main.py` novo (baseline 115 testes).
- `uv run python main.py` (sem argumento) — expected: mensagem de uso, código de saída 1.

**Manual checks (AC7, fora da suíte):**
- `uv run python main.py docs/reclamacoes_reclameaqui.csv` com `GOOGLE_API_KEY` real — expected: 50 lidas, 50 analisadas, 0 não analisadas.

## Auto Run Result

**O que foi implementado:** `main.py` com `_ler_argumento`, `_contar_codigos_derrubados`, `main()`. `estado = grafo.construir_grafo(caminho).invoke({})` dentro de `try/except Exception`, convertendo qualquer exceção (config inválida, CSV inválido, infraestrutura) em `SystemExit` com a mensagem original, sem traceback cru. `analisadas == 0` reporta causa(s) únicas de `falhas` e conta de eventos.

**Testado na mão, além da suíte:**
- `uv run python main.py` (sem argumento) → mensagem de uso, `exit 1`.
- `uv run python main.py arquivo-inexistente.csv` → **achado**: vazava traceback cru do LangGraph (`FileNotFoundError` de `ingestao.carregar` propagando sem captura). Corrigido com `try/except Exception` em volta do `invoke()`.
- `uv run python main.py docs/reclamacoes_reclameaqui.csv` sem `GOOGLE_API_KEY` → **achado**: acentos quebrados no console (`reclama��o`) — `sys.stdout.reconfigure` não cobre `stderr`, e `SystemExit` imprime lá. Corrigido reconfigurando os dois. Depois do fix: `"encerrado: nenhuma reclamação analisada — 5 evento(s) de falha, causa(s): No API key was provided..."`, `exit 1` — prova que os 5 lotes (50/10) falharam independentemente e de forma limpa, cada um sem desperdiçar retry (erro de credencial não é classificado como transitório por `_deve_repetir`, Story 1.6).

**Arquivos tocados:**

| Arquivo | Tipo | Descrição |
|---|---|---|
| `main.py` | novo | CLI, quatro contagens |
| `tests/test_main.py` | novo | 7 testes |
| `tests/test_analise.py` | modificado | varredura de AD-7 estendida para `main.py` |

**Verificação (pós-revisão):**
- `uv run pytest -q` → `122 passed` pós-implementação → `124 passed` pós-revisão (baseline: 115).
- Três invocações manuais reais (sem argumento, CSV inexistente, CSV real sem credencial) — reconfirmadas depois dos patches, saída limpa e código de saída correto em todas.

**Achados da revisão.** Blind Hunter + Edge Case Hunter em paralelo. 16 achados únicos: 6 patches (2 medium — `_ler_argumento([])` quebrando com `IndexError`, acesso a `estado[...]` fora do `try/except`; 4 low — fallback morto, dois comentários imprecisos, teste faltante no ramo de zero análises), 10 rejeitados (mensagem crua de `FileNotFoundError` já é suficientemente diagnóstica, prefixo "uv run python" é convenção deliberada do projeto, dependência de invariante entre módulos já estabelecida em stories anteriores, etc.).

**Riscos residuais / decisões por ausência de fonte:**
- "Quantos lotes concluíram" (AC6) reportado como `len(falhas)` eventos, não contagem exata de lotes — `Estado` não amarra `Analise`/`Falha` a um lote, decisão já registrada na story.
- AC7 (verificação manual com API real) não foi executada — exige `GOOGLE_API_KEY` real e gasta crédito; documentada para o usuário rodar quando quiser.
- Sem pré-check de credencial antes de despachar — decisão registrada na story (falha rápida já acontece via `_deve_repetir` classificando `ValueError` de credencial como não-transitório).
