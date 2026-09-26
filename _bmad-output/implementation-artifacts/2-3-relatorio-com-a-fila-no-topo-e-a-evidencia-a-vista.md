---
baseline_commit: 'e663e9244dca32f95365c0ebd6657799716cf50d'
---

# Story 2.3: Relatório com a fila no topo e a evidência à vista

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a gestor,
I want abrir o arquivo e ver primeiro a fila de prioridade, com a frase do cliente em cada item,
so that eu responda *o que atendo primeiro* sem rolar a página nem clicar em nada.

## Acceptance Criteria

**AC1 — Um único `Environment` Jinja2, `autoescape=True` literal**

**Given** o módulo `plataforma/relatorio.py`
**When** o ambiente de template é construído
**Then** existe exatamente um `Environment` do Jinja2, criado nesse módulo, com `autoescape=True` literal
**And** `select_autoescape` não é usado — o seletor casaria `relatorio.html.j2` no `default=False` e deixaria o escape desligado
**And** nenhum outro módulo do pacote constrói um `Environment` (AD-10)

**AC2 — Fila é o primeiro conteúdo, ordem preservada**

**Given** o relatório renderizado
**When** ele é aberto no navegador
**Then** a fila de prioridade é o primeiro conteúdo, antes de qualquer agregado (FR-11)
**And** o item mais grave é o primeiro da fila — o template preserva a ordem que `agregar` produziu e não reordena (AD-19, AD-22)

**AC3 — Motivo visível, não em detalhe expansível**

**Given** um item da fila
**When** ele é renderizado
**Then** exibe seu `Motivo` — citação literal quando `origem = "sinal"`, rótulo estrutural quando `origem = "atributo"` — como conteúdo visível
**And** não como detalhe expansível, acordeão ou tooltip (FR-12, FR-9)

**AC4 — Template não deriva pertencimento a partir de `Reclamacao`**

**Given** o template
**When** suas condicionais são lidas
**Then** nenhuma delas consulta `Reclamacao` para descobrir por que um item está na fila
**And** `reclamacoes` é lido apenas para exibir empresa, título e data (AD-4)

**AC5 — Texto do cliente escapado**

**Given** uma reclamação cujo texto contém caracteres de marcação HTML
**When** ela é renderizada
**Then** aparece escapada e não altera a estrutura da página

**AC6 — pt-BR**

**Given** o relatório renderizado
**When** ele é lido
**Then** rótulos, categorias e números estão em português do Brasil, com a convenção numérica local (FR-17)

**AC7 — Fila vazia é informação, não erro**

**Given** uma fila vazia porque nenhuma reclamação atingiu o corte
**When** o relatório é renderizado
**Then** a fila aparece declarada como vazia — fila vazia é informação, não erro (§6 do PRD)

## Tasks / Subtasks

- [x] **Task 1 — Criar `plataforma/relatorio.py`** (AC: 1, 2, 3, 4, 6, 7)
  - [x] Módulo-nível: `_ENVIRONMENT = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=True)` — `autoescape=True` literal, nunca `select_autoescape(...)` (AD-10)
  - [x] `_data_br(iso: str) -> str`: `"AAAA-MM-DD"` → `"DD/MM/AAAA"` por split em `"-"` e reordenação — sem biblioteca de data, é troca de posição de três strings (FR-17)
  - [x] `_itens_fila(fila: list[str], pontuacoes_por_id: dict, reclamacoes_por_id: dict) -> list[dict]`: para cada `id` em `agregados["fila"]`, **na ordem dada, sem reordenar** (AD-19, AD-22), monta um dict de exibição com `id`, `empresa`, `titulo`, `data` (via `_data_br`) — de `Reclamacao` — e `pontos`, `motivos` — de `Pontuacao`. Esta função é quem decide o que o template recebe pronto; o template não vai consultar `Reclamacao` para nada além dos três campos de exibição (AD-4)
  - [x] `renderizar(estado: Estado) -> str`: lê `estado["agregados"]["fila"]`, `estado["pontuacoes"]`, `estado["reclamacoes"]`; monta os mapas `id -> Pontuacao` e `id -> Reclamacao` (mesmo padrão de `pontuacao.py`/`agregacao.py`); chama `_itens_fila`; renderiza `relatorio.html.j2` com `itens_fila=...`; devolve a string HTML
  - [x] **Esta story não escreve arquivo em disco nem decide nome de saída (FR-1b é Story 2.6).** `renderizar` devolve a string; não grava, não recebe `caminho`, não é ainda um nó do grafo
  - [x] Docstring de módulo: por que só um `Environment`, por que `_itens_fila` pré-monta os dados fora do template (AD-4), por que esta story não grava arquivo
  - [x] Imports: `pathlib.Path`, `jinja2.Environment`, `jinja2.FileSystemLoader`, `plataforma.estado` (`Estado`, `Pontuacao`, `Reclamacao`) — sem `google.genai`, sem outro filtro de `plataforma/`
  - [x] `jinja2==3.1.6` acrescentado a `pyproject.toml` (`uv add jinja2==3.1.6`) — era dependência ausente, prevista na spine (Stack)

- [x] **Task 2 — Criar `plataforma/templates/relatorio.html.j2`** (AC: 2, 3, 4, 5, 6, 7)
  - [x] `<!doctype html>`, `<html lang="pt-BR">`, `<meta charset="utf-8">` — nada de `<script src>`/`<link href>` externo (AD-11, antecipa 2.4/2.6, mas já vale aqui)
  - [x] Seção da fila é o **primeiro** elemento do `<body>` (AC2/FR-11) — nenhuma outra seção existe ainda nesta story (ranking e sentimento são Story 2.4; cabeçalho de confiabilidade é Story 2.5)
  - [x] Itera `itens_fila` **na ordem recebida** — nenhum `sort`, `|sort`, `|dictsort` no template (AC2)
  - [x] Para cada item: empresa, título, data (pt-BR), pontos — texto livre do consumidor (`titulo`) passa pelo autoescape padrão do `Environment`, nenhum filtro `|safe` em campo de dado (AC5)
  - [x] Para cada `Motivo` do item: `{% if motivo.origem == "sinal" %}` exibe `motivo.rotulo` (código) e `motivo.citacao` entre aspas; `{% else %}` exibe só `motivo.rotulo`. Nenhuma condicional consulta `reclamacao.status`, `reclamacao.categoria` ou qualquer campo de `Reclamacao` para decidir isso — a decisão já veio pronta em `motivo.origem` (AD-4)
  - [x] Motivo é `<li>` sempre visível — nenhum `<details>`, `<summary>`, `aria-expanded`, classe de acordeão nem `title=` de tooltip (AC3)
  - [x] `{% if itens_fila %}` ... `{% else %}` parágrafo declarando a fila vazia ("Nenhuma reclamação atingiu o corte de prioridade nesta execução.") `{% endif %}` (AC7)
  - [x] Rótulos da seção em português ("Fila de prioridade", "ponto(s)")

- [x] **Task 3 — Criar `tests/test_relatorio.py`** (AC: 1, 2, 3, 4, 5, 6, 7)
  - [x] AC1: `relatorio._ENVIRONMENT` é instância de `jinja2.Environment`; `relatorio._ENVIRONMENT.autoescape is True`
  - [x] AC2: fixture com 3 itens na fila em ordem não-óbvia (`fila=["R3", "R1", "R2"]`); verifica posição relativa dos títulos no HTML (`str.index`) — trava que o template não reordena
  - [x] AC2: seção da fila é o primeiro elemento do `<body>`
  - [x] AC3: `Motivo` de origem `sinal` → citação aparece visível; origem `atributo` → só o rótulo aparece
  - [x] AC3: HTML não contém `<details`, `<summary`, `aria-expanded` nem `title="` no bloco de motivos
  - [x] AC4: lê o texto-fonte do template e confirma ausência de `reclamacao.status`/`reclamacao.categoria`/`item.status`/`item.categoria`
  - [x] AC5: `titulo='<script>alert(1)</script>'` → HTML contém `&lt;script&gt;`, não a tag crua
  - [x] AC6: `_data_br("2026-01-05") == "05/01/2026"`, testado direto e via `renderizar`
  - [x] AC7: `fila=[]` → HTML contém a mensagem de fila vazia
  - [x] Fixture reaproveita o padrão de builders de `tests/test_agregacao.py`
  - [x] `test_import_relatorio_sem_credencial`: import sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` funciona
  - [x] `uv run pytest -q` → **169 passed** (158 pré-existentes + 11 novos em `test_relatorio.py`)

### Review Findings

- [x] [Review][Patch] `plataforma.relatorio` ausente de `tests/test_import_sem_credencial.py::MODULOS` — cobertura de AD-7/AD-12 falha silenciosamente para este módulo, mesmo gap já corrigido para `pontuacao`/`agregacao` na Story 2.2 [tests/test_import_sem_credencial.py]
- [x] [Review][Patch] `_data_br` faz unpack cru de `"AAAA-MM-DD".split("-")` sem validar formato — string fora do padrão (ex.: com componente de hora) levanta erro de unpack sem mensagem nomeando o valor observado [plataforma/relatorio.py:_data_br]
- [x] [Review][Patch] `jinja2==3.1.6` fixado com igualdade exata, único caso no `pyproject.toml` — todo outro dependency usa piso `>=` [pyproject.toml]
- [x] [Review][Patch] `Environment` sem `trim_blocks`/`lstrip_blocks` — linhas de `{% if %}`/`{% for %}`/`{% endif %}` deixam espaço em branco no HTML renderizado, e o próprio teste já precisa de `.strip()` para compensar [plataforma/relatorio.py:_ENVIRONMENT]
- [x] [Review][Patch] Sem teste para item da fila com `motivos=[]` (lista vazia é valor permitido pelo contrato) [tests/test_relatorio.py]
- [x] [Review][Patch] Escape de HTML testado só em `titulo`; `motivo.citacao` — texto literal do cliente, o campo mais provável de carregar marcação — nunca testado isoladamente [tests/test_relatorio.py]
- [x] [Review][Patch] Sem teste com motivos de origem mista (`sinal` e `atributo`) no mesmo item — cada teste isola um tipo só [tests/test_relatorio.py]
- [x] [Review][Patch] `_itens_fila` devolve `list[dict]` solto em vez de `TypedDict`, único ponto do módulo fora do padrão que `estado.py` estabelece para todo o pacote [plataforma/relatorio.py:_itens_fila]
- [x] [Review][Patch] `sprint-status.yaml.last_updated` mudou de `"2026-08-09"` para `"2026-08-09 12:05"` — todo registro anterior do arquivo usa data pura, sem hora [_bmad-output/implementation-artifacts/sprint-status.yaml]
- [x] [Review][Defer] `_itens_fila` faz `pontuacoes_por_id[id_]`/`reclamacoes_por_id[id_]` sem guarda contra id ausente ou duplicado — deferred, mesmo padrão já aceito em `agregacao._fila_ordenada` (Story 2.2), sustentado pela mesma conservação AD-6/AD-19 [plataforma/relatorio.py:_itens_fila]

**Achados descartados (falso positivo / já coberto em outra camada):**
- Template renderizaria `"None"` se um `Motivo` de `origem="sinal"` tivesse `citacao=None` — impossível por construção: `Sinal.citacao` é `str` não-opcional em `estado.py`, e `pontuacao.py` só cria `Motivo(origem="sinal", citacao=sinal["citacao"], ...)` para `Sinal` com `valida=True`, cuja `citacao` já passou pela verificação de piso de 5 palavras (AD-1).
- Aspas tipográficas fixas (`“…”`) ao redor da citação sem tratamento de aspas aninhadas — cosmético, nenhuma AC exige, sem quebra funcional.
- Chave `"id"` no dict de `_itens_fila` nunca lida pelo template — campo morto inofensivo, não é violação de AD-4 (a restrição é sobre o que o *template* lê de `Reclamacao`, não sobre o que o dict auxiliar carrega).

## Dev Notes

### Por que esta story NÃO toca `grafo.py` nem `main.py`

Diferente de 2.1 (`pontuar`) e 2.2 (`agregar`), que religaram `grafo.py` na mesma story em que criaram o nó, `relatorio.py` desta story **não vira nó do grafo ainda**. O motivo: `Estado.caminho_html` só existe para carregar o caminho do arquivo **escrito em disco**, e escrever, nomear e proteger contra sobrescrita é FR-1b — explicitamente atribuído à Story 2.6 no `epics.md` ("FR-1b fica na Story 2.6, onde existe relatório para escrever"). Não há campo no contrato de estado para a *string* HTML em si (só para o caminho do arquivo final), então um nó "renderizar" que não escreve arquivo não teria o que retornar como delta de `Estado` — e inventar um campo novo em `estado.py` para isso não foi pedido nem está nas ACs desta story.

`renderizar(estado: Estado) -> str` é portanto uma função pura que devolve a string HTML, testável sozinha com um `Estado` fabricado à mão — sem grafo, sem `.invoke()`, sem I/O. As Stories 2.4 e 2.5 estendem o mesmo template e a mesma função (mais seções, mais contexto), e a Story 2.6 é quem finalmente cria o nó do grafo que chama `relatorio.renderizar`, grava o arquivo com o nome validado e popula `caminho_html`.

**Não criar nó `renderizar` em `grafo.py` nesta story. Não tocar `main.py`.**

### `agregados["fila"]` já vem ordenada — não ordenar de novo

`agregacao._fila_ordenada` (Story 2.2) já resolveu a ordem total e determinística (pontos desc, data asc, id asc) e gravou o resultado em `Agregados.fila` como lista de ids. `_itens_fila` desta story **itera essa lista na ordem dada**, sem `sorted()`/`.sort()` — reordenar aqui duplicaria uma decisão que já tem dono (AD-19: `agregar` é quem decide a ordem da fila; `relatorio.py` só exibe).

### `Motivo` já vem pronto de `pontuacao.py` — o template só decide layout por `origem`

`Pontuacao.motivos` (Story 2.1) já contém, para cada item, a lista de `Motivo` com `origem` resolvida (`"sinal"` com `citacao` não-nula, `"atributo"` com `citacao=None` e `rotulo` nomeando a regra estrutural, ex. `"Status: Respondida (-1)"`). O template só faz `{% if motivo.origem == "sinal" %}` — não recalcula nada, não consulta `Reclamacao.status` para decidir se é atributo (essa é exatamente a duplicação que AD-4 proíbe).

### Autoescape: `autoescape=True` literal, não `select_autoescape`

Já era regra em AD-10 desde a spine (repetida aqui porque esta é a story que finalmente instancia o `Environment`, pela primeira vez no pacote). `select_autoescape()` sem argumentos casa por extensão de arquivo — as extensões padrão são `html`, `htm`, `xml`; `relatorio.html.j2` termina em `.j2`, não bate em nenhuma delas, e cairia no branch `default=False` da função, desligando o escape justo na linha que parece a proteção certa. `autoescape=True` é booleano incondicional — sempre liga, para qualquer template carregado por este `Environment`. Único `Environment` do pacote inteiro; nenhum outro módulo cria um segundo.

### Formatação de data: sem biblioteca, é troca de posição

`Reclamacao.data` já está em ISO-8601 desde a ingestão (Story 1.3). `_data_br` é `"AAAA-MM-DD".split("-")` reordenado para `"DD/MM/AAAA"` — três strings, nenhuma dependência nova, nenhum `datetime.strptime`. Não introduzir `babel` nem formatação de locale para isto — é troca de posição, não parsing.

### O que esta story NÃO faz

**Não escreve arquivo.** `renderizar` devolve `str`; gravação é FR-1b, Story 2.6.
**Não renderiza ranking de produtos nem distribuição de sentimento.** Story 2.4.
**Não renderiza cabeçalho de confiabilidade/degradação.** Story 2.5.
**Não toca `grafo.py`, `main.py`.** Ver seção acima.
**Não introduz nova chave em `Estado`** — `renderizar` só lê `agregados`, `pontuacoes`, `reclamacoes`, já existentes.

### Estrutura de arquivos

```text
plataforma/
  relatorio.py                    # NOVO — renderizar, _itens_fila, _data_br, _ENVIRONMENT
  templates/
    relatorio.html.j2             # NOVO — só a seção da fila por enquanto
tests/
  test_relatorio.py                # NOVO
```

**Não criar/tocar nesta story:** `plataforma/grafo.py`, `main.py`, `plataforma/estado.py` (contrato já completo — `Agregados`, `Pontuacao`, `Motivo`, `Reclamacao` já têm todos os campos que esta story lê), `plataforma/agregacao.py`, `plataforma/pontuacao.py`, `plataforma/catalogo.py`, `plataforma/ingestao.py`, `plataforma/analise.py`, `plataforma/evidencia.py`, `plataforma/config.py`, `docs/`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-4** | `_itens_fila` pré-monta empresa/título/data a partir de `Reclamacao`; nenhuma condicional do template deriva "por que está na fila" a partir dela — só de `Motivo`, que já veio pronto de `pontuar` |
| **AD-7** | `relatorio.py` não importa `google.genai` — só `jinja2` e `plataforma.estado` |
| **AD-10** | Único `Environment`, `autoescape=True` literal, criado em `relatorio.py` |
| **AD-11** | Template sem `<script src>`/`<link href>` externo (vale desde já, mesmo sem gráfico ainda) |
| **AD-12** | `renderizar` é função pura sobre `Estado` fabricado à mão; nenhum teste faz chamada de rede |
| **AD-19/AD-22** | `_itens_fila` preserva a ordem de `agregados["fila"]`; não reordena, não recalcula pontos nem pertencimento |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3] — ACs originais
- [Source: plataforma/estado.py#Agregados, Pontuacao, Motivo, Reclamacao] — contrato já completo, nenhum campo novo necessário
- [Source: plataforma/agregacao.py#_fila_ordenada] — `agregados["fila"]` já é a ordem final; não recalcular
- [Source: plataforma/pontuacao.py#pontuar] — forma de `Motivo`, incluindo o texto de exemplo do rótulo de atributo (`"Status: Respondida (-1)"`)
- [Source: tests/test_agregacao.py] — padrão de builders (`reclamacao(...)`, `pontuacao(...)`) a reaproveitar em `test_relatorio.py`
- [Source: _bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md#AD-10, AD-4, AD-11] — regras do `Environment` único e da proveniência do `Motivo`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run pytest -q` → `169 passed` (baseline: 158 + 11 novos em `test_relatorio.py`).
- Único ajuste durante o desenvolvimento: `jinja2` não estava instalado (`ModuleNotFoundError`); acrescentado via `uv add jinja2==3.1.6`, versão fixada pela spine.
- Um teste precisou de ajuste após primeira falha: `test_fila_renderizada_preserva_ordem_de_agregados_nao_reordena` comparava `html.index("R3")` etc., mas o `id` da reclamação não é exibido no template (só empresa/título/data/pontos, por design de AD-4) — corrigido para comparar pelos títulos distintos de cada reclamação.

### Completion Notes List

- `plataforma/relatorio.py` criado com `_ENVIRONMENT` único (`autoescape=True` literal), `_data_br`, `_itens_fila` e `renderizar(estado) -> str`. Não escreve arquivo, não é nó do grafo — decisão de escopo documentada nas Dev Notes da story (FR-1b/AD-15 é Story 2.6).
- `plataforma/templates/relatorio.html.j2` criado só com a seção da fila de prioridade; motivo de origem `sinal` mostra código + citação, origem `atributo` mostra só o rótulo — nenhum acordeão/tooltip.
- `grafo.py` e `main.py` **não foram tocados**, conforme escopo da story.
- Nenhum desvio de design em relação ao que a story especificou.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/relatorio.py` | novo |
| `plataforma/templates/relatorio.html.j2` | novo |
| `tests/test_relatorio.py` | novo |
| `tests/test_import_sem_credencial.py` | modificado (achado de revisão) |
| `pyproject.toml` | modificado (dependência `jinja2>=3.1.6`) |
| `uv.lock` | modificado (lockfile) |

## Change Log

- 2026-08-09: Implementação completa da Story 2.3 — `relatorio.py`, template da fila, testes, dependência `jinja2` instalada. `169 passed`.
- 2026-08-09: Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Acceptance Auditor: 0 violações, todas as 7 ACs conformes. 9 patches aplicados — `plataforma.relatorio` em `MODULOS`; `_data_br` valida formato ISO antes do unpack; `jinja2` de `==3.1.6` para `>=3.1.6`; `trim_blocks`/`lstrip_blocks` no `Environment`; `ItemFila` como `TypedDict`; `sprint-status.yaml.last_updated` revertido a data pura; 3 testes novos (`motivos=[]`, escape de `citacao`, origem mista). 1 achado deferido (`_itens_fila` sem guarda contra id ausente/duplicado — mesmo padrão já aceito em `agregacao._fila_ordenada` desde a Story 2.2). 3 achados descartados por já cobertos por invariantes anteriores (AD-1, AD-3) ou por serem cosméticos sem AC associada. Suíte final: `uv run pytest -q` → `172 passed`.
