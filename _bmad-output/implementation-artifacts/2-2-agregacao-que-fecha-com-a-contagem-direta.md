---
baseline_commit: 'c6776fd57242221e6d3abff7b98ac3dba4edf302'
---

# Story 2.2: Agregação que fecha com a contagem direta

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a gestor,
I want números agregados que batem com a saída por reclamação,
so that eu não descubra depois que o ranking somava algo diferente do que a fila mostrava.

## Acceptance Criteria

**AC1 — `agregar` produz `Agregados` com ranking e distribuição**

**Given** o estado com `analises` e `pontuacoes` preenchidos
**When** `agregar` executa
**Then** produz `Agregados` como `TypedDict`, com ranking de produtos por volume e distribuição de sentimento
**And** cada número agregado bate com a contagem direta sobre a saída por reclamação (CAP-7, AD-20)

**AC2 — `produto = None` vira `não identificado`, visível com total**

**Given** uma `Analise` com `produto = None`
**When** `agregar` executa
**Then** ela entra no ranking sob o rótulo `não identificado`, com seu total
**And** não é descartada nem atribuída a um produto por aproximação (FR-8)

**AC3 — produto genérico marcado por `agregar`, nunca pelo modelo**

**Given** uma `Analise` cujo `produto` está na lista canônica de termos genéricos de `catalogo.py`
**When** `agregar` executa
**Then** ela é marcada como genérica no ranking
**And** essa marcação é feita por `agregar`, nunca pelo modelo (AD-21)

**AC4 — `Agregados` carrega as contagens de FR-2, FR-14, NFR-6, CM-2, CM-3**

**Given** o estado completo
**When** `agregar` executa
**Then** `Agregados` carrega as contagens que FR-2, FR-14, NFR-6, CM-2 e CM-3 reportam: lidas, analisadas, não analisadas, códigos derrubados, ocupação da fila e taxa de produto não nomeado (AD-22)
**And** CM-3 soma produto nulo **e** produto genérico, não apenas o nulo

**AC5 — degradação por mais de 10% não analisadas**

**Given** mais de 10% das reclamações não analisadas
**When** `agregar` executa
**Then** `Agregados` carrega o indicador de degradação já resolvido como booleano
**And** o número usado é reclamações afetadas (`sum(len(f["ids"]) for f in falhas)`), não `len(falhas)` — eventos de `Falha` (NFR-6, AD-5)

**AC6 — degradação por todos os códigos propostos derrubados**

**Given** uma execução em que o modelo propôs ao menos um código de sinal e todos foram derrubados
**When** `agregar` executa
**Then** o indicador de degradação também fica verdadeiro, ainda que a contagem de não analisadas seja zero (NFR-6, AD-13)

**AC7 — fila ordenada, determinística**

**Given** as reclamações com `na_fila = True`
**When** `agregar` executa
**Then** produz a fila ordenada por `pontos` decrescente
**And** o desempate é por `data` mais antiga primeiro, e persistindo o empate por `id` em ordem crescente — a ordem é total e determinística, para que duas execuções sobre a mesma entrada produzam a mesma fila (NFR-8)

**AC8 — `agregar` só ordena e conta, nunca decide pertencimento**

**Given** `agregar`
**When** ele executa
**Then** ordena e conta, e nunca decide pertencimento à fila — `na_fila` já veio de `pontuar` (AD-19)
**And** `agregados` é escrito só por ele

**AC9 — sem SDK do modelo nos imports (AD-7)**

**Given** o módulo `plataforma/agregacao.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai`, direta nem transitivamente

## Tasks / Subtasks

- [x] **Task 1 — Criar `plataforma/agregacao.py`** (AC: 1, 2, 3, 4, 5, 6, 7, 8, 9)
  - [x] `agregar(estado: Estado) -> dict`: lê `reclamacoes`, `analises`, `falhas`, `pontuacoes`; devolve `{"agregados": Agregados(...)}`
  - [x] **Contagens diretas (FR-2, FR-14):** `lidas = len(reclamacoes)`; `analisadas = len(analises)`; `nao_analisadas = sum(len(f["ids"]) for f in falhas)`; `eventos_falha = len(falhas)`
  - [x] **`codigos_propostos` e `codigos_derrubados` (CM-2), por `Analise`, somados entre reclamações — não deduplicados:** para cada `Analise`, `codigos_propostos += len({s["codigo"] for s in analise["sinais"]})` e `codigos_derrubados += len({s["codigo"] for s in analise["sinais"] if not s["valida"]})`. Este é o mesmo padrão de contagem que `main._contar_codigos_derrubados` já usa (Story 1.7) — não reinventar, replicar o comportamento (se `dinheiro_retido` foi derrubado em 5 reclamações diferentes, conta 5)
  - [x] **Ranking de produtos (FR-8, FR-13, AD-21):** agrupar por `produto` — chave `"não identificado"` quando `produto is None` ou é string vazia/só espaços (mesmo critério de "não nomeia" que `catalogo.nao_nomeia_produto` usa para nulo/vazio); `generico = produto não é None e catalogo.nao_nomeia_produto(produto)` — reaproveitar a função existente, não reimplementar a lista de termos. Cada grupo vira um `ItemRanking(rotulo=..., total=..., generico=...)`. Ordenar por `total` decrescente, desempate por `rotulo` em ordem alfabética — determinístico, sem depender de ordem de iteração de dict
  - [x] **`taxa_produto_nao_nomeado` (CM-3):** `sum(catalogo.nao_nomeia_produto(a["produto"]) for a in analises) / analisadas` se `analisadas > 0`, senão `0.0` — soma nulo **e** genérico porque `nao_nomeia_produto` já cobre os dois (AD-21)
  - [x] **Distribuição de sentimento:** contar `positivo`/`neutro`/`negativo` sobre `analises`
  - [x] **Fila ordenada (AC7, NFR-8):** filtrar `pontuacoes` com `na_fila = True`; ordenar por `(-pontos, data da Reclamacao correspondente, id)` — buscar `data` via mapa `id -> Reclamacao`, mesmo padrão de `pontuacao.py`. `fila = [ids nessa ordem]`; `total_na_fila = len(fila)`
  - [x] **`ocupacao_fila` (CM-1):** `total_na_fila / analisadas` se `analisadas > 0`, senão `0.0` — proporção da base **analisada** (só reclamação analisada tem `Pontuacao`, então só ela pode estar na fila)
  - [x] **Degradação (NFR-6, AD-13):** `degradado_falha = lidas > 0 and (nao_analisadas / lidas) > 0.10`; `degradado_derrubada = codigos_propostos > 0 and codigos_derrubados == codigos_propostos`; `degradado = degradado_falha or degradado_derrubada`. `motivo_degradacao`: `None` se não degradado; senão string nomeando qual(is) condição(ões) disparou(aram)
  - [x] **`data_execucao`:** `datetime.date.today().isoformat()` — não existe no `Estado`, é o único dado desta função que não vem de contagem sobre o estado
  - [x] Docstring de módulo: propósito, porquê da não-dedução entre reclamações em `codigos_propostos`/`codigos_derrubados`, porquê da reutilização de `catalogo.nao_nomeia_produto`
  - [x] Imports: `datetime`, `plataforma.catalogo` (`nao_nomeia_produto`), `plataforma.estado` (`Estado`, `Agregados`, `ItemRanking`, `DistribuicaoSentimento`) — sem `google.genai`, sem outro filtro de `plataforma/`

- [x] **Task 2 — Religar `grafo.py`** (AC: 8)
  - [x] Trocar a aresta final de `pontuar -> END` para `pontuar -> agregar -> END`
  - [x] `add_node("agregar", agregacao.agregar)` — sem `retry_policy`/`error_handler`: determinístico, sem rede, mesmo raciocínio de `pontuar` (Story 2.1)
  - [x] Atualizar a docstring de `construir_grafo` e remover o comentário em `_verificar_conservacao` que apontava esta story como pendente

- [x] **Task 3 — Criar `tests/test_agregacao.py`** (AC: 1, 2, 3, 4, 5, 6, 7, 8, 9)
  - [x] Contagens diretas: `lidas`, `analisadas`, `nao_analisadas`, `eventos_falha` batem com fixture construída à mão (CAP-7)
  - [x] `codigos_propostos`/`codigos_derrubados`: mesmo código derrubado em duas `Analise` diferentes conta 2, não 1 (não deduplicado)
  - [x] AC2: `produto=None` → linha `"não identificado"` no ranking, com total correto, não descartada
  - [x] AC3: `produto` em `catalogo.TERMOS_GENERICOS` (ex.: `"produto"`) → `generico=True`; produto não-genérico → `generico=False`
  - [x] CM-3: taxa soma nulo + genérico — fixture com um `None`, um genérico, um específico → taxa bate com `2/3`
  - [x] AC5: `nao_analisadas/lidas > 0.10` → `degradado=True`; ≤ 10% → `False`. Testado com `eventos_falha=1` cobrindo vários ids, provando que o número usado é o de reclamações afetadas, não eventos
  - [x] AC6: todos os `codigos_propostos` derrubados (com `nao_analisadas=0`) → `degradado=True`
  - [x] Caso limpo: nem AC5 nem AC6 disparam → `degradado=False`, `motivo_degradacao=None`
  - [x] AC7: fila ordenada por pontos desc; empate de pontos desempatado por `data` mais antiga; empate de pontos e data desempatado por `id` crescente — quatro reclamações fabricadas cobrindo os três níveis de desempate
  - [x] `ocupacao_fila`: bate com `total_na_fila / analisadas`
  - [x] `agregar` não decide `na_fila` — `Pontuacao` fabricada com `na_fila` já definido, inclusive contra-intuitivo (pontos alto fora da fila), e a fila resultante respeita esse valor tal como veio
  - [x] Import sem credencial: teste local `test_import_agregacao_sem_credencial` em `tests/test_agregacao.py`, mesmo padrão que `test_pontuacao.py` adotou na Story 2.1 (não em `test_import_sem_credencial.py::MODULOS` — `agregacao` importa `catalogo`/`estado`, mesmo caso de `pontuacao`, e o precedente real da 2.1 manteve o teste local em vez de estender aquele MODULOS)

- [x] **Task 4 — Estender `tests/test_grafo.py`** (AC: 8)
  - [x] `test_construir_grafo_tem_os_nos_esperados_sem_invocar`: acrescentar `"agregar"` à tupla de nós esperados
  - [x] Novo teste: nó `"agregar"` sem `retry_policy`/`error_handler`, mesmo padrão do teste já existente para `pontuar`/`analisar_lote`

### Review Findings

- [x] [Review][Patch] Colisão de sentinela no ranking: produto real de texto `"não identificado"` funde com o balde de nulo/vazio [plataforma/agregacao.py:_ranking_produtos]
- [x] [Review][Patch] Cobertura de AD-7 (nenhum módulo folga arrasta `google.*` para `sys.modules`) ausente para `pontuacao`/`agregacao` em `test_import_sem_credencial.py::MODULOS` [tests/test_import_sem_credencial.py]
- [x] [Review][Patch] Rótulo do ranking não remove espaço externo do `produto` não-vazio, criando linha duplicada para variação só de espaçamento [plataforma/agregacao.py:_ranking_produtos]
- [x] [Review][Patch] `test_data_execucao_e_iso_8601` não confere que os grupos separados por `-` são dígitos [tests/test_agregacao.py]
- [x] [Review][Patch] Ramo de `produto` vazio/só-espaços em `_ranking_produtos` sem teste dedicado [tests/test_agregacao.py]
- [x] [Review][Patch] Sem teste para `analises=[]` cobrindo os guardas de divisão por zero (`ocupacao_fila`, `taxa_produto_nao_nomeado`) [tests/test_agregacao.py]
- [x] [Review][Patch] Pluralização fixa `"código(s)"` em `_motivo_degradacao`, texto travado no teste como está [plataforma/agregacao.py:_motivo_degradacao]
- [x] [Review][Defer] `_fila_ordenada` levanta `KeyError` cru se `Pontuacao.id` não existir em `reclamacoes` — deferred, pre-existing (mesmo padrão já presente em `pontuacao.py` desde a Story 2.1, não introduzido por esta story) [plataforma/agregacao.py:_fila_ordenada]
- [x] [Review][Defer] Nenhum teste trava `codigos_derrubados` de `agregacao.py` em sincronia com `main._contar_codigos_derrubados` — deferred, pre-existing (duplicação consciente já documentada nas Dev Notes desta story; testar a sincronia exigiria acoplar os dois módulos, o que a própria story rejeitou) [plataforma/agregacao.py, main.py]

**Achados descartados (falso positivo / já coberto em outra camada):**
- Mesmo `codigo` com `valida` misto dentro de uma `Analise` — `evidencia.verificar` garante que todo `Sinal` do mesmo código numa `Analise` compartilha o mesmo `valida` (AD-2), então `agregacao.py` nunca vê essa combinação.
- `sentimento` fora de `{positivo, neutro, negativo}` — tipado como `Literal` em `estado.py` e imposto pelo `response_schema` do modelo em `analise.py`; fronteira de confiança já é o próprio SDK, não `agregar`.
- `id` duplicado em `reclamacoes` — unicidade já validada e forçada em `ingestao.py` (Story 1.3).
- `nao_analisadas` contado em dobro por overlap entre `Falha.ids` — `_verificar_conservacao` (AD-6) já assegura `lidas == analisadas + afetadas` antes de `agregar` rodar.
- `Pontuacao` duplicada na fila — `pontuar` produz uma `Pontuacao` por `Analise` (AD-19) e `Analise.id` já é único por construção.

## Dev Notes

### `data_execucao` não vem do `Estado` — é a única leitura de relógio nesta story

Nenhuma story anterior escreveu data de execução em lugar nenhum do `Estado`, e `state-contract.md`/`estado.py` não têm campo para isso. `Agregados.data_execucao` existe para FR-14 ("o relatório informa data da execução"). `agregar` é o nó que produz `Agregados`, então é aqui que a leitura do relógio acontece — `datetime.date.today().isoformat()`. Isso não viola AD-12 ("funções puras alimentadas por `Analise` fabricada à mão", "nenhum teste faz chamada de rede"): não há chamada de rede nem dependência externa, só o relógio do sistema. Para testar sem acoplar ao dia da execução do teste, o teste de `data_execucao` deve só checar o formato (ISO-8601, `len == 10`, três grupos separados por `-`) ou usar `monkeypatch` sobre `datetime.date` se precisar de um valor fixo — não comparar contra uma data hardcoded.

### `motivo_degradacao` — texto esperado

Não há AC prescrevendo o texto exato, só que ele "nomeia qual das duas condições disparou" (linha `agregados: Agregados` em `estado.py`). Como este módulo não escreve nada para o template ainda (isso é Story 2.5), o texto é livre desde que nomeie a condição e traga os números — sugestão, para manter consistência com o estilo de mensagem já usado em `main.py`/`config.py` (mensagem nomeando a causa com o valor observado):

- Só AC5: `f"mais de 10% não analisadas ({nao_analisadas}/{lidas})"`
- Só AC6: `f"todos os {codigos_propostos} código(s) de sinal propostos foram derrubados"`
- As duas: concatenar as duas frases com `"; "`

O teste deve conferir que o texto **contém** os números relevantes, não a string inteira formatada — não travar demais numa frase que pode mudar de redação sem mudar de sentido.

### Por que `codigos_propostos`/`codigos_derrubados` replicam a lógica de `main._contar_codigos_derrubados` em vez de importá-la

`main.py` já calcula "códigos derrubados" para a Story 1.7 (FR-2, impresso no terminal), com a mesma semântica: por `Analise`, códigos distintos inválidos, somados sem deduplicar entre reclamações (`main.py:42-53`, docstring documenta o motivo). `agregacao.py` não pode importar `main.py` — seria inversão de dependência, `main` é o entrypoint que monta o grafo, não um filtro. E `main.py` não pode importar `agregacao.py` nesta story porque isso está fora do escopo desta AC (que é só sobre a forma de `Agregados`, não sobre religar `main.py` para ler dele) — **não tocar `main.py` nesta story**. A duplicação de ~5 linhas entre os dois é aceita conscientemente; uma story futura (quando `main.py` for religado para ler `agregados` em vez de recalcular — provavelmente perto da Story 2.6, quando o relatório e a saída final se consolidam) pode remover `_contar_codigos_derrubados` de `main.py` e delegar para `agregados["codigos_derrubados"]`. Não fazer essa remoção agora — está fora do pedido desta story.

### `codigos_propostos` é conceito novo, não existia antes desta story

Diferente de `codigos_derrubados` (que `main.py` já calcula), `codigos_propostos` é introduzido agora como denominador de CM-2 e para a condição de AC6. Mesma granularidade de contagem: por `Analise`, `len({s["codigo"] for s in analise["sinais"]})` — todos os códigos que o modelo propôs para aquela reclamação, válidos ou não, sem deduplicar entre reclamações.

### Ranking de produtos: agrupamento por texto literal, não normalizado

`produto` vem do modelo "como leu, sem julgamento" (AD-21) — `agregacao.py` não deve normalizar case/acentuação para decidir se dois produtos são "o mesmo" no ranking (isso seria o tipo de julgamento que AD-21 proíbe fazer sobre o texto livre). Só a checagem "é genérico" usa a normalização de `catalogo.nao_nomeia_produto` (NFC, lower, plural simples) porque essa normalização já existe e é especificamente sobre a lista fechada de `TERMOS_GENERICOS`, não sobre o produto em geral. Duas entradas como `"Celular"` e `"celular"` viram duas linhas distintas no ranking nesta story — não há AC pedindo o contrário, e a base sintética não expõe esse caso.

### O que esta story NÃO faz

**Não escreve `caminho_html`.** Isso é Story 2.6.
**Não decide `na_fila`.** Já veio de `pontuar` (Story 2.1) — `agregar` só filtra e ordena o que já está marcado (AD-19, AC8).
**Não toca `main.py`, `relatorio.py`, `templates/`.** Ver seção acima sobre `main.py`.
**Não recalcula pontos nem motivos.** Só lê `pontuacoes` para montar a fila.

### Estrutura de arquivos

```text
plataforma/
  agregacao.py           # NOVO — agregar
  grafo.py                # UPDATE — nó "agregar", aresta final pontuar -> agregar -> END
tests/
  test_agregacao.py        # NOVO
  test_grafo.py             # UPDATE — nó "agregar" nos testes de introspecção
  test_import_sem_credencial.py  # UPDATE — "plataforma.agregacao" em MODULOS
```

**Não criar nesta story:** `relatorio.py`, `main.py` (já existe, não tocar), `templates/`.

**Não tocar:** `plataforma/ingestao.py`, `plataforma/config.py`, `plataforma/evidencia.py`, `plataforma/analise.py`, `plataforma/pontuacao.py`, `plataforma/catalogo.py`, `plataforma/estado.py` (já tem `Agregados`, `ItemRanking`, `DistribuicaoSentimento` completos desde a Story 1.1/1.6 — conferir contra `test_contrato.py` antes de assumir que falta campo), `docs/`, `baseline.py`, `classificador.py`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-7** | `agregacao.py` não importa `google.genai` |
| **AD-12** | Função pura sobre `Estado` fabricado à mão; única leitura externa é o relógio do sistema para `data_execucao`, sem rede |
| **AD-19** | `agregar` é o único nó que escreve `agregados`; não decide `na_fila` |
| **AD-20** | `Agregados` já é `TypedDict` desde `estado.py` — `agregar` só instancia, não redefine |
| **AD-21** | Marcação de genérico é feita em `agregar`, lendo `catalogo.TERMOS_GENERICOS` via `nao_nomeia_produto`, nunca pelo modelo |
| **AD-22** | `Agregados` carrega os números prontos; o template (Story 2.3+) só exibe, não soma nem divide |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2] — ACs originais
- [Source: plataforma/estado.py#Agregados, ItemRanking, DistribuicaoSentimento] — contrato já completo, ratificado contra `test_contrato.py`
- [Source: plataforma/catalogo.py#nao_nomeia_produto, TERMOS_GENERICOS] — reaproveitar, não reimplementar
- [Source: main.py#_contar_codigos_derrubados] — mesma semântica de contagem de códigos derrubados, duplicada conscientemente (ver Dev Notes)
- [Source: plataforma/pontuacao.py] — padrão de mapa `id -> Reclamacao` para juntar `Pontuacao` com dado de `Reclamacao`
- [Source: plataforma/grafo.py] — comentário em `_verificar_conservacao` e docstring de `construir_grafo` já anunciavam esta story como o próximo religamento
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/risk-signals.md#O que o gabarito revelou] — contexto de CM-1/CM-2/CM-3, não recalculado aqui, só a forma de `Agregados` que os carrega

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run pytest -q` → `154 passed` (baseline: 137 + 16 novos em `test_agregacao.py` + 1 novo em `test_grafo.py`).
- Sem achados de correção durante a implementação — o design já havia sido resolvido em detalhe nas Dev Notes durante `create-story`, então a primeira versão passou de primeira.

### Completion Notes List

- `codigos_propostos`/`codigos_derrubados` replicam a semântica de `main._contar_codigos_derrubados` (Story 1.7) conscientemente, sem importar `main.py` (evita inversão de dependência) — documentado nas Dev Notes da story.
- Import sem credencial testado localmente em `test_agregacao.py` (`test_import_agregacao_sem_credencial`), seguindo o precedente real da Story 2.1 (`pontuacao.py`) em vez de estender `test_import_sem_credencial.py::MODULOS` — as duas abordagens cobrem AD-7/AD-12 igualmente, optei por manter consistência com o padrão já estabelecido no código, não com o texto literal da task (atualizado no arquivo para refletir a decisão).
- `main.py` não foi tocado, como determinado nas Dev Notes — `_contar_codigos_derrubados` permanece duplicado ali; candidato a remoção numa story futura que religue `main.py` para ler de `agregados`.
- Nenhum desvio de design em relação ao que a story especificou para o cálculo de degradação, ranking, fila ou taxas.
- **Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor, 2026-08-09):** 7 patches aplicados — sentinela própria (não string literal) para o balde "não identificado" no ranking, evitando fusão com produto real de mesmo texto; `strip()` no rótulo do ranking; `pontuacao`/`agregacao` acrescentados a `test_import_sem_credencial.py::MODULOS`, fechando um gap de cobertura de AD-7 que também existia desde a Story 2.1; pluralização de `_motivo_degradacao`; três testes novos (`produto` vazio/espaços, `produto` literal `"não identificado"`, `analises=[]` degenerado) e um fortalecido (`data_execucao` agora confere dígitos, não só comprimento). 2 achados deferidos (`KeyError` cru em `_fila_ordenada` se id não casar — mesmo padrão pré-existente em `pontuacao.py`; ausência de teste de sincronia entre `agregacao._contar_codigos` e `main._contar_codigos_derrubados` — duplicação consciente, ver Dev Notes). 5 achados descartados por já estarem cobertos por invariantes de stories anteriores (AD-2, AD-6, AD-19, unicidade de id da ingestão, `Literal` imposto pelo `response_schema`). Suíte final: `uv run pytest -q` → `158 passed`.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/agregacao.py` | novo |
| `plataforma/grafo.py` | modificado |
| `tests/test_agregacao.py` | novo |
| `tests/test_grafo.py` | modificado |
| `tests/test_import_sem_credencial.py` | modificado (achado de revisão) |
