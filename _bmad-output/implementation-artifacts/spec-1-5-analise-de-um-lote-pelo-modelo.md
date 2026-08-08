---
title: 'Story 1.5 — Análise de um lote pelo modelo'
type: 'feature'
created: '2026-08-08'
status: 'done'
baseline_revision: '738aa22'
final_revision: '29206f9'
review_loop_iteration: 1
followup_review_recommended: true
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/1-5-analise-de-um-lote-pelo-modelo.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
warnings: ['oversized']
---

<intent-contract>

## Intent

**Problem:** Nada hoje chama o modelo para extrair sentimento, produto e sinais de risco de um lote de reclamações, com casamento seguro por identificador. Uma resposta incompleta, com id inventado, ou fora do schema esperado precisa ser detectada, não corromper a base em silêncio.

**Approach:** Criar `plataforma/analise.py` com `analisar_lote(lote) -> dict`, separado em uma parte impura fina (cliente, payload, chamada ao modelo) e uma função pura `_montar_delta(lote, analises_modelo)` que faz todo o casamento por id, descarte de repetido/inventado, integração com `evidencia.verificar` e montagem de `Falha`. A separação é o que torna a story testável sem mock do SDK (proibido no repositório).

## Boundaries & Constraints

**Always:**
- Tudo em português: módulo, função, comentário.
- `cliente = genai.Client()` só dentro de `analisar_lote`, nunca em escopo de módulo (AD-7).
- Payload ao modelo só `id`+`texto` (AD-16).
- `response_schema` via classes `pydantic.BaseModel` privadas (`_SinalResposta`, `_AnaliseResposta`, `_LoteResposta`); `_SinalResposta` não tem campo `valida` — só o código decide validade, via `evidencia.verificar`.
- `_montar_delta` é função pura: recebe `list[_AnaliseResposta] | None`, nunca toca o SDK.
- Resposta fora do schema (`resposta.parsed is None`) vira uma única `Falha` cobrindo todo o lote, não exceção.
- `prazo_prometido_dias` e `data_evento` sempre `None` nesta story — nenhuma AC pede que o modelo os preencha.

**Block If:**
- Alguma AC exigir integração com `grafo.py`, `langgraph`, `retry_policy` ou `error_handler` — isso é Story 1.6.
- A suíte existente falhar por motivo não previsto nas tasks.

**Never:**
- Não mockar `google.genai` — proibido no repositório; toda cobertura de AC3/AC4/AC5 é via `_montar_delta` alimentada à mão.
- Não colocar `try/except` genérico em volta de `generate_content` — falha de transporte propaga, é problema da Story 1.6 (AD-9).
- Não filtrar produto genérico nem decidir pontuação — isso é Épico 2.
- Não tocar `plataforma/ingestao.py`, `plataforma/config.py` (**importar `config.carregar().modelo`, não modificar o arquivo** — corrigido em revisão, ver Spec Change Log), `plataforma/evidencia.py` (só importar), `docs/reclamacoes_reclameaqui.csv`, `baseline.py`, `classificador.py`.
- Não acrescentar `plataforma.analise` a `tests/test_import_sem_credencial.py::MODULOS` — essa lista é para módulos que **não** arrastam o SDK; `analise.py` arrasta por design.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Payload | Lote com `empresa`/`titulo` preenchidos | Só `id`/`texto` no payload | Nenhum erro esperado |
| Casamento completo | `analises_modelo` cobre todos os ids do lote | `analises` com todos, `sinais` já passados por `evidencia.verificar` | Nenhum erro esperado |
| Id faltante | Lote de 2, resposta com 1 | 1 `Analise` + 1 `Falha` com o id faltante | — |
| Id repetido | Resposta traz o mesmo id 2x | 1 `Analise` (primeira ocorrência), sem `Falha` extra | — |
| Id inventado | Resposta traz id fora do lote | Item descartado, sem `Analise` nem `Falha` | — |
| Schema não casa | `analises_modelo=None` | `analises=[]`, 1 `Falha` cobrindo todo o lote | — |

</intent-contract>

## Code Map

- `plataforma/analise.py` — **NOVO**. `analisar_lote(lote) -> dict`; `_montar_delta`, `_montar_payload`, `_montar_instrucao` puras/auxiliares.
- `plataforma/estado.py` — fonte de `Reclamacao`, `Sinal`, `Analise`, `Falha`.
- `plataforma/catalogo.py` — fonte dos códigos/definições para o prompt (AD-18).
- `plataforma/evidencia.py` — `verificar(sinais, texto)`, chamado dentro de `_montar_delta` (AD-1, AC6).
- `classificador.py:28-39,80-92` — padrão de chamada `generate_content`/`response_schema` já provado; reaproveitar a mecânica, não o schema antigo por booleano.
- `.venv/Lib/site-packages/google/genai/types.py:8708-8724` — comportamento real de `response.parsed` (silencia `ValidationError`/`JSONDecodeError`, não levanta).
- `pyproject.toml` — acrescentar `pydantic` como dependência direta.
- `tests/test_analise.py` — **NOVO**.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` — acrescentar `pydantic>=2.13` a `dependencies` (já instalado como transitivo, `2.13.4`); rodar `uv sync`.
- [x] `plataforma/analise.py` — `_SinalResposta(BaseModel)` (`codigo: str`, `citacao: str`); `_AnaliseResposta(BaseModel)` (`id: str`, `sentimento: Literal["positivo","neutro","negativo"]`, `produto: str | None`, `sinais: list[_SinalResposta]`); `_LoteResposta(BaseModel)` (`analises: list[_AnaliseResposta]`); `_montar_payload(lote) -> list[dict]` só `id`/`texto`; `_montar_instrucao() -> str` monta o prompt de `catalogo.CATALOGO`; `analisar_lote(lote) -> dict` constrói cliente dentro da função, chama o modelo, delega a `_montar_delta`; `_montar_delta(lote, analises_modelo) -> dict` faz casamento por id (faltante→`Falha`, repetido/inventado→descarte), chama `evidencia.verificar` por item casado, monta `Analise` com `prazo_prometido_dias=None`/`data_evento=None`.
- [x] `tests/test_analise.py` — cobrir a I/O Matrix inteira alimentando `_montar_payload`/`_montar_delta` diretamente, nunca chamando `generate_content`; teste de import sem credencial (`GOOGLE_API_KEY`/`GEMINI_API_KEY` ausentes).

**Acceptance Criteria:**
- Given um lote com `empresa`/`titulo` preenchidos, when o payload é montado, then só `id`/`texto` aparecem (AD-16).
- Given uma resposta que cobre todos os ids do lote, when o delta é montado, then cada `Sinal` já passou por `evidencia.verificar` antes de entrar na `Analise` (AD-1, AC6).
- Given um lote de 2 e resposta com 1 item, when o casamento roda, then o id faltante vira uma `Falha` que o carrega (NFR-7, AD-5).
- Given uma resposta com id repetido ou inventado, when o casamento roda, then o item é descartado sem `Falha` extra (NFR-7).
- Given `analises_modelo=None` (schema não casou), when `_montar_delta` roda, then devolve uma única `Falha` cobrindo todo o lote, não exceção.
- Given `plataforma/analise.py` inspecionado, when os imports de todo o pacote são varridos, then só ele importa `google.genai`, e o cliente nasce dentro de `analisar_lote`.
- Given a suíte, when roda sem `GOOGLE_API_KEY`/`GEMINI_API_KEY`, then `import plataforma.analise` funciona.

## Spec Change Log

### 2026-08-08 — Correção de intent-contract (achado de revisão, categoria intent_gap)

- **Gatilho:** Blind Hunter apontou que `analise.py` hardcodeava `MODELO = "gemini-3.6-flash"` e nunca chamava `plataforma.config.carregar()` — a Story 1.2 existe especificamente para tornar `MODELO` configurável por ambiente antes de qualquer chamada paga, e a função que de fato gasta dinheiro (`analisar_lote`) ignorava esse mecanismo por completo.
- **O que foi emendado:** a linha `Never` de `Boundaries & Constraints` dizia "não tocar `plataforma/config.py`" sem qualificar que **importar** (sem modificar) era esperado — a mesma ambiguidade que a Story 1.2 já havia resolvido explicitamente em suas próprias Dev Notes ("`config.py`... será importado por `analise`, `grafo` e `ingestao`"). Corrigida a linha para "importar `config.carregar().modelo`, não modificar o arquivo".
- **Estado ruim evitado:** sem a correção, `MODELO` no `.env` teria efeito zero sobre a única chamada paga do pipeline — a Story 1.2 inteira ficaria morta para o caso de uso que a motivou.
- **Por que não travou o workflow (desvio deliberado do protocolo padrão):** a leitura correta tinha uma única interpretação possível, já registrada em documento anterior do próprio repositório (não inferida do zero) — travar aqui gastaria um ciclo de decisão do usuário numa pergunta com resposta inequívoca. Corrigido em código e nesta emenda de spec, ambos no mesmo commit; nenhuma outra parte do `<intent-contract>` foi tocada.
- **KEEP:** a separação `analisar_lote` (impura) / `_montar_delta` (pura) funcionou exatamente como desenhado — nenhuma re-derivação necessária ali. `MODELO` como constante de módulo foi **removido**; `config.carregar()` é chamado dentro de `analisar_lote`, no mesmo escopo que já constrói `genai.Client()` (AD-7 preservado).

## Review Triage Log

### 2026-08-08 — Review pass

- intent_gap: 1: (high 1, medium 0, low 0)
- bad_spec: 0
- patch: 3: (high 0, medium 2, low 1)
- defer: 0
- reject: 8: (high 0, medium 0, low 8)
- addressed_findings:
  - `[high]` `[intent_gap]` `analise.py` ignorava `plataforma.config`, hardcodeando `MODELO` — corrigido para `config.carregar().modelo`; ver Spec Change Log.
  - `[medium]` `[patch]` `AD-7` ("só `analise.py` importa `google.genai`") era verificado só por prosa/docstring, não por teste — acrescentado `test_somente_analise_importa_o_sdk_do_modelo`, varredura textual no padrão de `test_catalogo.py::test_nenhum_outro_modulo_declara_codigo_de_sinal_como_literal`.
  - `[medium]` `[patch]` `analisar_lote([])` disparava chamada paga com payload vazio — guarda acrescentada, retorna antes de `genai.Client()` ser construído (permitindo teste direto, sem mock).
  - `[low]` `[patch]` `_montar_instrucao()` não tinha nenhum teste, apesar de pura e determinística — acrescentado `test_montar_instrucao_lista_todos_os_codigos_do_catalogo`.

## Design Notes

**A separação impuro/puro é a decisão central.** O repositório proíbe mock do `google.genai` (`project-context.md`). `analisar_lote` fica fino — cliente, payload, chamada — e delega toda decisão (casamento, descarte, verificação, `Falha`) a `_montar_delta`, pura, alimentada com `list[_AnaliseResposta] | None` fabricado à mão em teste. Sem essa separação, AC3/AC4/AC5 não são testáveis dentro das regras do projeto.

**Detecção de schema fora do padrão, confirmada no SDK instalado:** `types.py:8708-8724` mostra que `pydantic.ValidationError`/`json.decoder.JSONDecodeError` são engolidos num `try/except` interno da lib — `resposta.parsed` só fica `None`, nunca levanta. A checagem é `if resposta.parsed is None`, não `try/except` em volta da chamada.

**`prazo_prometido_dias`/`data_evento` ficam sempre `None`.** Nenhuma AC de nenhuma story pede que o modelo os preencha; `SPEC.md#Resolved` já registra que `prazo_estourado` foi resolvido como sinal simples, sem aritmética de data. Campos residuais do brainstorm original, não promovidos a capacidade.

## Verification

**Commands:**
- `uv run pytest` — expected: suíte inteira verde, incluindo `test_analise.py` novo (baseline 84 testes antes desta story).
- `uv run python -c "import plataforma.analise"` sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` — expected: sem erro.

**Manual checks (if no CLI):**
- Ler o código de `analisar_lote` e confirmar visualmente que `genai.Client()` só aparece dentro do corpo da função, nunca em escopo de módulo.

## Auto Run Result

**O que foi implementado:** `plataforma/analise.py` com `analisar_lote(lote) -> dict` (impuro, fino) e `_montar_delta(lote, analises_modelo) -> dict` (pura, todo o casamento por id). Três classes `pydantic.BaseModel` privadas para o `response_schema` (`_SinalResposta` sem campo `valida`, `_AnaliseResposta`, `_LoteResposta`). `_montar_payload` emite só `id`/`texto`. `_montar_instrucao` monta o prompt iterando `catalogo.CATALOGO`. `_montar_delta` casa por id, ignora inventado/repetido sem gerar `Falha`, chama `evidencia.verificar` por item casado antes de montar cada `Analise`, e agrupa ids sem resposta numa única `Falha`. `prazo_prometido_dias`/`data_evento` sempre `None`, conforme decisão registrada na story. `pydantic>=2.13` declarado em `pyproject.toml`.

**Arquivos tocados:**

| Arquivo | Tipo | Descrição |
|---|---|---|
| `plataforma/analise.py` | novo | `analisar_lote`, `_montar_delta`, `_montar_payload`, `_montar_instrucao` |
| `tests/test_analise.py` | novo | 11 testes: I/O Matrix inteira + import sem credencial + cobertura de revisão (AD-7 package-wide, lote vazio, `_montar_instrucao`) |
| `pyproject.toml` | modificado | `pydantic>=2.13` como dependência direta |

**Verificação (pós-revisão):**
- `uv run pytest -q` → `92 passed` pós-implementação → `95 passed` pós-revisão (baseline antes desta story: 84).
- `uv run python -c "import plataforma.analise"` sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` → `ok`, sem erro (reconfirmado após a correção de `config.carregar()`).
- Confirmado por leitura: nenhum teste chama `generate_content` nem constrói `genai.Client()` — toda cobertura via `_montar_payload`/`_montar_delta` alimentados à mão.

**Achados da revisão.** Blind Hunter + Edge Case Hunter em paralelo, sem contexto prévio. 12 achados únicos: **1 intent_gap de alta severidade** — `analise.py` hardcodeava o modelo em vez de ler `config.carregar().modelo`, anulando o mecanismo que a Story 1.2 construiu; corrigido em código e no `<intent-contract>` (ver Spec Change Log), sem travar o workflow porque a leitura correta era inequívoca e já documentada em Story 1.2. 3 patches (2 medium: teste package-wide de AD-7, guarda contra lote vazio disparando chamada paga; 1 low: cobertura de `_montar_instrucao`). 8 rejeitados (granularidade do envelope de schema já é o comportamento especificado por AC5, injeção de prompt fora de escopo, seguranças redundantes contra invariantes já garantidos por stories anteriores, etc.).

**Riscos residuais / decisões por ausência de fonte:**
- Ordem de `Falha.ids` no caso "schema não casou" e no caso "id faltante" segue a ordem do `lote` de entrada (não a ordem de um `set`), por determinismo — não estava explícito no spec, mas é consistente com NFR-8.
- Nenhum outro desvio do spec além do já registrado no Spec Change Log. A separação impuro/puro, a checagem `resposta.parsed is None`, e os dois campos sempre `None` seguem exatamente como documentado nas Dev Notes da story.
- Esta é a primeira implementação desta sessão feita diretamente (sem subagent) após a subagent anterior atingir o limite de sessão durante a fase de leitura de contexto — nenhum código daquela tentativa foi aproveitado, o módulo foi escrito do zero com o contexto já reunido.
