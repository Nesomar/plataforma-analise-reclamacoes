---
baseline_commit: '1329c90a72a87d274608e4850a566f91516d110a'
---

# Story 3.1: A fila do pipeline medida contra o gabarito

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a avaliador técnico,
I want ver a precisão e o recall da fila que o pipeline realmente produz,
so that eu saiba que a métrica mede o produto e não um classificador de medição que roda por fora dele.

## Acceptance Criteria

**AC1 — Comparação usa a saída real do pipeline, casamento por id**

**Given** o pipeline completo executado sobre `docs/reclamacoes_reclameaqui.csv`
**When** o campo `na_fila` das `pontuacoes` é comparado com `docs/gabarito.csv`
**Then** a comparação usa a saída do próprio pipeline, nunca `baseline.py` nem `classificador.py` (M-1)
**And** o casamento entre saída e gabarito é por `ID_Reclamacao`, nunca por posição

**AC2 — Precisão, recall e contagens registrados**

**Given** a comparação concluída
**When** os números são calculados
**Then** precisão, recall e as contagens de TP, FP e FN são registrados
**And** o critério de aceitação é precisão ≥ 95% com recall ≥ 65% (M-1)

**AC3 — Resultado registrado como saiu, sem reajuste de limiar**

**Given** um resultado que não atinge o critério
**When** ele é registrado
**Then** o número real é reportado como saiu, com os itens divergentes nomeados por identificador
**And** o limiar não é reajustado para acomodar o resultado
**And** a story está pronta quando a medição está registrada — um resultado abaixo do limiar abre um item de correção de curso, não reprova a story nem bloqueia a entrega

**AC4 — Ocupação da fila (CM-1)**

**Given** a fila produzida
**When** sua ocupação é calculada
**Then** a proporção da base que entrou na fila é registrada
**And** acima de 40% dispara alerta: a fila deixou de ordenar (CM-1)

**AC5 — CM-2, CM-3, CM-4 registrados junto da medição**

**Given** a saída do pipeline
**When** CM-2, CM-3 e CM-4 são lidos de `Agregados`
**Then** os três valores são registrados junto com a medição de M-1
**And** CM-2 em zero constante é anotado como indistinguível de mecanismo morto, já que o caso sintético da Story 1.4 é o único que o exercita

**AC6 — 100% das citações são trecho literal (M-2)**

**Given** as citações presentes no relatório final
**When** elas são verificadas
**Then** 100% são trecho literal do texto original com no mínimo cinco palavras (M-2)

## Tasks / Subtasks

- [x] **Task 1 — Criar `medir_fila.py`** (AC: 1, 2, 3, 4, 5, 6)
  - [x] Script executável na raiz, mesmo padrão de `baseline.py`/`classificador.py` (`autoteste()` com `assert`, chamado em `if __name__ == "__main__":`)
  - [x] `ler_gabarito(caminho) -> list[dict]`
  - [x] `comparar(pontuacoes, gabarito) -> dict` — casamento por `ID_Reclamacao`, TP/FP/FN/precisão/recall/divergentes, sem importar `baseline.py`/`classificador.py`
  - [x] `verificar_citacoes(pontuacoes, reclamacoes_por_id) -> tuple[int, int]` — reaproveita `evidencia._passa_checagem_individual`
  - [x] `main()`: grafo real, imprime M-1/CM-1/CM-2/CM-3/CM-4/M-2
  - [x] `autoteste()`: TP/FP/FN fabricados + citação inválida fabricada
  - [x] Imports conforme especificado

- [x] **Task 2 — Rodar a medição real e registrar os números** (AC: 2, 3, 4, 5, 6)
  - [x] Rodado com `GEMINI_API_KEY` real do ambiente (o SDK `google-genai` já lê essa variável como fallback de `GOOGLE_API_KEY` — achado registrado na Story 1.2)
  - [x] Números reais registrados em Completion Notes, como saíram, sem ajuste de limiar
  - [x] Precisão (88%) não atingiu 95% — registrado, ids divergentes nomeados, item de correção de curso aberto em `deferred-work.md` (AC3, não é falha desta story)

### Review Findings

- [x] [Review][Patch] `comparar` itera só sobre `previsto` (ids que receberam `Pontuacao`) — um id do gabarito nunca analisado (`nao_analisadas > 0`) desaparece silenciosamente do FN em vez de contar como erro, e um id de `previsto` ausente do gabarito cai em `divergentes`/FP por `None != False`. Não se manifestou nesta execução porque os dois CSVs têm exatamente os mesmos 50 ids, mas é bug real de propósito geral — achado convergente dos três revisores [medir_fila.py:comparar]
- [x] [Review][Patch] Strings de critério/alerta impressas (`"95%"`, `"65%"`, `"40%"`) são texto solto, não formatadas a partir de `LIMIAR_PRECISAO`/`LIMIAR_RECALL`/`LIMIAR_OCUPACAO_FILA` — se o limiar mudar, o texto impresso dessincroniza da lógica real [medir_fila.py:main]
- [x] [Review][Patch] `tempfile.mktemp()` é documentado pela própria stdlib como obsoleto por corrida TOCTOU [medir_fila.py:main]
- [x] [Review][Patch] Arquivo HTML temporário nunca é removido, apesar da docstring chamá-lo de "efêmero" — toda execução deixa um resíduo órfão no diretório temporário do SO [medir_fila.py:main]
- [x] [Review][Patch] Caminhos `"docs/reclamacoes_reclameaqui.csv"`/`"docs/gabarito.csv"` fixos sem checagem de existência — rodar fora da raiz do repositório produz `FileNotFoundError` cru, na contramão da disciplina de "nenhum traceback cru ao operador" que o resto do projeto segue [medir_fila.py:main]
- [x] [Review][Patch] Nota de CM-2 ("zero constante é indistinguível de mecanismo morto") dispara também quando `propostos == 0` (nenhum código proposto) — caso degenerado diferente de "derrubou zero de vários propostos", mas exibe a mesma frase [medir_fila.py:main]
- [x] [Review][Patch] `comparar` devolve `falsos_positivos`/`falsos_negativos` separados em vez de `divergentes` misturado — mapeamento real recuperado por consulta local a `docs/gabarito.csv` (sem gastar crédito de novo): FP = `RA333754555`, `RA607526654`; FN = `RA283758720`, `RA497478786`, `RA678722458`, `RA821218382` [medir_fila.py:comparar, deferred-work.md]
- [x] [Review][Patch] `main()` acessa `estado["pontuacoes"]`/`estado["agregados"]` sem checar `estado["analises"]` vazio primeiro — se `_rotear_apos_conservacao` desviar para `END` (zero análises), essas chaves nem existem no estado devolvido, e o acesso levantaria `KeyError` cru em vez de mensagem nomeando a causa (mesma disciplina que `main.py` já aplica) [medir_fila.py:main]

- [x] [Review][Defer] Sem checagem prévia de que os conjuntos de id de `docs/gabarito.csv` e `docs/reclamacoes_reclameaqui.csv` coincidem — um id defasado ou digitado errado em qualquer um dos dois seria absorvido silenciosamente. Risco residual bem menor depois do patch de `comparar` (que agora usa o gabarito como universo), mas uma validação completa (`assert` nomeando a diferença de conjuntos) não foi pedida por nenhuma AC

**Achados descartados (decisão de design já justificada / nit de processo):**
- `verificar_citacoes` importa `evidencia._passa_checagem_individual` (nome privado de outro módulo) — reuso intencional já justificado nas próprias Dev Notes desta story, mesmo precedente de `pontuacao.py` lendo `catalogo.CATALOGO` diretamente.
- Entrada de `deferred-work.md` sem responsável/prazo/critério de encerramento explícitos — nenhuma outra entrada do arquivo (stories 1.1-2.6) tem esses campos; não é o formato estabelecido no projeto.

## Change Log

- 2026-08-10: `medir_fila.py` criado (script + `autoteste()`) e medição real executada. M-1 registrado como saiu: precisão 88% (< critério de 95%), recall 79% (≥ 65%). Item de correção de curso aberto em `deferred-work.md`. `208 passed`, sem regressão.
- 2026-08-10: Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Acceptance Auditor: 0 violações, todas as 6 ACs conformes (achado convergente dos 3 revisores classificado como "gap latente, não manifestado nesta execução"). 8 patches aplicados — `comparar` corrigido para usar o gabarito como universo de ids (bug real: id não analisado desaparecia do FN); `falsos_positivos`/`falsos_negativos` separados; `tempfile.mkstemp` + limpeza do HTML temporário; checagem de arquivo antes de rodar; guarda de zero-análises; textos de critério formatados a partir das constantes; nota de CM-2 só quando há códigos propostos. Números de M-1/CM-1 a CM-4/M-2 confirmados inalterados para esta base específica (gabarito e CSV com os mesmos 50 ids, `nao_analisadas=0`) — não foi necessário gastar crédito de API de novo. 1 achado deferido (checagem prévia de conjuntos de id). 2 achados descartados (reuso de helper privado já justificado; formato de `deferred-work.md`). Suíte final: `208 passed`.

## Dev Notes

### Por que `medir_fila.py` é script na raiz com `autoteste()`, não `tests/test_medir_fila.py`

`project-context.md` já registra o padrão: `baseline.py` e `classificador.py` são "módulo executável na raiz" que "carrega `autoteste()` com `assert` chamado no `if __name__ == "__main__":`", e a regra explícita é "não replicar esse padrão **dentro de `plataforma/`**" — não proíbe um terceiro script de medição na raiz seguindo o mesmo padrão. `medir_fila.py` mede o pipeline de verdade (rede, credencial, gasta crédito) — não pode ser um `tests/test_*.py` porque **nenhum teste da suíte pode fazer chamada de rede** (AD-12), e a suíte roda em CI/`bmad-dev-auto` sem credencial. As funções puras (`ler_gabarito`, `comparar`, `verificar_citacoes`) ganham `autoteste()` fabricado à mão, exatamente como `baseline.py`/`classificador.py` já fazem para as suas próprias funções puras.

### Por que `comparar` não importa `baseline.py`/`classificador.py`

`classificador.py` já tem uma função `mede(previsto, gabarito) -> dict` com a mesma fórmula de precisão/recall — matematicamente idêntica ao que `comparar` precisa. Ainda assim, **não importar**: AC1 exige que a comparação prove especificamente o pipeline de `plataforma/`, e a spec desta story nomeia `baseline.py`/`classificador.py` como as duas coisas que a medição **não pode** ser. Importar `mede()` de `classificador.py` acopla o script de medição do Épico 3 a um script de medição de uma fase anterior do projeto (que mede uma pergunta diferente: "o LLM cru supera a linha de base?", não "o pipeline entrega o que promete?"). A fórmula é curta (4 linhas) — duplicar é mais barato que a confusão de manter os dois acoplados.

### Por que `verificar_citacoes` reaproveita `evidencia._passa_checagem_individual`

Diferente do caso acima, aqui a regra **é** a mesma regra (AD-1, FR-6): substring exata + piso de 5 palavras. Reimplementar seria divergir se o piso mudar em um lugar e não no outro — exatamente o tipo de duplicação que `catalogo.py`/`pontuacao.py` já evitam para pesos de sinal (AD-18). Importar um nome com `_` de outro módulo é incomum, mas o precedente já existe neste projeto (`pontuacao.py` lê `catalogo.CATALOGO[...]` diretamente, não duplica a tabela).

### `caminho_saida` desta medição é efêmero

`main()` precisa passar um `caminho_saida` para `grafo.construir_grafo` (assinatura da Story 2.6), mas o HTML gerado aqui não é o entregável do operador — é resíduo da execução real necessário para produzir `Agregados`/`pontuacoes`. Usar `tempfile` (ex.: `tempfile.mktemp(suffix=".html")`) evita que a medição produza um `relatorio-*.html` extra no diretório de `docs/`, que ficaria indistinguível do relatório de verdade e poderia confundir DG-2/DG-3 se alguém commitasse por engano (mesmo coberto por `.gitignore`, é ruído desnecessário).

### Esta story não pode ser "implementada e testada" da forma usual

Diferente de toda story do Épico 1/2, o "código" desta story (Task 1) é 100% testável sem rede — mas o **resultado que a story pede** (Task 2: os números reais de M-1/CM-1 a CM-4/M-2) só existe depois de uma execução real contra a API do Gemini. Se esta sessão não tiver `GOOGLE_API_KEY` configurada, a Task 1 fecha normalmente (código + `autoteste()` passando), e a Task 2 fica documentada como pendente — não é permissão para inventar números. **Nunca simular ou estimar M-1/CM-1 a CM-4 sem rodar de verdade.**

### O que esta story NÃO faz

**Não altera `plataforma/`, `main.py` nem `grafo.py`.** Só consome o que já existe.
**Não reajusta pesos, corte nem catálogo de sinais** mesmo que o resultado medido decepcione — isso seria mover a métrica para caber no resultado, exatamente o que a nota de abertura do Épico 3 proíbe ("o número medido é registrado como saiu").
**Não mede NFR-1 (tempo) nem custo (tokens/chamadas)** — isso é Story 3.2.
**Não demonstra extensibilidade do grafo** — isso é Story 3.3.

### Estrutura de arquivos

```text
medir_fila.py   # NOVO — script de medição, raiz, mesmo padrão de baseline.py/classificador.py
```

**Não criar/tocar nesta story:** qualquer arquivo em `plataforma/`, `main.py`, `tests/`, `docs/gabarito.csv`, `docs/reclamacoes_reclameaqui.csv`, `baseline.py`, `classificador.py`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-12** | Nenhum teste automatizado faz chamada de rede — `medir_fila.py` não é `tests/test_*.py`; `autoteste()` cobre as funções puras sem rede, `main()` (com rede) só roda manualmente |
| **AD-1/FR-6** | `verificar_citacoes` reaproveita a regra existente de `evidencia.py`, não a reimplementa |
| **M-1** | Medição roda sobre a saída real de `plataforma/grafo.py`, nunca sobre `baseline.py`/`classificador.py` |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1] — ACs originais
- [Source: classificador.py#mede, main] — padrão de script de medição na raiz com `autoteste()`; fórmula de precisão/recall a **não** importar (ver Dev Notes)
- [Source: plataforma/evidencia.py#_passa_checagem_individual] — regra de M-2 a reaproveitar, não reimplementar
- [Source: plataforma/grafo.py#construir_grafo] — assinatura `(caminho, caminho_saida)` desde a Story 2.6
- [Source: plataforma/estado.py#Pontuacao, Motivo, Agregados] — campos lidos por esta story, todos já completos
- [Source: docs/gabarito.csv] — colunas `ID_Reclamacao;Empresa;Titulo;Status;fila_prioridade`, valores `sim`/`nao`
- [Source: _bmad-output/project-context.md] — regra de `autoteste()` em módulo executável na raiz, não replicar dentro de `plataforma/`
- [Source: _bmad-output/implementation-artifacts/1-7-as-quatro-contagens-do-operador.md, 2-6-o-arquivo-entregue-nasce-seguro-e-autocontido.md] — precedente de tratamento de AC manual que exige credencial real

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run python -m pytest -q` (via PowerShell) → `208 passed`, sem regressão (`medir_fila.py` não é coletado pela suíte, por design).
- `uv run python medir_fila.py` executado contra a API real do Gemini (`GEMINI_API_KEY` do ambiente, lido pelo SDK como fallback de `GOOGLE_API_KEY`) — 50 reclamações, 5 lotes de 10, `nao_analisadas=0`.

### Completion Notes List

**Medição real (2026-08-10), registrada como saiu — AC3:**

```
M-1: TP=15 FP=2 FN=4  precisão=88%  recall=79%  NÃO PASSOU (critério: precisão≥95%, recall≥65%)
  falsos positivos: ['RA333754555', 'RA607526654']
  falsos negativos: ['RA283758720', 'RA497478786', 'RA678722458', 'RA821218382']
CM-1: ocupação da fila = 34%
CM-2: códigos derrubados = 0/32 (0%) — zero constante é indistinguível de mecanismo morto
CM-3: taxa de produto não nomeado = 42%
CM-4: não analisadas = 0
M-2: citações válidas = 32/32
```

- **M-1 não atingiu o critério de aceitação:** precisão 88% (< 95%), recall 79% (≥ 65%, passa). Limiar **não foi reajustado** — o número é registrado como saiu (AC3). Item de correção de curso aberto em `deferred-work.md` para investigar os 2 FP e 4 FN contra o texto real das reclamações divergentes.
- **Mapeamento FP/FN acima recuperado após o patch de revisão a `comparar()`** (que passou a devolver as duas listas separadas) por consulta local a `docs/gabarito.csv` — os totais (2 FP, 4 FN) batem exatamente com a execução original, sem gastar crédito de API de novo. Os números de M-1/CM-1 a CM-4/M-2 acima são os mesmos da execução real do dia 2026-08-10: o bug de `comparar()` corrigido na revisão (universo de ids = gabarito, não `previsto`) não altera o resultado desta base específica, porque `docs/gabarito.csv` e `docs/reclamacoes_reclameaqui.csv` têm exatamente os mesmos 50 ids e `nao_analisadas=0` nesta execução — o bug só se manifestaria se os conjuntos de id divergissem ou se alguma reclamação tivesse ficado sem análise.
- **CM-1 (34%) está abaixo do alerta de 40%** — a fila ainda ordena.
- **CM-2 em zero constante** — nenhuma citação real foi derrubada nesta execução; a nota "indistinguível de mecanismo morto" se aplica: só o caso sintético da Story 1.4 exercita a derrubada de fato.
- **CM-3 (42%)** — quase metade da base não tem produto nomeado; consistente com a natureza da base sintética (§1 do PRD já registra essa limitação, coberta pela ressalva de FR-18/AD-14 no relatório).
- **M-2: 100% das citações são literais** (32/32) — confirma em execução real a garantia que `evidencia.verificar` já dava por construção.
- Nenhum desvio de design em relação ao que a story especificou. `medir_fila.py` segue o padrão de `baseline.py`/`classificador.py` (script na raiz, `autoteste()`, sem `tests/test_*.py`).

### File List

| Arquivo | Tipo |
|---|---|
| `medir_fila.py` | novo |
