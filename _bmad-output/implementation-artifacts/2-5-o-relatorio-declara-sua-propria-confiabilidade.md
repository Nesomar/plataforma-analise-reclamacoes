---
baseline_commit: 'e663e9244dca32f95365c0ebd6657799716cf50d'
---

# Story 2.5: O relatório declara sua própria confiabilidade

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a gestor,
I want que o arquivo me diga em que execução ele nasceu e se ela foi confiável,
so that eu não trate um relatório sobre metade da base como se fosse sobre a base inteira.

## Acceptance Criteria

**AC1 — Cabeçalho informa data, analisadas e não analisadas**

**Given** o relatório renderizado
**When** seu cabeçalho é lido
**Then** informa a data da execução, o total de reclamações analisadas e o total não analisado por falha (FR-14)
**And** esses números vêm de `Agregados`; o template não soma, não divide e não compara com limiar (AD-22)

**AC2 — Marca de degradação visível quando `degradado=True`**

**Given** uma execução com o indicador de degradação verdadeiro
**When** o relatório é renderizado
**Then** carrega marca de degradação visível ao leitor no próprio arquivo
**And** essa marca não depende de o leitor procurar por ela (NFR-6)

**AC3 — Execução limpa não exibe marca de degradação**

**Given** uma execução limpa
**When** o relatório é renderizado
**Then** nenhuma marca de degradação aparece — uma execução confiável e uma degradada não têm a mesma aparência

**AC4 — Declaração de heurística de engenharia, não parecer jurídico**

**Given** o relatório renderizado
**When** ele é lido
**Then** declara em texto visível que a classificação de risco é heurística de engenharia e não parecer jurídico (FR-16)
**And** essa declaração recebe o mesmo tratamento estrutural das ressalvas de FR-18 (AD-14)

## Tasks / Subtasks

- [x] **Task 1 — Estender `plataforma/relatorio.py`** (AC: 1, 2, 3, 5)
  - [x] `class Cabecalho(TypedDict)`: `data_execucao`, `analisadas`, `nao_analisadas`, `degradado`, `motivo_degradacao`
  - [x] `_cabecalho(agregados) -> Cabecalho`: repassa contagens/degradação direto; converte data via `_data_br` reaproveitado
  - [x] `renderizar(estado)` passa `cabecalho=_cabecalho(agregados)` ao template
  - [x] Nenhum texto de ressalva/declaração em Python
  - [x] Import adicional: `plataforma.estado.Agregados`

- [x] **Task 2 — Estender `plataforma/templates/relatorio.html.j2`** (AC: 1, 2, 3, 4)
  - [x] Nova `<section id="confiabilidade">` entre `#fila-prioridade` e `#distribuicao-sentimento`
  - [x] Parágrafo com data/contagens
  - [x] `{% if cabecalho.degradado %}` parágrafo `class="degradado"` sem `{% else %}`
  - [x] Parágrafo fixo `<p class="ressalva">` com a declaração de FR-16
  - [x] Nenhuma aritmética no template envolvendo `cabecalho`/`agregados`

- [x] **Task 3 — Estender `tests/test_relatorio.py`** (AC: 1, 2, 3, 4)
  - [x] `_cabecalho`: conversão de data e repasse de contagens/degradação testados
  - [x] Marca de degradação visível quando `degradado=True`; ausente quando `False`
  - [x] Data e contagens aparecem no HTML
  - [x] Declaração de heurística visível no HTML e literal no `.j2`
  - [x] Estrutural: `#confiabilidade` entre `#fila-prioridade` e `#distribuicao-sentimento`
  - [x] Builders `agregados(...)`/`estado(...)` estendidos com `nao_analisadas`, `degradado`, `motivo_degradacao`, `data_execucao`, retrocompatíveis
  - [x] `uv run python -m pytest -q` (via PowerShell) → **192 passed** (186 pré-existentes + 6 novos)

### Review Findings

- [x] [Review][Patch] `test_cabecalho_exibe_data_e_contagens_no_html` verifica `"2" in html` para provar que `nao_analisadas=2` renderizou, mas `"2026-03-10"` já contém `"2"` — a asserção passa mesmo se `nao_analisadas` nunca aparecer [tests/test_relatorio.py]
- [x] [Review][Patch] Sem teste estrutural confirmando que a declaração de FR-16 está dentro de `<p class="ressalva">` e dentro de `#confiabilidade` — os testes atuais só buscam a substring solta em qualquer lugar do HTML/template [tests/test_relatorio.py]
- [x] [Review][Patch] Texto da declaração de FR-16 não começa com `"Ressalva:"`, quebrando a convenção que toda outra ressalva do template segue (`"Ressalva: este gráfico..."`, `"Ressalva: volume não equivale..."`) [plataforma/templates/relatorio.html.j2]
- [x] [Review][Patch] Sem teste para a mensagem de degradação com as duas condições concatenadas por `"; "` (`agregacao._motivo_degradacao`) — só o caso de condição única foi exercitado no nível de `relatorio.py` [tests/test_relatorio.py]
- [x] [Review][Patch] Sem guarda estrutural contra aritmética/comparação envolvendo `cabecalho`/`agregados` no template (AD-22) — o mesmo padrão de teste estrutural já existe para AD-4 (`test_template_nao_referencia_campos_de_reclamacao_fora_de_exibicao`), mas não para AD-22 [tests/test_relatorio.py]
- [x] [Review][Patch] Sem teste de escape para `cabecalho.motivo_degradacao` (texto livre montado em `agregacao.py`) — mesmo padrão de teste já existe para `titulo` e `citacao` [tests/test_relatorio.py]
- [x] [Review][Patch] Pluralização incorreta em pt-BR quando `analisadas`/`nao_analisadas` == 1 (produziria "1 reclamações analisadas") — `agregacao._motivo_degradacao` já resolve esse mesmo problema de pluralização em outro lugar do pacote, este texto não segue o precedente [plataforma/templates/relatorio.html.j2]

**Achados descartados (falso positivo / já coberto em outra camada / fora de escopo):**
- `degradado=True` com `motivo_degradacao=None` renderizaria `"Execução degradada: None"` — impossível por construção: `agregacao._motivo_degradacao` só devolve `None` quando nem `degradado_falha` nem `degradado_derrubada` dispararam, e `degradado` é exatamente `degradado_falha or degradado_derrubada` (mesmo módulo, mesma chamada). Os dois campos nascem juntos e nunca divergem.
- Classe `class="degradado"` sem folha de estilo (nenhuma cor/destaque visual) — nenhuma AC exige diferenciação visual, mesmo precedente já descartado na Story 2.4.
- Docstring do módulo de `test_relatorio.py` não lista a nova cobertura de cabeçalho/degradação/heurística — cosmético, não exigido.
- Documento acumula múltiplos `<h1>` (um por seção) — padrão pré-existente desde a Story 2.4, nenhuma AC trata de estrutura semântica de cabeçalhos HTML.
- Diff construído a partir de snapshot em scratchpad em vez de histórico git — nota sobre o processo de revisão desta sessão, não defeito de código (o snapshot foi verificado manualmente contra o conteúdo real das Stories 2.3/2.4).
- `Cabecalho` como `TypedDict` para um repasse simples — consistente com o padrão já estabelecido no mesmo módulo (`ItemFila`, `BarraSentimento`, `BarraRanking`), não é cerimônia isolada.
- Builders de teste com muitos kwargs opcionais sujeitos a erro posicional — nit de fixture de teste, sem risco de produção.

## Dev Notes

### Por que a seção de confiabilidade vai DEPOIS da fila, não literalmente no topo

O nome "cabeçalho" na AC (`"seu cabeçalho é lido"`) sugere topo do documento, mas **FR-11 já é regra travada por teste desde a Story 2.3**: "a fila de prioridade é o primeiro conteúdo do relatório, antes de qualquer agregado" (`test_secao_da_fila_e_o_primeiro_conteudo_do_body` verifica isso literalmente — a seção da fila é o primeiro filho de `<body>`). Data de execução, contagens e degradação vêm de `Agregados`, então por definição de FR-11 elas não podem preceder a fila. A resolução adotada: a seção de confiabilidade (`#confiabilidade`) é a **segunda** seção do documento — logo depois da fila, antes dos gráficos. Isso cumpre FR-11 ao pé da letra e ainda dá à informação de confiabilidade a posição mais alta possível sem violar a story anterior. Não é ambiguidade a resolver durante a implementação — é uma decisão já tomada aqui; a Task 2 e o teste estrutural da Task 3 travam essa ordem.

### Texto sugerido para a declaração de FR-16 (AD-14)

Nenhuma AC prescreve o texto exato, só que ele "declara... heurística de engenharia e não parecer jurídico" e recebe "o mesmo tratamento estrutural das ressalvas de FR-18". Sugestão, no mesmo tom das outras ressalvas já escritas (Story 2.4):

> "Esta classificação de risco é uma heurística de engenharia baseada em sinais textuais — não constitui parecer jurídico nem substitui avaliação humana antes de qualquer decisão."

Usar `<p class="ressalva">`, mesma classe já usada nas seções de gráfico — consistência visual/estrutural, não uma classe nova por seção.

### `motivo_degradacao` já vem pronto de `agregacao.py` — não reconstruir o texto aqui

`Agregados.motivo_degradacao` (Story 2.2, `agregacao._motivo_degradacao`) já monta a frase nomeando qual condição de NFR-6 disparou, com os números observados (ex.: `"mais de 10% não analisadas (6/50)"` ou `"todos os 3 códigos de sinal propostos foram derrubados"`, ou as duas concatenadas por `"; "`). `_cabecalho` só repassa essa string; o template só a exibe dentro do `{% if cabecalho.degradado %}`. Nenhuma lógica de threshold, nenhuma reconstrução de frase.

### Diferença entre esta seção e as ressalvas de gráfico (Story 2.4)

As ressalvas de FR-18 (sentimento/ranking) são **sempre visíveis**, textos fixos que não dependem de dado nenhum. A marca de degradação (AC2/AC3) é **condicional** — só aparece quando `degradado=True`. Não confundir os dois padrões: a declaração de FR-16 (AC4) segue o padrão das ressalvas (sempre visível, incondicional); a marca de degradação segue um padrão novo (condicional, `{% if %}` sem `{% else %}`).

### O que esta story NÃO faz

**Não escreve arquivo, não toca `grafo.py`/`main.py`.** Mesmo raciocínio das Stories 2.3/2.4 — FR-1b é Story 2.6.
**Não recalcula degradação.** `agregados["degradado"]`/`agregados["motivo_degradacao"]` já vêm resolvidos de `agregar` (Story 2.2, AD-19/AD-22) — esta story só exibe.
**Não introduz nova chave em `Estado`.** `_cabecalho` só lê campos de `Agregados` já existentes desde a Story 1.1/2.2.
**Não move nem reordena as seções já existentes** (`#fila-prioridade`, `#distribuicao-sentimento`, `#ranking-produtos`) — só insere `#confiabilidade` entre a primeira e a segunda.

### Estrutura de arquivos

```text
plataforma/
  relatorio.py                    # UPDATE — Cabecalho, _cabecalho, renderizar estendido
  templates/
    relatorio.html.j2             # UPDATE — nova seção #confiabilidade
tests/
  test_relatorio.py                # UPDATE — testes de _cabecalho e da seção nova
```

**Não criar/tocar nesta story:** `plataforma/grafo.py`, `main.py`, `plataforma/estado.py` (contrato já completo — `Agregados.data_execucao/analisadas/nao_analisadas/degradado/motivo_degradacao` já existem desde a Story 1.1/2.2), `plataforma/agregacao.py`, `plataforma/pontuacao.py`, `plataforma/catalogo.py`, `docs/`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-10** | Declaração de FR-16 e texto do cabeçalho de contagem são literais do `.j2`; `_cabecalho` só repassa dado, nunca prosa |
| **AD-14** | Declaração de FR-16 recebe o mesmo tratamento estrutural das ressalvas de FR-18 (`<p class="ressalva">`, dentro da seção correspondente) |
| **AD-19/AD-22** | `_cabecalho` só repassa `analisadas`/`nao_analisadas`/`degradado`/`motivo_degradacao` já calculados por `agregar`; nenhuma soma, divisão ou comparação de limiar acontece em `relatorio.py` ou no template |
| **AD-7/AD-12** | `relatorio.py` continua sem `google.genai`; `_cabecalho` é função pura, testável com `Agregados` fabricado à mão |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5] — ACs originais
- [Source: plataforma/estado.py#Agregados] — `data_execucao`, `analisadas`, `nao_analisadas`, `degradado`, `motivo_degradacao` já completos
- [Source: plataforma/agregacao.py#_motivo_degradacao] — quem monta a frase de degradação; não reconstruir
- [Source: plataforma/relatorio.py, plataforma/templates/relatorio.html.j2] — código real das Stories 2.3/2.4: `_data_br` (reaproveitar), `_ENVIRONMENT`, padrão `<p class="ressalva">` já estabelecido
- [Source: tests/test_relatorio.py] — builders (`reclamacao`, `pontuacao`, `agregados`, `estado`) a estender, não recriar
- [Source: _bmad-output/implementation-artifacts/2-4-graficos-embutidos-com-a-ressalva-ao-lado.md#Dev Agent Record] — revisão adversarial anterior; nenhum achado dela é reaberto aqui
- [Source: _bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md#AD-10, AD-14, AD-22] — regras de texto no template e de exibição sem cálculo

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run python -m pytest -q` (via PowerShell) → `192 passed` (baseline: 186 + 6 novos em `test_relatorio.py`). `rtk`/bash seguem bloqueados por política de Controle de Aplicativo do Windows nesta sessão (mesmo bloqueio da Story 2.4).
- Sem falhas de implementação — testes passaram de primeira.

### Completion Notes List

- `plataforma/relatorio.py` ganhou `Cabecalho` (`TypedDict`), `_cabecalho`, e `renderizar` passa `cabecalho=...` ao template.
- `plataforma/templates/relatorio.html.j2` ganhou `<section id="confiabilidade">` entre a fila e o gráfico de sentimento, com contagens, marca condicional de degradação e a declaração de heurística de engenharia.
- Decisão de posicionamento (seção de confiabilidade depois da fila, não antes) documentada nas Dev Notes para não violar FR-11 já travado por teste desde a Story 2.3.
- `grafo.py`/`main.py` não tocados.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/relatorio.py` | modificado |
| `plataforma/templates/relatorio.html.j2` | modificado |
| `tests/test_relatorio.py` | modificado |

## Change Log

- 2026-08-09: Implementação completa da Story 2.5 — cabeçalho de confiabilidade (data, contagens, degradação condicional, declaração de heurística), testes estendidos. `192 passed`.
- 2026-08-09: Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Acceptance Auditor: 0 violações, todas as 4 ACs conformes. 7 patches aplicados — pluralização pt-BR correta para `analisadas`/`nao_analisadas` (`_contagem_pt_br`, novo em `relatorio.py`); declaração de FR-16 prefixada com "Ressalva:"; 5 testes novos (asserção fraca corrigida, posicionamento estrutural da ressalva, mensagem de degradação com duas condições, escape de `motivo_degradacao`, guarda contra aritmética/comparação no template para AD-22). 7 achados descartados por impossíveis por construção, fora de escopo de AC, ou nits de teste/estilo já aceitos em stories anteriores. Suíte final: `uv run python -m pytest -q` → `197 passed`.
