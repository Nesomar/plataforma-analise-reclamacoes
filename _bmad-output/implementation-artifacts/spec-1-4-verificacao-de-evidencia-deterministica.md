---
title: 'Story 1.4 — Verificação de evidência determinística'
type: 'feature'
created: '2026-08-08'
status: 'in-review'
baseline_revision: '905c888'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/1-4-verificacao-de-evidencia-deterministica.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
warnings: []
---

<intent-contract>

## Intent

**Problem:** O modelo pode alucinar uma citação que sustenta um sinal de risco. Nada hoje confirma, sem consultar o modelo de novo, que a citação existe de fato no texto original antes de o sinal virar pontuação.

**Approach:** Criar `plataforma/evidencia.py` com `verificar(sinais: list[Sinal], texto: str) -> list[Sinal]`: recalcula `valida` por comparação de substring exata e piso de cinco palavras, agrupado por `codigo` — se qualquer citação de um código falha, todo `Sinal` daquele código sai `valida=False`, inclusive os que passariam sozinhos (AD-2). Função pura, sem rede.

## Boundaries & Constraints

**Always:**
- Tudo em português: módulo, função, comentário.
- Checagem individual = substring exata (`in`) **e** `len(citacao.split()) >= 5`, as duas no mesmo lugar.
- `valida` final é decidida por **grupo de `codigo`**, não por `Sinal` isolado — um código só fica válido se todas as suas citações passarem.
- `evidencia.py` não importa `google.genai`, direta nem transitivamente, nem `plataforma.catalogo`.
- Função pura: devolve nova lista, não muta os `Sinal` recebidos.

**Block If:**
- Alguma AC exigir integração com `analise.py` ou `grafo.py` — isso é Story 1.5, não esta.
- A suíte existente falhar por motivo não previsto nas tasks.

**Never:**
- Não integrar com `analise.py` — só a função pura e a suíte.
- Não validar `codigo` contra a lista de `catalogo.py` — `evidencia.py` não conhece o catálogo, só agrupa pelo valor que já está em cada `Sinal`.
- Não tocar `plataforma/ingestao.py`, `plataforma/config.py`, `docs/reclamacoes_reclameaqui.csv`.
- Não acrescentar `evidencia` ao `parametrize` de módulos-folha em `test_contrato.py` — mesmo caso de `ingestao` na Story 1.3, importa `estado` por desenho.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Citação válida | Substring exata, ≥5 palavras | `valida=True` | Nenhum erro esperado |
| Citação fabricada | Não é substring do texto | `valida=False` | Nenhum erro esperado |
| Par do mesmo código, um falso | 2 `Sinal` mesmo `codigo`: um válido, um fabricado | **Ambos** `valida=False` (AD-2) | Nenhum erro esperado |
| Citação curta | 4 palavras, substring válida | `valida=False` | Nenhum erro esperado |
| Citação vazia | `citacao=""` | `valida=False` | Nenhum erro esperado |

</intent-contract>

## Code Map

- `plataforma/evidencia.py` — **NOVO**. `verificar(sinais, texto) -> list[Sinal]`.
- `plataforma/estado.py` — fonte de `Sinal`; `evidencia` importa de lá (aresta já desenhada em `ARCHITECTURE-SPINE.md`).
- `plataforma/ingestao.py` — padrão de módulo a seguir: docstring de propósito, comentário cita fonte (AD-2, AD-1).
- `tests/test_evidencia.py` — **NOVO**.
- `tests/test_import_sem_credencial.py:6` — `MODULOS`; acrescentar `"plataforma.evidencia"`.

## Tasks & Acceptance

**Execution:**
- [x] `plataforma/evidencia.py` — criar `verificar(sinais: list[Sinal], texto: str) -> list[Sinal]`: checagem individual (substring + `len(citacao.split()) >= 5`); agrupar por `codigo`, `valida` final de todo `Sinal` do grupo é `True` só se todas as citações do grupo passaram individualmente (AD-2); devolver nova lista, mesma ordem de entrada.
- [x] `tests/test_evidencia.py` — citação válida; citação fabricada; **par do mesmo código com uma citação fabricada (AD-2, o teste central)**; citação de 4 palavras; citação de 5 palavras (limite); citação vazia; caso com `Analise` fabricada citando `ameaca_explicita`/`dano_continuado`/`registro_contraditorio` com citação falsa (CM-2).
- [x] `tests/test_import_sem_credencial.py` — acrescentar `"plataforma.evidencia"` a `MODULOS`.

**Acceptance Criteria:**
- Given um `Sinal` com citação substring exata e ≥5 palavras, when `verificar()` roda, then `valida=True` (AD-1).
- Given um `Sinal` cuja citação não é substring, when `verificar()` roda, then todo `Sinal` do mesmo `codigo` fica `valida=False`, inclusive pares que passariam sozinhos (AD-2).
- Given um `Sinal` com citação de 4 palavras substring válida, when `verificar()` roda, then `valida=False` (FR-6, AD-1).
- Given um `Sinal` com `citacao=""`, when `verificar()` roda, then `valida=False`, apesar de string vazia ser substring de qualquer texto.
- Given `Analise` fabricada com citação falsa injetada, when a suíte roda, then a verificação derruba o código correspondente, sem nenhuma chamada de rede (AD-12, CM-2).
- Given `plataforma/evidencia.py` inspecionado, when se procura por `google.genai`, then não há import, direto nem transitivo (AD-7) — coberto por `test_import_sem_credencial.py`.

## Spec Change Log

## Review Triage Log

### 2026-08-08 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 3: (high 0, medium 0, low 3)
- defer: 2: (high 0, medium 0, low 2)
- reject: 7: (high 0, medium 0, low 7)
- addressed_findings:
  - `[low]` `[patch]` Nenhum teste cobria grupo do mesmo `codigo` intercalado por `Sinal` de outro código — acrescentado `test_grupo_intercalado_com_outro_codigo_ainda_derruba_junto`. A primeira versão do teste usava uma citação de `catalogo.py` que não é substring de `TEXTO` deste arquivo — corrigido durante a aplicação do patch, pego pela própria suíte (`1 failed` antes da correção).
  - `[low]` `[patch]` Nenhum teste cobria grupo de tamanho 3+ — acrescentado `test_grupo_de_tres_com_uma_fabricada_derruba_as_tres`, generalizando o caso central de AD-2 além do par.
  - `[low]` `[patch]` `verificar([])` sem teste — acrescentado `test_lista_vazia_de_sinais_devolve_lista_vazia`.

**O núcleo é o agrupamento por `codigo` (AD-2), não a comparação de substring.** Checagem por `Sinal` isolado passa em 5 das 6 ACs e falha silenciosamente na que testa AD-2 — o caso que esta story existe para cobrir. Calcular a checagem individual primeiro, depois decidir `valida` por grupo: um código só fica válido se **todas** as suas citações passaram.

**Por que `evidencia` não entra no teste de módulos-folha:** mesma decisão já tomada para `ingestao` na Story 1.3 — `test_modulos_folha_so_importam_o_que_a_story_permite` é só para módulos que não importam nada de `plataforma/`, e `evidencia.py` importa `Sinal` de `estado` por desenho.

## Verification

**Commands:**
- `uv run pytest` — expected: suíte inteira verde, incluindo `test_evidencia.py` novo e a lista `MODULOS` estendida.
- `uv run python -c "import plataforma.evidencia, sys; assert not [m for m in sys.modules if m.startswith('google')]"` — expected: sem saída, sem erro.

**Manual checks (if no CLI):**
- Chamar `verificar([{"codigo": "x", "citacao": "a b c", "valida": False}], "texto qualquer")` num REPL e conferir que a citação curta sai `valida=False`.

## Auto Run Result

**O que foi implementado:** `plataforma/evidencia.py` com `verificar(sinais, texto) -> list[Sinal]`, função pura. A checagem individual (`_passa_checagem_individual`) confere substring exata via `in` **e** `len(citacao.split()) >= 5` no mesmo lugar; citação vazia reprova pelo piso de palavras sem caso especial. O agrupamento por `codigo` (AD-2) roda em duas passadas: primeiro calcula a checagem individual de cada `Sinal` na ordem de entrada, depois reduz por `codigo` com `and` acumulado (`codigo_valido.get(codigo, True) and passou`) — qualquer citação reprovada de um código derruba `valida` de todo `Sinal` daquele código, inclusive os que passariam sozinhos. A lista de saída é reconstruída (`Sinal(...)` novo por item) preservando a ordem de entrada, sem mutar os dicts recebidos.

`tests/test_evidencia.py` (novo, 9 testes) cobre: citação válida (6 palavras); citação fabricada; o par do mesmo código — um válido, um fabricado — com a asserção de que **ambos** saem `valida=False` (teste central de AD-2); citação de 4 palavras (reprova); citação de exatamente 5 palavras (passa, limite inclusivo); citação vazia (reprova apesar de `"" in texto` ser `True`); `Analise` fabricada citando `ameaca_explicita`, `dano_continuado` (citação falsa injetada) e `registro_contraditorio`, provando que só o código com citação fabricada cai (CM-2); mais dois testes de contrato da função pura — não mutar a lista recebida e preservar ordem de saída.

`tests/test_import_sem_credencial.py` — `"plataforma.evidencia"` acrescentado a `MODULOS`; os dois testes existentes (`test_importa_sem_google_api_key`, `test_nenhum_modulo_folha_arrasta_o_sdk`) passam a cobrir o módulo novo sem alteração de lógica.

**Arquivos tocados:**

| Arquivo | Tipo | Descrição |
|---|---|---|
| `plataforma/evidencia.py` | novo | `verificar(sinais, texto) -> list[Sinal]`, checagem individual + agrupamento por código (AD-2) |
| `tests/test_evidencia.py` | novo | 9 testes: AC1-AC5, contrato de função pura (não muta, preserva ordem) |
| `tests/test_import_sem_credencial.py` | update | `"plataforma.evidencia"` em `MODULOS` |

**Verificação (pós-revisão):**
- `uv run pytest -q` → `81 passed` pós-implementação → `84 passed` pós-revisão (baseline antes desta story: 72).
- `uv run python -c "import plataforma.evidencia, sys; assert not [m for m in sys.modules if m.startswith('google')]"` → sem saída, sem erro (exit 0).

**Achados da revisão.** Blind Hunter + Edge Case Hunter em paralelo, sem contexto prévio. 12 achados únicos: 3 patches aplicados (todos low — testes reforçando a cobertura do agrupamento AD-2: grupo intercalado por outro código, grupo de tamanho 3, lista vazia), 2 deferidos (guarda contra `Sinal` malformado — achado convergente dos dois revisores, redirecionado para quando a Story 1.5 construir `Sinal` a partir do `response_schema`; contagem de "palavra" por `.split()` ingênua o bastante para contar fragmentos numéricos), 7 rejeitados (artefato de como o diff foi montado para revisão, sensibilidade a maiúscula/pontuação que é o comportamento especificado por "substring exata", variável de loop sombreando nome de teste em arquivo diferente, lookup redundante em dict, comentário de teste impreciso sobre qual teste garante o quê, números fixos no próprio Auto Run Result, exaustão teórica de iterador que o contrato de tipo `list[Sinal]` já exclui).
- Bônus da revisão: o primeiro rascunho do patch de teste do grupo intercalado usava uma citação de `catalogo.py` que não era substring do `TEXTO` local do arquivo de teste — a própria suíte pegou (`1 failed`) antes de eu confirmar o patch como concluído.

**Riscos residuais / decisões por ausência de fonte:**
- Nenhum desvio do spec. O contrato `Sinal` de `estado.py` já existia (Story 1.1) e bateu exatamente com o que o spec descreve; nenhuma decisão de forma foi necessária.
- `evidencia.py` não foi acrescentado ao `parametrize` de `test_modulos_folha_so_importam_o_que_a_story_permite` em `test_contrato.py`, conforme instruído — só recebeu a checagem de import sem SDK em `test_import_sem_credencial.py`.
- Nenhuma linha tocada em `plataforma/ingestao.py`, `plataforma/config.py`, `docs/reclamacoes_reclameaqui.csv`, `baseline.py` ou `classificador.py`.
- Dois itens de baixo risco ficaram deferidos em `deferred-work.md`, ambos revisitáveis quando a Story 1.5 (`analise.py`) nascer.
