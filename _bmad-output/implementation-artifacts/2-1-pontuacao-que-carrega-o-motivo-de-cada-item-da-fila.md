# Story 2.1: Pontuação que carrega o motivo de cada item da fila

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a gestor,
I want que cada item da fila chegue acompanhado do que o colocou ali,
so that eu decida sobre a evidência e não sobre a palavra do sistema.

## Acceptance Criteria

**AC1 — Pesos em mapeamento único, código do catálogo como chave**

**Given** o módulo `plataforma/pontuacao.py`
**When** os pesos são declarados
**Then** vivem num único mapeamento com o código do catálogo como chave, derivado da tabela de `risk-signals.md`
**And** nenhum código de sinal aparece como literal solto no módulo (AD-18)
**And** o corte binário de 3 pontos é declarado no mesmo lugar

**AC2 — Pesos ratificados e modificador de `Status`**

**Given** os pesos por código, ratificados em 2026-08-07 contra `risk-signals.md`
**When** eles são declarados
**Then** `dinheiro_retido` = 3, `ameaca_explicita` = 3, `lei_citada` = 3, `registro_contraditorio` = 2, `dano_continuado` = 2, `prazo_estourado` = 1
**And** `Status == "Respondida"` aplica modificador −1, nunca como parcela independente

**AC3 — Grupo A satura em 3, nunca 6**

**Given** uma reclamação com `ameaca_explicita` **e** `lei_citada` ambos válidos
**When** `pontuar` executa
**Then** o grupo do sinal A contribui 3 pontos, não 6
**And** a saturação é lida de `catalogo.GRUPO_SINAL_A`, não reimplementada em `pontuacao.py`

**AC4 — `dinheiro_retido` + `Status=Respondida` fica fora da fila (o caso que valida a regra)**

**Given** uma reclamação com `dinheiro_retido` válido e `Status = "Respondida"`
**When** `pontuar` executa
**Then** a pontuação é 2 e o item **não** entra na fila
**And** este é o caso que dá precisão de 100% à regra medida (M-1)

**AC5 — Sinal válido produz `Motivo` de origem `sinal`**

**Given** uma `Analise` com um `Sinal` de `valida = True`
**When** `pontuar` executa
**Then** produz um `Motivo` com `origem = "sinal"` e `citacao` não nula, vinda do modelo (AD-3)

**AC6 — Motivo de origem `atributo` para o modificador de `Status`**

**Given** o modificador de `Status = "Respondida"` aplicado a uma reclamação
**When** `pontuar` executa
**Then** produz um `Motivo` com `origem = "atributo"` e `citacao` nula
**And** o rótulo nomeia o motivo estrutural (FR-9, AD-3) — ver Dev Notes sobre por que "entra na fila apenas por atributo" não é alcançável com a tabela de pesos ratificada

**AC7 — Código com `Sinal` inválido não soma pontos**

**Given** um `codigo` cujo `Sinal` ficou com `valida = False`
**When** `pontuar` executa
**Then** aquele código não soma pontos, inclusive se outro par do mesmo código passou na verificação (AD-2)

**AC8 — `pontuar` é o único escritor de `pontuacoes`**

**Given** o estado após `pontuar`
**When** ele é inspecionado
**Then** `pontuacoes` contém uma `Pontuacao` por reclamação analisada, com `id`, `pontos`, `na_fila` e `motivos`
**And** `pontuar` é o único nó que escreve `pontuacoes`, incluindo o valor de `na_fila` (AD-19)

**AC9 — Parcelas não exercidas pela base têm caso construído à mão**

**Given** `Analise` fabricada à mão exercitando `ameaca_explicita`, `dano_continuado` e `registro_contraditorio`
**When** a suíte roda
**Then** cada uma das três parcelas produz pontuação, sem nenhuma chamada de rede (AD-12, Q-4)

**AC10 — Sem SDK do modelo nos imports (AD-7)**

**Given** o módulo `plataforma/pontuacao.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai`, direta nem transitivamente

## Tasks / Subtasks

- [x] **Task 1 — Criar `plataforma/pontuacao.py`** (AC: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
  - [x] `PESOS = MappingProxyType({...})` — os seis códigos com os pesos ratificados; `CORTE = 3`; `MODIFICADOR_STATUS_RESPONDIDA = -1`. Congelado, no padrão de `catalogo.CATALOGO`
  - [x] `pontuar(estado: Estado) -> dict`: para cada `Analise` em `estado["analises"]`, localizar a `Reclamacao` correspondente por `id` (para ler `status`); construir `motivos: list[Motivo]` e somar `pontos`
  - [x] **Um `Motivo` de origem `sinal` por `Sinal` válido** (não deduplicado por código — decisão desta story, ver Dev Notes) — `citacao` vem do `Sinal`, `rotulo` é o `codigo`
  - [x] **Pontuação por código, não por instância de `Sinal`:** se dois `Sinal` válidos compartilham o mesmo `codigo` (duas citações diferentes sustentando o mesmo risco), o peso daquele código soma **uma vez** — cada `Sinal` ainda gera seu próprio `Motivo`, mas os pontos não dobram
  - [x] **Saturação do grupo A:** ler `catalogo.GRUPO_SINAL_A`; se qualquer código do grupo estiver entre os válidos, somar o peso da parcela **uma única vez** para o grupo inteiro, mesmo que os dois códigos do grupo estejam presentes
  - [x] **Modificador de `Status`:** se `reclamacao["status"] == "Respondida"`, somar `MODIFICADOR_STATUS_RESPONDIDA` e acrescentar um `Motivo(origem="atributo", citacao=None, rotulo=...)` — sempre, independente do item entrar ou não na fila
  - [x] `na_fila = pontos >= CORTE`
  - [x] Devolver `{"pontuacoes": [Pontuacao(...), ...]}` — uma por `Analise`, na mesma ordem de `estado["analises"]`
  - [x] Docstring de módulo: propósito, porquê não-óbvio (pontuação por código não por par/instância; saturação lida do catálogo, não reimplementada; por que AC6 é estruturalmente correto mas não alcançável isoladamente com a tabela de pesos atual)
  - [x] Imports: `types.MappingProxyType`, `plataforma.catalogo` (`GRUPO_SINAL_A`), `plataforma.estado` (`Estado`, `Motivo`, `Pontuacao`) — sem `google.genai`, sem `plataforma.analise`/`plataforma.evidencia`/`plataforma.ingestao`/`plataforma.grafo` (pontuacao é filtro, não importa outro filtro)

- [x] **Task 2 — Religar `grafo.py`** (AC: 8)
  - [x] Trocar a aresta final de `_verificar_conservacao -> END` para `_verificar_conservacao -> pontuar -> END`
  - [x] `add_node("pontuar", pontuacao.pontuar)` — sem `retry_policy`/`error_handler`: `pontuar` é determinístico, não toca rede, não tem falha de transporte para absorver
  - [x] Comentário no código apontando que, quando `agregar` nascer (Story 2.2), a aresta final muda de novo para `pontuar -> agregar -> END`

- [x] **Task 3 — Criar `tests/test_pontuacao.py`** (AC: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
  - [x] Caso feliz: `dinheiro_retido` válido, `Status` ≠ Respondida → 3 pontos, `na_fila=True`, um `Motivo` de origem `sinal`
  - [x] AC4, o caso que valida a regra: `dinheiro_retido` válido + `Status="Respondida"` → 2 pontos, `na_fila=False`
  - [x] Saturação: `ameaca_explicita` **e** `lei_citada` válidos → 3 pontos (não 6); dois `Motivo` de origem `sinal` (um por código), mas pontuação única do grupo
  - [x] Dois `Sinal` válidos do mesmo código (duas citações diferentes) → peso somado uma vez; dois `Motivo` (um por `Sinal`)
  - [x] `Sinal` com `valida=False` não soma pontos, mesmo com outro par do mesmo código válido (AD-2)
  - [x] Modificador de `Status="Respondida"` sempre produz `Motivo` de origem `atributo`, `citacao=None` — testar isoladamente (não depende de o item entrar na fila)
  - [x] `Registro_contraditorio` + `prazo_estourado` = 3 pontos → `na_fila=True` (linha da tabela de conferência de `risk-signals.md`)
  - [x] Caso construído à mão para `ameaca_explicita`, `dano_continuado`, `registro_contraditorio` (AC9, Q-4) — sem chamada de rede
  - [x] `pontuar(estado)` preserva a ordem de `estado["analises"]` em `pontuacoes`
  - [x] Import sem credencial: `plataforma.pontuacao` funciona sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` — **não** acrescentar a `test_import_sem_credencial.py::MODULOS` diretamente sem checar; `pontuacao.py` não arrasta o SDK (só importa `catalogo`/`estado`), então **pode** entrar nesse `MODULOS` como os módulos-folha originais — mas não no `parametrize` de `test_contrato.py`, que é especificamente para módulos que não importam nada de `plataforma/` (pontuacao importa `catalogo` e `estado`)

## Dev Notes

### AC6 é estruturalmente correto, mas "entra na fila apenas por atributo" não acontece com a tabela ratificada — leia antes de codar

`risk-signals.md#Pesos do v1` (ratificado em 2026-08-07) lista **um único** atributo: `Status = Respondida`, peso **−1**, explicitamente marcado como "modificador", nunca parcela independente. Não existe peso positivo para nenhum atributo do CSV — "categoria", mencionada no texto solto de `epics.md` AC6 desta story, **não aparece em lugar nenhum da tabela de pesos ratificada nem do contrato de estado** (`Reclamacao` não tem campo `categoria`). Um modificador negativo, sozinho, nunca cruza o corte de 3 pontos — é matematicamente impossível uma reclamação **entrar** na fila só por atributo com a tabela atual.

**Decisão desta story:** implementar o mecanismo de forma genérica e correta — o modificador de `Status` sempre produz seu `Motivo` de origem `atributo`, com `citacao` nula, exatamente como AD-3 exige — mas **não** forçar um teste onde esse `Motivo` sozinho põe o item na fila, porque isso exigiria inventar um peso positivo que nenhuma fonte autoriza. O teste cobre a AC pela metade que é real: o modificador sempre gera o `Motivo` certo, testado isoladamente da decisão de `na_fila`. Se uma base real algum dia trouxer um atributo com peso positivo, o mecanismo já está pronto — só a tabela `PESOS` muda.
[Source: risk-signals.md#Pesos do v1 — tabela canônica, sem entrada de "categoria"; plataforma/estado.py — Reclamacao sem campo categoria]

### Pontuação é por código, `Motivo` é por `Sinal` — duas granularidades diferentes, de propósito

Duas citações diferentes sustentando o mesmo código (`dinheiro_retido` citado duas vezes na mesma reclamação) somam o peso **uma vez** — sem isso, a reclamação ganharia pontos por repetição textual, não por gravidade. Mas cada citação individual ainda produz seu próprio `Motivo`, porque FR-12 quer a evidência visível — esconder a segunda citação seria perder informação que o gestor pode querer ver. Isso não está escrito letra por letra em nenhuma AC; é a leitura mais consistente com AD-2 (pontuação por código) e FR-6/FR-12 (toda citação válida é evidência exibível) ao mesmo tempo.

### O que esta story NÃO faz

**Não decide a ordem da fila.** `agregar` (Story 2.2) ordena por `pontos` decrescente com desempate por data/id — `pontuar` só decide `na_fila`, nunca ordena.
**Não lê `catalogo.CATALOGO` além de `GRUPO_SINAL_A`.** As definições/exemplos do catálogo são para o prompt (Story 1.5); `pontuacao.py` só precisa saber quais códigos saturam juntos.
**Não escreve `agregados` nem `caminho_html`.** Só `pontuacoes` (AD-19).

### Religar o grafo — mesmo espírito da Story 1.6, sem os riscos de concorrência

Diferente de `analisar_lote`, `pontuar` é síncrono, determinístico, sem chamada de rede — não precisa de `retry_policy`/`error_handler`, e não tem o problema que a Story 1.6 encontrou (esse problema era específico de `error_handler` sob concorrência de `Send`; `pontuar` roda como nó único, não fan-out). `add_node("pontuar", pontuacao.pontuar)` simples basta.

### Estrutura de arquivos

```text
plataforma/
  pontuacao.py           # NOVO — PESOS, CORTE, MODIFICADOR_STATUS_RESPONDIDA, pontuar
  grafo.py                # UPDATE — aresta final: _verificar_conservacao -> pontuar -> END
tests/
  test_pontuacao.py        # NOVO
```

**Não criar nesta story:** `agregacao.py`, `relatorio.py`, `main.py` (já existe, não tocar), `templates/`.

**Não tocar:** `plataforma/ingestao.py`, `plataforma/config.py`, `plataforma/evidencia.py`, `plataforma/analise.py`, `docs/`, `baseline.py`, `classificador.py`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-2** | Código com `Sinal` inválido não soma pontos, mesmo com par válido do mesmo código |
| **AD-3** | `Motivo.origem` correto para cada fonte; `citacao` não nula sse `origem="sinal"` |
| **AD-4** | `pontuacao.py` lê `Reclamacao.status` para o modificador — não é `renderizar`, então não viola a proibição de `renderizar` derivar motivo de `Reclamacao` |
| **AD-18** | Pesos num mapeamento único; saturação lida de `catalogo.GRUPO_SINAL_A`, nenhum código como literal solto |
| **AD-19** | `pontuar` é o único escritor de `pontuacoes` |
| **AD-7** | `pontuacao.py` não importa `google.genai` |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1] — ACs originais
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/risk-signals.md#Pesos do v1] — tabela canônica de pesos, ratificada 2026-08-07
- [Source: ARCHITECTURE-SPINE.md#AD-2, AD-3, AD-4, AD-18, AD-19] — invariantes centrais
- [Source: plataforma/catalogo.py] — `GRUPO_SINAL_A`
- [Source: plataforma/estado.py] — `Motivo`, `Pontuacao`, `Reclamacao.status`
- [Source: _bmad-output/implementation-artifacts/1-6-fan-out-por-lote-com-falha-absorvida.md] — Dev Notes já apontavam que a aresta final de `grafo.py` mudaria nesta story

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-auto) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run pytest -q` → falhou em `test_catalogo.py::test_nenhum_outro_modulo_declara_codigo_de_sinal_como_literal` na primeira versão (`PESOS` retipava os seis códigos em `pontuacao.py`).
- Corrigido: `catalogo.py` ganhou `"peso"` em cada entrada; `pontuacao.PESOS` deriva de lá. `uv run pytest -q` → `134 passed` (baseline: 124).
- `uv run python -c "from plataforma import pontuacao; print(dict(pontuacao.PESOS))"` → pesos conferem com `risk-signals.md`.
- Pós-revisão: `137 passed`.

### Completion Notes List

- **Achado corrigido antes mesmo da revisão:** a primeira versão de `pontuacao.py` violava AD-18 ao retipar os seis códigos como chaves literais — pego pelo teste pré-existente da Story 1.1 (`test_nenhum_outro_modulo_declara_codigo_de_sinal_como_literal`), cujo próprio docstring já previa esse cenário. Corrigido movendo os pesos para `catalogo.CATALOGO[codigo]["peso"]`; `pontuacao.py` só lê.
- **AC6 é estruturalmente satisfeita, não pela fila** — documentado na story: a tabela ratificada só tem `Status=Respondida` como atributo, sempre modificador negativo, nunca cruza o corte sozinho. O `Motivo` de origem `atributo` é produzido corretamente; o cenário "entra na fila só por atributo" é matematicamente impossível com os pesos atuais.
- **Achado de revisão (Blind Hunter):** a saturação do grupo A dependia da ordem de iteração ("primeiro código que aparece ganha"), só estável porque `ameaca_explicita` e `lei_citada` têm o mesmo peso hoje. Corrigido para usar o maior peso entre os presentes, independente de ordem — a mudança certa antes de qualquer story futura divergir os pesos do grupo.
- **Achado de revisão:** acesso a `PESOS` inconsistente entre os dois branches (`[codigo]` levantando `KeyError` vs `.get(codigo, 0)` silenciando) — unificado para não derrubar a execução inteira por um código alucinado pelo modelo.
- Vários achados rejeitados por já estarem protegidos por invariantes de stories anteriores (casamento por id da 1.5, unicidade de id da 1.3, NFR-4) — ver Review Triage Log do spec para o detalhe completo.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/pontuacao.py` | novo |
| `plataforma/catalogo.py` | modificado |
| `plataforma/grafo.py` | modificado |
| `tests/test_pontuacao.py` | novo |
| `tests/test_catalogo.py` | modificado |
