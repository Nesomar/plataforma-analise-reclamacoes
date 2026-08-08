---
title: 'Story 1.3 — Ingestão que rejeita base inválida antes de gastar'
type: 'feature'
created: '2026-08-08'
status: 'done'
baseline_revision: 'decb05d'
final_revision: '876c80f'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/1-3-ingestao-que-rejeita-base-invalida-antes-de-gastar.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
warnings: ['oversized']
---

<intent-contract>

## Intent

**Problem:** O CSV de reclamações pode ter coluna ausente, `ID_Reclamacao` duplicado ou nenhuma linha de dado. Nada hoje valida isso antes de qualquer chamada paga ao modelo — o erro só apareceria tarde, na fatura da API.

**Approach:** Criar `plataforma/ingestao.py` com `carregar(caminho: str) -> list[Reclamacao]`: lê o CSV com `utf-8-sig`/`;`, valida as sete colunas e a unicidade de `ID_Reclamacao`, converte `Data` para ISO-8601, e levanta `ValueError` nomeando a causa antes de devolver qualquer coisa. Sem fatiamento em lotes — isso é Story 1.6.

## Boundaries & Constraints

**Always:**
- Tudo em português: módulo, função, mensagem de erro.
- Ler com `encoding="utf-8-sig"` e `csv.DictReader(delimiter=";")` — BOM cru quebra o nome da primeira coluna.
- `Reclamacao` vem de `plataforma.estado`, nunca redeclarada.
- `ValueError` nomeia a coluna faltante, o id repetido, ou o caminho do arquivo vazio — nunca erro cru do stdlib.
- `ingestao.py` não importa `google.genai`, direta nem transitivamente.

**Block If:**
- Alguma AC exigir importar `plataforma.config`, `tamanho_lote` ou fatiamento em lotes — isso é Story 1.6, não esta.
- A suíte existente falhar por motivo não previsto nas tasks.

**Never:**
- Não fatiar em lotes nem montar `Send` — nó de carga completo só existe após a Story 1.6.
- Não validar o valor de `Status` contra o `Literal` de cinco opções — nenhuma AC pede.
- Não tocar `docs/reclamacoes_reclameaqui.csv`, `baseline.py`, `classificador.py`, `plataforma/config.py`.
- Não acrescentar `ingestao` ao `parametrize` de módulos-folha em `test_contrato.py` — esse teste é só para módulos que não importam nada de `plataforma/`, e `ingestao` importa `estado` por desenho.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| CSV válido | `docs/reclamacoes_reclameaqui.csv` | 50 `Reclamacao`, sem BOM no header, `data` em ISO-8601 | Nenhum erro esperado |
| Coluna ausente | CSV sintético sem uma das 7 colunas | — | `ValueError` nomeando a(s) coluna(s) faltante(s) |
| Id duplicado | CSV sintético com `ID_Reclamacao` repetido | — | `ValueError` nomeando o id repetido |
| CSV sem linha de dado | Cabeçalho válido, zero linhas | — | `ValueError` com causa nomeada |
| Execuções repetidas | Mesmo arquivo, duas chamadas | Mesmo `set` de ids nas duas | Nenhum erro esperado |

</intent-contract>

## Code Map

- `plataforma/ingestao.py` — **NOVO**. `carregar(caminho) -> list[Reclamacao]`.
- `plataforma/estado.py` — fonte de `Reclamacao`; `ingestao` importa de lá (aresta já desenhada em `ARCHITECTURE-SPINE.md`).
- `plataforma/config.py`, `plataforma/catalogo.py` — padrão de módulo a seguir: docstring de propósito, comentário cita fonte, `ValueError` nomeando valor observado.
- `tests/test_ingestao.py` — **NOVO**.
- `tests/test_import_sem_credencial.py:6` — `MODULOS`; acrescentar `"plataforma.ingestao"`.
- `_bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md` — schema do CSV: `ID_Reclamacao`, `Data`, `Empresa`, `Titulo`, `Descricao`→`texto`, `Cidade_Estado`, `Status`.

## Tasks & Acceptance

**Execution:**
- [x] `plataforma/ingestao.py` — criar `carregar(caminho: str) -> list[Reclamacao]`: `COLUNAS_ESPERADAS` como tupla das 7 colunas; checar `fieldnames` antes de iterar (fail-fast); acumular ids vistos num `set` e levantar ao repetir; converter `Data` com `datetime.strptime(...).strftime("%Y-%m-%d")`, capturando `ValueError` de data malformada e renomeando com o id da linha; se a lista final estiver vazia, levantar nomeando o caminho.
- [x] `tests/test_ingestao.py` — caso feliz (50 itens, primeiro id bate, todas as datas em `AAAA-MM-DD`); determinismo (duas chamadas, mesmo `set` de ids); coluna faltante, id duplicado e CSV vazio com CSVs sintéticos em `tmp_path` (nunca editar `docs/`); BOM não quebra a leitura.
- [x] `tests/test_import_sem_credencial.py` — acrescentar `"plataforma.ingestao"` a `MODULOS`.

**Acceptance Criteria:**
- Given `docs/reclamacoes_reclameaqui.csv`, when `carregar()` roda, then devolve 50 `Reclamacao`, sem BOM colado no nome da primeira coluna, com `data` em ISO-8601 (FR-3, state-contract.md).
- Given um CSV sem uma das sete colunas, when `carregar()` roda, then levanta `ValueError` nomeando a(s) coluna(s) faltante(s), sem nenhuma chamada ao modelo (FR-3).
- Given um CSV com `ID_Reclamacao` repetido, when `carregar()` roda, then levanta `ValueError` nomeando o id repetido (FR-3).
- Given um CSV com cabeçalho e zero linhas de dado, when `carregar()` roda, then levanta `ValueError` com causa nomeada (AD-13).
- Given o mesmo arquivo processado duas vezes, when as duas chamadas terminam, then o `set` de ids é idêntico (NFR-8).
- Given `plataforma/ingestao.py` inspecionado, when se procura por `google.genai`, then não há import, direto nem transitivo (AD-7) — coberto por `test_import_sem_credencial.py`.

## Spec Change Log

## Review Triage Log

### 2026-08-08 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 4: (high 0, medium 1, low 3)
- defer: 2: (high 0, medium 0, low 2)
- reject: 10: (high 0, medium 0, low 10)
- addressed_findings:
  - `[medium]` `[patch]` Linha do CSV com menos campos que o cabeçalho deixava `DictReader` preencher coluna faltante com `None`, que viraria valor de campo tipado `str` sem erro, ou `TypeError` cru no `strptime` — guarda `None in linha.values()` acrescentada antes de processar a linha, com `ValueError` nomeando a causa.
  - `[low]` `[patch]` `test_data_malformada_levanta_nomeando_id_e_valor` só verificava o valor da data na mensagem, não o id — nome do teste prometia os dois. `match` estendido para cobrir `ID_Reclamacao` e o valor.
  - `[low]` `[patch]` `test_csv_sem_linha_de_dado_levanta_com_causa_nomeada` não tinha `match=`, passaria com qualquer `ValueError`. Acrescentado `match="nenhuma linha de dado"`.
  - `[low]` `[patch]` Nenhum teste exercitava arquivo zero-byte (sem cabeçalho nenhum) — o `fieldnames or ()` defensivo ficava sem cobertura. Teste acrescentado.

## Design Notes

**Por que `ingestao` não entra no teste de módulos-folha:** `test_modulos_folha_so_importam_o_que_a_story_permite` em `tests/test_contrato.py` existe para módulos que não importam nada de `plataforma/` (hoje `estado`, `catalogo`, `config`). `ingestao.py` importa `estado` por desenho — a AC de AD-7 já está coberta por `test_import_sem_credencial.py`, que não exige lista-branca fechada de terceiros.

**Por que o fatiamento não é aqui:** a Story 1.2 registrou como dívida que "quem fatia é `carregar`" apontaria para a Story 1.3, mas o épico real (`epics.md`) move `tamanho_lote`, fusão de lote residual e `Send` para a Story 1.6. As ACs desta story cobrem só leitura, schema, unicidade e data.

## Verification

**Commands:**
- `uv run pytest` — expected: suíte inteira verde, incluindo `test_ingestao.py` novo e a lista `MODULOS` estendida.
- `uv run python -c "import plataforma.ingestao, sys; assert not [m for m in sys.modules if m.startswith('google')]"` — expected: sem saída, sem erro.

**Manual checks (if no CLI):**
- Rodar `carregar("docs/reclamacoes_reclameaqui.csv")` num REPL e conferir `len(resultado) == 50` e `resultado[0]["data"]` no formato `AAAA-MM-DD`.

## Auto Run Result

**O que foi implementado:** `plataforma/ingestao.py` (novo), expondo `carregar(caminho: str) -> list[Reclamacao]`. O módulo lê o CSV com `encoding="utf-8-sig"` e `csv.DictReader(delimiter=";")`, valida as sete colunas esperadas contra `leitor.fieldnames` antes de iterar qualquer linha (fail-fast, `ValueError` nomeando as colunas faltantes), acumula `ID_Reclamacao` num `set` e levanta `ValueError` nomeando o id assim que ele repete, converte `Data` de `DD/MM/AAAA` para ISO-8601 via `datetime.strptime(...).strftime(...)` — capturando `ValueError` de data malformada e relevantando com o id da linha e o valor observado — e levanta `ValueError` nomeando o caminho do arquivo se a lista final vier vazia (cabeçalho sem linha de dado). Nenhum fatiamento em lotes, nenhum import de `plataforma.config`, nenhuma validação de `Status` contra o `Literal` — exatamente o escopo do spec.

`tests/test_ingestao.py` (novo) cobre os seis pontos do Task 2: caso feliz contra `docs/reclamacoes_reclameaqui.csv` (50 itens, primeiro id `RA249827706`, todas as datas em `AAAA-MM-DD`), determinismo entre duas chamadas (mesmo `set` de ids), coluna faltante, id duplicado e CSV sem linha de dado com CSVs sintéticos escritos em `tmp_path`, e um teste de data malformada. Todos os CSVs sintéticos são escritos com `encoding="utf-8-sig"`, prova negativa de que `carregar` não usa leitura crua.

`tests/test_import_sem_credencial.py` (modificado) ganhou `"plataforma.ingestao"` em `MODULOS`, estendendo a verificação executável de AD-7/AD-12 para o módulo novo. `tests/test_contrato.py` não foi tocado, por instrução explícita do spec — `ingestao` importa `estado` por desenho e não pertence ao teste de módulos-folha.

**Arquivos tocados:**

| Arquivo | Tipo |
|---|---|
| `plataforma/ingestao.py` | novo |
| `tests/test_ingestao.py` | novo |
| `tests/test_import_sem_credencial.py` | modificado |

**Resultado dos comandos de verificação (pós-revisão):**

| Comando | Antes da story | Pós-implementação | Pós-revisão |
|---|---|---|---|
| `uv run pytest` | 64 passed | 70 passed | 72 passed |
| `uv run python -c "import plataforma.ingestao, sys; assert not [m for m in sys.modules if m.startswith('google')]"` | — | sem saída, sem erro | sem saída, sem erro (AD-7 confirmado) |

**Achados da revisão.** Blind Hunter (`bmad-review-adversarial-general`) e Edge Case Hunter (`bmad-review-edge-case-hunter`) rodaram em paralelo, sem contexto prévio, contra o diff completo. 16 achados únicos após deduplicação: 4 patches aplicados (1 medium, 3 low), 2 deferidos, 10 rejeitados. Nenhum intent gap, nenhum defeito de spec. O único medium — linha do CSV com menos campos que o cabeçalho deixando `None` entrar num campo tipado `str`, ou estourando `TypeError` cru no `strptime` — foi convergente entre os dois revisores, o que elevou a confiança de que era real; corrigido com uma guarda de uma linha antes de processar a linha. Os 10 rejeitados cobrem cenários de infraestrutura fora do escopo desta story (arquivo inexistente, encoding inválido, CSV corrompido — tratamento de exceção de infraestrutura é do `main.py` futuro, Story 1.7) ou exigiam AC que o spec explicitamente excluiu (validação de `Status`, contra o `Boundaries & Constraints` do próprio spec).

**Riscos residuais / decisões por ausência de fonte:**
- Nenhum desvio do spec. A única correção feita em runtime foi o valor exato do primeiro `id` do CSV real (`"RA249827706"`, confirmado por leitura direta do arquivo) usado na asserção do caso feliz — o spec não fixava esse valor, só pedia que o primeiro id batesse com a primeira linha real.
- Mensagem de coluna faltante usa `sorted(faltantes)` (lista, não set, para saída determinística) — não há AC que prescreva o formato exato da lista, só que a(s) coluna(s) sejam nomeadas; a decisão segue o padrão de `config.py` (`ValueError` com `repr` do valor observado e da referência esperada).
- Nenhuma outra dívida conhecida: a story já registrava (Dev Notes) que fatiamento em lotes e validação de `Status` ficam fora desta story — nenhuma das duas foi implementada, como esperado.
- Dois itens reais de baixo risco ficaram deferidos, registrados em `deferred-work.md`: `ID_Reclamacao` duplicado por espaço em volta não é pego (comparação sem `strip()`), e a validação de `Status` contra o `Literal` — dívida que a revisão da Story 1.1 já havia apontado para esta story, mas que o spec desta story excluiu por não estar em nenhuma AC de `epics.md`; redirecionada para a Story 2.1, primeiro nó que de fato lê `Status`.
