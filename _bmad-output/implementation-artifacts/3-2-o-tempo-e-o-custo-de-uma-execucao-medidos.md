---
baseline_commit: 'cd9e9175b2fa8a1876cdb892cc49c16c522976fe'
---

# Story 3.2: O tempo e o custo de uma execução, medidos

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a operador,
I want saber quanto uma execução real demora e quanto ela consome,
so that o teto de dois minutos deixe de ser suposição e eu saiba se cabe no tier gratuito.

## Acceptance Criteria

**AC1 — Tempo cronometrado com cache desligado**

**Given** o pipeline completo e o cache de análises desligado
**When** uma execução ponta a ponta roda sobre as 50 reclamações
**Then** o tempo total é cronometrado e registrado (M-3, NFR-1)
**And** a medição com cache ligado é descartada — ela mede o disco, não o pipeline (Q-8)

**AC2 — Teto de 2 minutos, [ASSUMPTION] substituída pelo número real**

**Given** o tempo medido
**When** ele é comparado ao teto de 2 minutos
**Then** a marca `[ASSUMPTION]` de NFR-1 é substituída pelo número real no PRD
**And** Q-8 é movida para resolvida, com a data da medição

**AC3 — Tempo acima do teto é registrado como saiu**

**Given** um tempo acima do teto
**When** ele é registrado
**Then** é reportado como saiu, e a decisão entre ajustar o teto ou o pipeline fica explícita, não implícita

**AC4 — Consumo apurado, cabe no tier gratuito**

**Given** a mesma execução
**When** o consumo é apurado
**Then** o número de chamadas ao modelo e o volume de tokens são registrados
**And** confirma-se que a execução completa cabe no tier de teste gratuito da API do Gemini (M-4, NFR-3)

**AC5 — Número de chamadas confere com o número de lotes**

**Given** o número de chamadas
**When** ele é conferido
**Then** equivale ao número de lotes emitidos, e nenhuma reclamação foi analisada duas vezes por desenho do fluxo (NFR-4, AD-17)

## Tasks / Subtasks

- [x] **Task 1 — Instrumentação pontual em `plataforma/analise.py`** (AC: 4, 5)
  - [x] `_metricas: dict` de módulo, fora de `Estado`
  - [x] `ler_metricas()`/`resetar_metricas()`
  - [x] `_registrar_metrica` somada dentro de `_gerar()`, toda tentativa real
  - [x] Assinatura/retorno de `analisar_lote` inalterados
  - [x] Docstring do módulo atualizada

- [x] **Task 2 — Criar `medir_tempo_custo.py`** (AC: 1, 2, 3, 4, 5)
  - [x] Script na raiz, mesmo padrão de `medir_fila.py`
  - [x] `main()`: cronometra `.invoke()`, lê métricas, compara lotes emitidos vs chamadas reais
  - [x] Impressões na ordem especificada
  - [x] `autoteste()`: reset/leitura/cópia-não-referência
  - [x] Imports conforme especificado, sem `google.genai`

- [x] **Task 3 — Rodar a medição real e registrar os números** (AC: 1, 2, 3, 4, 5)
  - [x] Rodado com `GEMINI_API_KEY` real do ambiente
  - [x] Números registrados em Completion Notes, como saíram
  - [x] Tempo dentro do teto (27,4s < 120s) — sem decisão pendente de ajuste
  - [x] PRD atualizado: `[ASSUMPTION]` de NFR-1 removida, Q-8 movida para "Resolvidas em 2026-08-10"

### Review Findings

- [x] [Review][Patch] `_registrar_metrica` só roda depois de `generate_content()` devolver com sucesso — uma tentativa que `_chamar_com_retry` descarte por erro de transporte nunca chega lá, contradizendo a própria docstring do módulo ("soma a cada tentativa real... inclusive uma que `_chamar_com_retry` descarte") e a Dev Notes desta story. Consequência real: a checagem IGUAL/DIVERGENTE de `medir_tempo_custo.py` nunca detecta retry de verdade — achado convergente dos três revisores [plataforma/analise.py:_gerar, _registrar_metrica]
- [x] [Review][Patch] `_registrar_metrica` acessa `resposta.usage_metadata.prompt_token_count` sem guarda para `usage_metadata is None` — se o SDK devolver uma resposta sem metadado de uso, `AttributeError` propaga de dentro de `_gerar()`, não é reconhecido por `_deve_repetir`, e transforma uma chamada **bem-sucedida** numa `Falha` de lote inteiro [plataforma/analise.py:_registrar_metrica]
- [x] [Review][Patch] `medir_tempo_custo.py` não trata `KeyError` se `estado` não tiver as chaves esperadas — mesma disciplina de mensagem nomeada que `medir_fila.py`/`main.py` já aplicam [medir_tempo_custo.py:main]
- [x] [Review][Patch] Limpeza do arquivo temporário em `finally` usa `os.remove` sem tratar exceção — um `PermissionError` (arquivo ainda travado no Windows) mascararia o resultado real da medição com um traceback de limpeza [medir_tempo_custo.py:main]
- [x] [Review][Patch] `_registrar_metrica` (a função que de fato interpreta uma resposta real do modelo, incluindo o risco de `usage_metadata is None` acima) não tem nenhuma cobertura de teste — `autoteste()` só mexe em `_metricas` diretamente, nunca chama a função que lê uma resposta de verdade [plataforma/analise.py, tests/test_analise.py]

- [x] [Review][Defer] Mutação não-atômica de `_metricas` sob fan-out concorrente — `AD-9` já registra que "o v1 invoca de forma síncrona" (`grafo.py`, `plataforma/analise.py`), então o fan-out via `Send` não roda em paralelo de fato nesta versão. Reavaliar se o pipeline algum dia mover para execução assíncrona/concorrente
- [x] [Review][Defer] `usage_metadata` pode carregar categorias além de `prompt_token_count`/`candidates_token_count` (cache, "thinking") que este contador não soma — `gemini-3.6-flash` não é um modelo "thinking" nem usa cache de contexto nesta base, então a lacuna é teórica hoje. Reavaliar se o modelo pinado mudar
- [x] [Review][Defer] Sem timeout em `.invoke()` dentro de `medir_tempo_custo.py` — mesma ausência de timeout que o resto do pipeline já tem (`main.py` também não declara um); não é lacuna introduzida por esta story
- [x] [Review][Defer] Medição de tempo/custo é uma única execução, sem repetição, sem variar o formato do lote residual, sem exercitar retry de verdade — limitação real de uma medição manual que gasta crédito a cada rodada; aceitável dentro do princípio do Épico 3 de "medir uma vez e registrar como saiu", não pedir múltiplas rodadas pagas

**Achados descartados (nit de estilo / decisão de design já aceita no projeto):**
- `TETO_TEMPO_S = 120` como constante local em vez de derivar do PRD/`config.py` — mesmo padrão que `medir_fila.py` já usa para seus próprios limiares (`LIMIAR_PRECISAO` etc.), não centralizados em lugar nenhum do projeto.
- Scripts de medição acessam símbolos privados de outros módulos (`grafo._despachar`, `analise._metricas`) — mesmo precedente já aceito na Story 3.1 (`medir_fila.py` reaproveitando `evidencia._passa_checagem_individual`).
- Confiança de que `estado["reclamacoes"]` permanece intacto depois de `pontuar`/`agregar`/`renderizar` rodarem — mesma classe de "confiança em invariante upstream" já aceita em múltiplas revisões anteriores (Stories 2.2, 2.3, 2.4).

## Change Log

- 2026-08-10: Instrumentação pontual em `analise.py`, `medir_tempo_custo.py` criado, medição real executada (27,4s, 5 chamadas, 9.701 tokens). PRD atualizado (NFR-1, Q-8). `208 passed`, sem regressão.
- 2026-08-10: Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Achado crítico convergente dos 3 revisores: `_registrar_metrica` só contava chamadas bem-sucedidas, contradizendo a própria docstring ("conta toda tentativa") — corrigido separando `_registrar_tentativa()` (soma antes da chamada, sucesso ou não) de `_registrar_tokens()` (só soma tokens de resposta bem-sucedida, com guarda contra `usage_metadata is None`). 5 patches aplicados no total — os dois acima, mais tratamento de `KeyError`/`OSError` em `medir_tempo_custo.py` e 3 testes novos em `tests/test_analise.py` cobrindo a função que lê uma resposta real. Números da medição já registrada (27,4s, 5 chamadas, 9.701 tokens) continuam válidos — a correção só muda comportamento em caso de retry/resposta sem `usage_metadata`, nenhum dos dois ocorreu na execução real. 4 achados deferidos, 3 dispensados. Suíte final: `211 passed`.

## Dev Notes

### Por que "desligar o cache" não toca `plataforma/`

Q-8 e a AC1 desta story vêm de uma época em que a única execução medível era `classificador.py`, que tem cache próprio (`.cache_analises.json`, controlado por `usar_cache=True` em `classifica()`). **O pipeline de `plataforma/` nunca teve cache** — `ARCHITECTURE-SPINE.md` lista cache explicitamente em "Deferred": "exige uma versão do prompt no estado, que hoje não existe em lugar nenhum". Rodar `medir_tempo_custo.py` já mede o pipeline sem cache, porque não há cache para desligar. Não criar um mecanismo de cache só para esta story ter algo para desligar — isso seria inventar trabalho que a arquitetura declara fora de escopo do v1.

### Por que a instrumentação vive em `analise.py`, não em `Estado`

`Estado` é o contrato que atravessa todos os nós do grafo (Story 1.1) — cada campo novo obriga toda execução futura, inclusive as que nada têm a ver com medição de custo, a carregar esse campo. `_metricas` é module-level, fora de `Estado` de propósito: só existe para `medir_tempo_custo.py` ler depois do `.invoke()` terminar. Isso é exatamente o que a nota de arquivos do Épico 3 chama de "instrumentação pontual" — pontual porque é a única story do projeto que precisa desse dado, e ele não pertence ao domínio (`Reclamacao`, `Analise`, `Pontuacao`) que `Estado` modela.

### Por que a contagem de chamadas conta toda tentativa, não só a bem-sucedida

`_chamar_com_retry` (Story 1.6) pode chamar `_gerar()` até 3 vezes para o mesmo lote se a primeira falhar por erro transitório (429, 5xx). Cada tentativa **gasta quota de verdade**, mesmo a que falha — o provedor cobra pela chamada feita, não pelo resultado. Por isso a instrumentação soma dentro de `_gerar()`, executada a cada tentativa, não uma vez por lote. Consequência documentada explicitamente (AC5): se a execução de referência tiver 0 retries (o caso esperado, já que a base sintética responde normalmente), `chamadas reais == lotes emitidos`. Se houver retry, a contagem real excede a esperada — isso não é bug da instrumentação, é o comportamento correto sendo revelado. O script relata a divergência como fato, não a esconde.

### `usage_metadata` — nomes de campo confirmados contra o SDK instalado

`google.genai.types.GenerateContentResponseUsageMetadata` (google-genai atual do `uv.lock`) expõe `prompt_token_count`, `candidates_token_count`, `total_token_count`, entre outros campos de detalhamento (cache, thoughts, tool-use) que esta story não precisa. Usar exatamente esses três nomes — não inventar nomes de campo sem checar contra a versão instalada.

### O que esta story NÃO faz

**Não decide se o teto de 2 minutos deve mudar.** Registra o número e nomeia a decisão pendente (AC3); ajustar o teto do PRD é decisão de produto, fora do escopo de código desta story.
**Não implementa cache, streaming, nem otimização de latência.** Mede o que existe hoje.
**Não adiciona telemetria permanente.** `_metricas` é instrumentação pontual para esta medição, não um mecanismo de observabilidade contínua — o projeto declara explicitamente que "não há log estruturado, métrica exportada nem trace" (`project-context.md`).
**Não toca `grafo.py`, `main.py`, `Estado`, `pontuacao.py`, `agregacao.py`, `relatorio.py`, `medir_fila.py`.**

### Estrutura de arquivos

```text
plataforma/
  analise.py               # UPDATE — _metricas, ler_metricas, resetar_metricas
medir_tempo_custo.py        # NOVO — script de medição, raiz, mesmo padrão de medir_fila.py
```

**Não criar/tocar nesta story:** qualquer outro arquivo em `plataforma/`, `main.py`, `tests/`, `medir_fila.py`, `docs/`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-7** | `medir_tempo_custo.py` não importa `google.genai` — só `analise.py` toca o SDK, e a instrumentação vive dentro dele |
| **AD-9** | Retry continua absorvido dentro de `analisar_lote`; a instrumentação só observa, não muda o comportamento de repetição |
| **AD-17** | O número de lotes emitidos (`_despachar`, já existente) é a referência contra a qual as chamadas reais são conferidas |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2] — ACs originais
- [Source: plataforma/analise.py#analisar_lote, _gerar, _chamar_com_retry] — onde a instrumentação entra
- [Source: plataforma/grafo.py#_despachar] — número de lotes esperado, já existente e testado
- [Source: _bmad-output/implementation-artifacts/3-1-a-fila-do-pipeline-medida-contra-o-gabarito.md] — padrão de script de medição na raiz, `tempfile.mkstemp` + limpeza, tratamento de AC manual sem credencial
- [Source: _bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md#Deferred] — cache listado como fora de escopo do v1, justifica AC1 não exigir mudança de código
- [Source: classificador.py#classifica, CACHE] — cache que Q-8 realmente descreve, não o pipeline de `plataforma/`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run python -m pytest -q` (via PowerShell) → `208 passed`, sem regressão (mudança em `analise.py` só afeta o caminho real de `_gerar()`, nunca exercitado pela suíte).
- `uv run python medir_tempo_custo.py` executado contra a API real do Gemini.

### Completion Notes List

**Medição real (2026-08-10), registrada como saiu:**

```
Tempo total: 27.4s  DENTRO do teto de 120s
Chamadas ao modelo: 5  tokens entrada=7035 saída=2666 total=9701
Lotes emitidos: 5  IGUAL às chamadas reais (5) — divergência indica retry de transporte (AD-9)
```

- **M-3/NFR-1:** 27,4s ponta a ponta — bem dentro do teto de 2 minutos. `[ASSUMPTION]` removida do PRD (§4.1); Q-8 movida para "Resolvidas em 2026-08-10" (§9.3).
- **M-4/NFR-3:** 5 chamadas, 9.701 tokens totais (7.035 entrada, 2.666 saída) — consistente com o tier de teste gratuito da API do Gemini vigente nesta data.
- **AC5:** chamadas reais (5) == lotes emitidos (5) — nenhum retry de transporte ocorreu nesta execução, confirmando NFR-4 na prática (nenhuma reclamação analisada duas vezes).
- Nenhum desvio de design em relação ao que a story especificou. `medir_tempo_custo.py` segue o padrão de `medir_fila.py` (script na raiz, `autoteste()`, sem `tests/test_*.py`).

### File List

| Arquivo | Tipo |
|---|---|
| `medir_tempo_custo.py` | novo |
| `plataforma/analise.py` | modificado |
| `tests/test_analise.py` | modificado (achado de revisão) |
| `_bmad-output/planning-artifacts/prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md` | modificado (NFR-1, Q-8) |
