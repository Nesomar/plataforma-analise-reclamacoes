---
baseline_commit: 'e663e9244dca32f95365c0ebd6657799716cf50d'
---

# Story 2.4: Gráficos embutidos com a ressalva ao lado

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a gestor,
I want ver a distribuição de sentimento e o ranking de produtos como gráfico, com a limitação de cada leitura escrita ao lado,
so that eu não dê aos dois a mesma autoridade que dou à fila.

## Acceptance Criteria

**AC1 — Gráficos são `<svg>` inline, sem biblioteca externa**

**Given** o relatório renderizado
**When** os gráficos são inspecionados
**Then** são `<svg>` escrito no próprio template
**And** não há biblioteca de plotagem, `<script src>` nem `<link href>` externo (FR-15, AD-11)

**AC2 — Ressalva de sentimento ao lado do gráfico**

**Given** o gráfico de distribuição de sentimento
**When** ele é renderizado
**Then** carrega ao lado, no corpo do relatório, uma ressalva fixa nomeando o que limita essa leitura nesta base
**And** a ressalva é texto do template, não calculada em tempo de execução (FR-18, AD-14)

**AC3 — Ranking com ressalva, `não identificado` visível, genérico marcado**

**Given** o ranking de produtos
**When** ele é renderizado
**Then** carrega ao lado a ressalva de que volume não equivale a gravidade — o produto mais reclamado tende a ser o mais vendido (FR-13)
**And** a linha `não identificado` aparece visível com seu total (FR-8)
**And** produto genérico aparece marcado como tal, usando a marcação que `agregar` já resolveu (FR-13, AD-21)

**AC4 — Ressalvas ao lado, nunca em rodapé**

**Given** as duas ressalvas
**When** sua posição é verificada
**Then** estão ao lado do respectivo gráfico, nunca em nota de rodapé (FR-18, AD-14)

**AC5 — Texto de ressalva vive no template**

**Given** os textos de ressalva
**When** eles são localizados no código
**Then** vivem no template, não em Python (AD-10)

## Tasks / Subtasks

- [x] **Task 1 — Estender `plataforma/relatorio.py`** (AC: 1, 2, 3, 5)
  - [x] `_barras_sentimento(distribuicao: DistribuicaoSentimento, analisadas: int) -> list[BarraSentimento]`: uma barra por categoria, ordem fixa positivo→neutro→negativo, `largura_pct = total / analisadas * 100 if analisadas else 0.0`. Rótulos "Positivo"/"Neutro"/"Negativo" em português
  - [x] `_barras_ranking(ranking: list[ItemRanking]) -> list[BarraRanking]`: uma barra por item, ordem preservada, `largura_pct` relativa ao maior `total`; guard de lista vazia sem `max()` de sequência vazia
  - [x] `renderizar(estado)` passa `barras_sentimento=...` e `barras_ranking=...` ao template, além de `itens_fila=...`
  - [x] Nenhum texto de ressalva em Python — `_barras_*` só devolvem números e rótulos
  - [x] Imports: `plataforma.estado.DistribuicaoSentimento`, `plataforma.estado.ItemRanking`
  - [x] Docstring do módulo atualizada com o princípio dos dois gráficos novos

- [x] **Task 2 — Estender `plataforma/templates/relatorio.html.j2`** (AC: 1, 2, 3, 4, 5)
  - [x] Duas `<section>` novas depois de `#fila-prioridade`: `#distribuicao-sentimento` e `#ranking-produtos`, nessa ordem
  - [x] Seção de sentimento: `<svg>` com `<rect>`/`<text>` por `barras_sentimento`, ressalva `<p class="ressalva">` na mesma `<section>`
  - [x] Seção de ranking: mesma técnica; item `generico=True` ganha sufixo `" (termo genérico)"` no `<text>`; `"não identificado"` aparece como item comum do ranking, sem tratamento especial; ressalva de volume≠gravidade na mesma seção
  - [x] Nenhum `<script src>`/`<link href>`/`@import` externo
  - [x] Ressalvas literais no `.j2`, comentário Jinja explicando o fator de escala do `viewBox`

- [x] **Task 3 — Estender `tests/test_relatorio.py`** (AC: 1, 2, 3, 4, 5)
  - [x] `_barras_sentimento`: proporção correta e guard de `analisadas=0`
  - [x] `_barras_ranking`: maior item em 100%, lista vazia sem erro
  - [x] Produto genérico marcado visivelmente; `"não identificado"` visível com total
  - [x] Sem biblioteca externa no HTML renderizado
  - [x] Ressalva de sentimento dentro da própria seção (entre abertura da seção e a seção de ranking); ressalva de ranking dentro da própria seção (antes de `</body>`)
  - [x] Textos de ressalva literais no `.j2`
  - [x] Builders `agregados(...)`/`estado(...)` estendidos com `ranking_produtos`/`distribuicao_sentimento`/`analisadas` opcionais, retrocompatíveis com as chamadas da Story 2.3
  - [x] `uv run pytest -q` → **182 passed** (172 pré-existentes + 10 novos)

### Review Findings

- [x] [Review][Patch] Ressalva de sentimento afirma um fato específico desta execução ("o sentimento desta base é quase todo negativo") — se uma base futura vier mais balanceada, a ressalva fixa contradiz visualmente o próprio gráfico ao lado dela [plataforma/templates/relatorio.html.j2]
- [x] [Review][Patch] Seção de ranking sem estado vazio — `barras_ranking=[]` produz `viewBox="0 0 320 0"` (altura zero, inválida) sem mensagem alguma, ao contrário da seção da fila que já declara "fila vazia" como informação [plataforma/templates/relatorio.html.j2]
- [x] [Review][Patch] `<svg>` de sentimento com altura fixa `90` em vez de calculada (`barras_sentimento|length * 30`), inconsistente com o `<svg>` de ranking que já calcula a própria altura [plataforma/templates/relatorio.html.j2]
- [x] [Review][Patch] Sem teste para proporção que não divide exato (ex.: 1/3) — os dois casos testados de `_barras_ranking`/`_barras_sentimento` usam denominadores que dividem certo, o comportamento de `|round(1)` nunca foi exercitado numa dízima [tests/test_relatorio.py]
- [x] [Review][Patch] Comentário do `viewBox` do ranking diz "320 de largura útil", mas o maior item só preenche até 300 (`largura_pct` máximo 100 × fator 3) — a largura útil real é 300, não 320 [plataforma/templates/relatorio.html.j2]
- [x] [Review][Defer] `_barras_ranking` confia que `ranking` já chega ordenado por `total` decrescente (de `agregacao._ranking_produtos`) sem reverificar — mesma classe de confiança em invariante upstream já aceita para `_itens_fila` na Story 2.3 [plataforma/relatorio.py:_barras_ranking]
- [x] [Review][Defer] Ressalva de ranking cita exemplos de termo genérico ("produto", "fatura") como texto livre, duplicando `catalogo.TERMOS_GENERICOS` sem vínculo — se a lista canônica mudar, a ressalva pode ficar desatualizada [plataforma/templates/relatorio.html.j2]
- [x] [Review][Defer] `rotulo` do produto é texto livre do modelo, renderizado sem tratamento de overflow/quebra de linha no `<svg>` — rótulo muito longo pode extrapolar visualmente o `viewBox` de 320 [plataforma/templates/relatorio.html.j2]

**Achados descartados (falso positivo / já coberto em outra camada / fora de escopo):**
- Sugestão de `StrictUndefined` no `Environment` — mudaria o comportamento de erro do Jinja para todo o pacote, não pedido por nenhuma AC, fora do escopo desta story.
- Gráfico de sentimento sempre renderiza 3 barras, mesmo com `analisadas=0` — não é bug, é design: as três categorias são fixas por construção (`_ROTULOS_SENTIMENTO`), nunca uma lista vazia como o ranking.
- Guard `if maior_total else 0.0` em `_barras_ranking` sem teste cobrindo `maior_total == 0` — inalcançável na prática: um item só entra no ranking depois de ser contado ao menos uma vez (`agregacao._ranking_produtos`), então `maior_total >= 1` sempre que a lista não é vazia.
- Testes estruturais por `str.split` em vez de parser de DOM — mesmo estilo já estabelecido e aceito nos testes da Story 2.3.
- Classes CSS (`grafico-com-ressalva`, `ressalva`) sem folha de estilo — nenhuma AC exige diferenciação visual, só posicionamento estrutural (já provado pelos testes).
- Falta de `<title>`/`<desc>` de acessibilidade no `<svg>` — nenhuma AC pede isso, fora do escopo.
- Builders de teste (`agregados`/`estado`) permitem `distribuicao_sentimento`/`analisadas` inconsistentes entre si — nit de fixture de teste, não risco de produção.
- Soma de `distribuicao_sentimento` não bater com `analisadas` causando `largura_pct > 100` — impossível por construção: `agregacao._distribuicao_sentimento` itera `analises` (comprimento == `analisadas`) e incrementa exatamente um balde por `Analise`, já que `sentimento` é `Literal` não-nulo obrigatório.

## Dev Notes

### Texto de ressalva sugerido (AD-14, FR-18) — literal no `.j2`

Nenhuma AC prescreve o texto exato, só que ele "nomeia o que limita a leitura nesta base". Para manter consistência com o tom das mensagens já usadas no repositório (`main.py`, `config.py`: nomear a causa/limite com precisão, sem jargão), usar como base:

- **Sentimento:** "Ressalva: o sentimento desta base é quase todo negativo — o gráfico mostra o tom do texto recebido, não uma medida de satisfação geral dos clientes."
- **Ranking:** "Ressalva: volume não equivale a gravidade. O produto mais reclamado tende a ser o mais vendido, não o mais problemático. Itens marcados como genéricos (ex.: \"produto\", \"fatura\") não identificam um item específico."

Ambas devem ficar **dentro da mesma seção** do gráfico correspondente, visualmente ao lado (ex.: mesmo `<div>`/`<section>`, um `<figure>`+`<figcaption>`, ou duas colunas) — nunca num bloco de rodapé compartilhado no fim do documento. A prova de teste (Task 3) é estrutural: a ressalva precisa aparecer *dentro* da seção do gráfico, não depois de todas as seções.

### Por que a proporção (`largura_pct`) é calculada em Python, não no template

`agregacao.py` já estabeleceu o padrão: guardas de divisão por zero (`ocupacao_fila`, `taxa_produto_nao_nomeado`) vivem no filtro que produz o número, não em quem exibe. Fazer `{{ (barra.total / analisadas * 100) }}` dentro do `.j2` reintroduziria esse cálculo (e o guard de zero) espalhado em Jinja, sem teste unitário isolado. `_barras_sentimento`/`_barras_ranking` seguem o mesmo formato de `_itens_fila` (Story 2.3): uma função pura que devolve uma lista de dicts prontos para o `for` do template — o template só itera e desenha.

Isto **não viola AD-10** ("texto de produto vive no template, não em Python") — AD-10 é sobre *texto visível* (rótulos, ressalvas, categorias), não sobre a geometria numérica de um gráfico. O rótulo do produto (`item["rotulo"]`) já vem pronto de `agregacao.py` desde a Story 2.2; `relatorio.py` só o repassa, nunca o reescreve.

### Ranking pode ter qualquer número de produtos — nenhum corte (top-N) é pedido

Nenhuma AC ou documento pede truncar o ranking a um top-N. Renderizar todos os itens de `agregados["ranking_produtos"]`, na base sintética de 50 reclamações isso é uma lista curta. Não inventar paginação nem "ver mais" — fora do escopo desta story.

### Escala do SVG: proporção importa, pixel exato não

A Task 2 sugere um `viewBox`/largura de referência (~300 unidades) só como ponto de partida; o dev agent tem liberdade de ajustar constantes de geometria (altura de barra, espaçamento entre barras) desde que: (1) a largura de cada `<rect>` seja proporcional a `largura_pct`, (2) o item de maior `total` no ranking preencha 100% da largura útil, (3) nenhum valor de geometria seja um número "mágico" sem comentário explicando a escolha (ex.: por que 300, por que altura 20).

### O que esta story NÃO faz

**Não escreve arquivo, não toca `grafo.py`/`main.py`.** Mesmo raciocínio da Story 2.3 — FR-1b (escrita/nomeação) é Story 2.6; até lá `renderizar` continua sendo função pura testada isoladamente.
**Não renderiza cabeçalho de confiabilidade/degradação.** Story 2.5.
**Não trunca o ranking.** Ver Dev Notes acima.
**Não introduz nova chave em `Estado`.** `_barras_sentimento`/`_barras_ranking` só leem `agregados`, já completo desde a Story 2.2.

### Estrutura de arquivos

```text
plataforma/
  relatorio.py                    # UPDATE — _barras_sentimento, _barras_ranking, renderizar estendido
  templates/
    relatorio.html.j2             # UPDATE — duas seções novas após a fila
tests/
  test_relatorio.py                # UPDATE — testes das duas funções novas e das ressalvas
```

**Não criar/tocar nesta story:** `plataforma/grafo.py`, `main.py`, `plataforma/estado.py` (contrato já completo — `Agregados.ranking_produtos`, `Agregados.distribuicao_sentimento`, `ItemRanking`, `DistribuicaoSentimento` já existem desde a Story 1.1/2.2), `plataforma/agregacao.py`, `plataforma/pontuacao.py`, `plataforma/catalogo.py`, `docs/`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-10** | Ressalvas são texto literal do `.j2`; `relatorio.py` só calcula geometria numérica, nunca o texto de limitação |
| **AD-11** | Gráficos são `<rect>`/`<text>` dentro de `<svg>` escrito no template; nenhuma fonte externa |
| **AD-14** | Ressalva ao lado do gráfico correspondente, dentro da mesma seção — nunca em rodapé compartilhado |
| **AD-19/AD-22** | `_barras_ranking` preserva a ordem de `agregados["ranking_produtos"]`; não reordena, não recalcula pertencimento nem contagem |
| **AD-21** | Marcação de "genérico" já veio de `agregar` (Story 2.2) em `item["generico"]`; o template só decide como exibi-la |
| **AD-7/AD-12** | `relatorio.py` continua sem `google.genai`; `_barras_sentimento`/`_barras_ranking` são funções puras, testáveis com `Agregados` fabricado à mão |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.4] — ACs originais
- [Source: plataforma/estado.py#Agregados, ItemRanking, DistribuicaoSentimento] — contrato já completo
- [Source: plataforma/agregacao.py#_ranking_produtos, _distribuicao_sentimento] — quem produz os dados que esta story só exibe; não recalcular aqui
- [Source: plataforma/relatorio.py, plataforma/templates/relatorio.html.j2] — código real da Story 2.3, já com `_ENVIRONMENT` (`trim_blocks`/`lstrip_blocks` incluídos), `_itens_fila`, `ItemFila` — seguir o mesmo padrão para as novas funções
- [Source: tests/test_relatorio.py] — builders (`reclamacao`, `pontuacao`, `agregados`, `estado`) a estender, não recriar
- [Source: _bmad-output/implementation-artifacts/2-3-relatorio-com-a-fila-no-topo-e-a-evidencia-a-vista.md#Dev Agent Record] — revisão adversarial da story anterior já cobriu `plataforma.relatorio` em `test_import_sem_credencial.py::MODULOS`; não reabrir esse achado, só manter a cobertura ao estender o módulo
- [Source: _bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md#AD-10, AD-11, AD-14] — regras de autocontenção e ressalva

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run pytest -q` → `182 passed` (baseline: 172 + 10 novos em `test_relatorio.py`).
- Sem falhas de implementação — os testes passaram de primeira após escrever o código conforme as Dev Notes já haviam resolvido a geometria/proporção.

### Completion Notes List

- `plataforma/relatorio.py` estendido com `_barras_sentimento`, `_barras_ranking` (+ `BarraSentimento`/`BarraRanking` `TypedDict`), e `renderizar` passa os dois novos contextos ao template.
- `plataforma/templates/relatorio.html.j2` ganhou duas seções (`#distribuicao-sentimento`, `#ranking-produtos`) com `<svg>`/`<rect>`/`<text>` e ressalvas literais ao lado, dentro da própria seção.
- `grafo.py`/`main.py` não tocados, conforme escopo da story.
- Nenhum desvio de design em relação ao que a story especificou.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/relatorio.py` | modificado |
| `plataforma/templates/relatorio.html.j2` | modificado |
| `tests/test_relatorio.py` | modificado |

## Change Log

- 2026-08-09: Implementação completa da Story 2.4 — gráficos SVG de sentimento e ranking com ressalvas, testes estendidos. `182 passed`.
- 2026-08-09: Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Acceptance Auditor: 0 violações, todas as 5 ACs conformes. 5 patches aplicados — ressalva de sentimento reescrita sem afirmar fato específico da execução; estado vazio no ranking ("Nenhum produto identificado"); altura do SVG de sentimento calculada em vez de fixa; comentário de `viewBox` corrigido (300, não 320); 4 testes novos cobrindo dízima (`_barras_ranking`, `_barras_sentimento`, HTML renderizado) e ranking vazio. 3 achados deferidos (confiança na ordenação upstream do ranking, exemplos de termo genérico como texto livre, rótulo de produto sem tratamento de overflow). 8 achados descartados por já cobertos por invariantes anteriores ou fora de escopo. Suíte final: `186 passed` (via `uv run python -m pytest` — `rtk`/bash bloqueados por política de Controle de Aplicativo do Windows nesta sessão, contornado com PowerShell).
