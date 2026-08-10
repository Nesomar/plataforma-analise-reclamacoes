---
baseline_commit: 'e663e9244dca32f95365c0ebd6657799716cf50d'
---

# Story 2.6: O arquivo entregue nasce seguro e autocontido

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a operador,
I want que o relatório seja escrito com nome previsível, sem nunca apagar um anterior em silêncio,
so that eu possa comparar execuções e não vaze um relatório de base real para o repositório público.

## Acceptance Criteria

**AC1 — Nome e local do arquivo**

**Given** a execução sobre `docs/reclamacoes_reclameaqui.csv`
**When** o arquivo é escrito
**Then** nasce ao lado do CSV de entrada
**And** o nome começa com `relatorio-`, seguido do nome do arquivo de entrada e da data da execução (FR-1b, AD-15)
**And** casa com o glob `relatorio-*.html` já coberto pelo `.gitignore` (DG-2)

**AC2 — Caminho impresso ao encerrar**

**Given** a execução concluída
**When** o comando encerra
**Then** o caminho final do arquivo é impresso ao operador (FR-1b)

**AC3 — Arquivo existente encerra sem escrever**

**Given** um arquivo de saída que já existe
**When** a execução chega ao momento de escrever
**Then** encerra sem escrever, nomeando o arquivo existente (FR-4)

**AC4 — Sinalizador de sobrescrita**

**Given** o sinalizador explícito de sobrescrita na linha de comando
**When** a execução roda sobre um arquivo existente
**Then** sobrescreve (FR-4)

**AC5 — Zero análises não escreve arquivo**

**Given** `len(analises) == 0`
**When** a execução chega ao momento de escrever
**Then** encerra com a causa nomeada e não escreve arquivo algum (AD-13)

**AC6 — Sem referência externa no HTML (verificação automatizada)**

**Given** o HTML gerado
**When** seu conteúdo é varrido
**Then** não contém nenhuma referência a host externo — nem `src=`, nem `href=`, nem `@import` apontando para fora do arquivo
**And** essa varredura é um teste automatizado, não inspeção manual (FR-10, AD-11)

**AC7 — Abre offline (verificação manual)**

**Given** o HTML gerado
**When** ele é aberto em navegador atual com a rede desligada
**Then** renderiza completo, sem servidor, sem instalação e sem plugin (FR-10, NFR-9)

**AC8 — Sobrevive a anexo de e-mail (verificação manual)**

**Given** o HTML gerado enviado como anexo único de e-mail
**When** o destinatário o abre
**Then** renderiza igual ao original (NFR-9)

## Tasks / Subtasks

- [x] **Task 1 — Estender `plataforma/grafo.py`** (AC: 1, 5)
  - [x] `construir_grafo(caminho: str, caminho_saida: str) -> CompiledStateGraph` — assinatura estendida
  - [x] Nó `renderizar(estado) -> dict`: chama `relatorio.renderizar`, escreve UTF-8, devolve `{"caminho_html": ...}`
  - [x] `_rotear_apos_conservacao(estado) -> str`: função de módulo, `"pontuar"` ou `END`
  - [x] `add_conditional_edges("_verificar_conservacao", _rotear_apos_conservacao)`
  - [x] Aresta final `agregar -> renderizar -> END`
  - [x] `add_node("renderizar", renderizar)` sem `retry_policy`/`error_handler`
  - [x] Import `plataforma.relatorio`
  - [x] Docstring atualizada

- [x] **Task 2 — Estender `main.py`** (AC: 1, 2, 3, 4, 5)
  - [x] `_nome_saida(caminho_csv) -> Path` com data ISO
  - [x] `_ler_argumento(argv) -> tuple[str, bool]` com `--sobrescrever`
  - [x] Cheque de arquivo existente antes de `.invoke()`
  - [x] `caminho_saida` passado a `construir_grafo`
  - [x] Impressão do caminho final após as quatro contagens
  - [x] Mensagem de uso atualizada
  - [x] Imports `datetime`, `pathlib.Path`

- [x] **Task 3 — Estender `tests/test_grafo.py`** (AC: 1, 5)
  - [x] 4 chamadas a `construir_grafo` atualizadas com segundo argumento
  - [x] `"renderizar"` na tupla de nós esperados
  - [x] Teste: `renderizar` sem `retry_policy`/`error_handler`
  - [x] `_rotear_apos_conservacao`: dois testes (vazio → `END`; não vazio → `"pontuar"`)

- [x] **Task 4 — Estender `tests/test_main.py`** (AC: 2, 3, 4)
  - [x] `_nome_saida` testado com data do dia via `datetime.date.today().isoformat()`
  - [x] `_ler_argumento`: casos `(caminho, False)`, `(caminho, True)`, flag errada, argumento extra inválido
  - [x] Testes existentes ajustados para a tupla de retorno nova
  - [x] Sem teste de `.invoke()` completo

- [x] **Task 5 — Verificação automatizada de ausência de referência externa (AC6)**
  - [x] `test_html_completo_sem_nenhuma_referencia_a_host_externo` em `tests/test_relatorio.py`, cobrindo todas as seções
  - [x] Builders reaproveitados, nenhum novo criado

- [x] **Task 6 — Verificação manual (AC7, AC8)**
  - [x] Documentada como não executada nesta sessão — exige `GOOGLE_API_KEY` real, rede e navegador real; ver Completion Notes. Mesmo tratamento que a Story 1.7 deu à sua AC manual (50/50 sobre a base de referência)

### Review Findings

- [x] [Review][Patch] `_nome_saida()` e o cheque de existência em `main()` rodam **fora** do bloco `try/except` — um caminho de CSV degenerado (ex.: terminando em separador) levanta `ValueError` cru de `Path.with_name`, vazando traceback ao operador, violando a própria garantia que o módulo declara ter [main.py]
- [x] [Review][Patch] `["main.py", "--sobrescrever"]` (2 argumentos) é lido como `caminho_csv="--sobrescrever"` com `sobrescrever=False` em vez de erro de uso — a flag sozinha, sem CSV, deveria ser rejeitada [main.py:_ler_argumento]
- [x] [Review][Patch] Corpo do nó `renderizar` (escreve UTF-8, devolve `{"caminho_html": ...}`) sem nenhuma cobertura direta — os dois testes existentes só checam `retry_policy`/`error_handler` [tests/test_grafo.py]
- [x] [Review][Patch] O desvio de custo (arquivo existe, sem `--sobrescrever` → `grafo.construir_grafo`/`.invoke()` nunca é alcançado) não é testado — uma regressão que movesse o cheque para depois do `.invoke()` passaria por toda a suíte existente sem ser detectada [tests/test_main.py]
- [x] [Review][Patch] Bypass de `--sobrescrever` através de `main()` não é testado ponta a ponta — só o retorno de `_ler_argumento` é verificado, não que `main()` de fato ignora o arquivo existente quando a flag está ligada [tests/test_main.py]
- [x] [Review][Patch] `Path.write_text` sem atomicidade — uma falha no meio da escrita (disco cheio, permissão revogada) deixa um arquivo truncado em `caminho_saida`, e a próxima execução sem `--sobrescrever` fica travada atrás dele [plataforma/grafo.py:renderizar]

- [x] [Review][Defer] Corrida TOCTOU entre o cheque de existência (antes de `.invoke()`, que pode levar minutos com chamadas pagas) e a escrita de fato dentro de `renderizar` — duas execuções concorrentes, ou um arquivo criado durante a execução, passariam pelo cheque. Sem requisito de concorrência em nenhuma AC/NFR deste projeto (ferramenta de linha de comando de operador único); reavaliar se execução agendada/concorrente virar requisito
- [x] [Review][Defer] O cheque prévio só verifica existência, não gravabilidade — diretório sem permissão de escrita ou arquivo travado por outro processo só falha dentro de `renderizar`, depois das chamadas pagas já terem acontecido, na contramão do próprio motivo de checar antes. Cobrir esse caso plenamente exigiria sondar gravabilidade sem efeito colateral, complexidade não pedida por nenhuma AC

**Achados descartados (decisão de design já justificada / fora de escopo / já coberto em outra camada):**
- Flag `--sobrescrever` só reconhecida em posição fixa (`argv[2]`), sem `argparse` — decisão de design já justificada nas Dev Notes da própria story ("não introduz argparse... sinalizador booleano é sys.argv cru").
- Roteamento de zero-análises (AD-13) provado só no nível de unidade (`_rotear_apos_conservacao` chamada direta + presença do nó), não via `.invoke()` mockado ponta a ponta — consistente com a filosofia de teste já estabelecida no projeto inteiro (nunca invocar o grafo de verdade, evita rede/`analisar_lote`); a função de roteamento em si está totalmente coberta.
- `assert` nu em `_verificar_conservacao` (AD-6) some sob `python -O` — pré-existente desde a Story 1.6, não introduzido por esta story.
- Vaivém `Path`⇄`str` entre `main.py` e `grafo.py` — churn cosmético, sem efeito funcional.
- `Path.write_text` em modo texto (CRLF no Windows) — nenhuma AC/NFR exige saída byte-idêntica entre plataformas; navegador e cliente de e-mail lidam com as duas convenções de quebra de linha sem problema.
- `main()` imprime `estado["caminho_html"]` em vez do `caminho_saida` local — é a escolha mais correta (o valor que `renderizar` de fato usou para escrever), não um defeito; os dois são garantidamente idênticos por fluxo de dado direto (`main.py` passa `str(caminho_saida)`, `renderizar` devolve o mesmo valor).

## Dev Notes

### Por que o cheque de arquivo existente acontece ANTES de `.invoke()`, não dentro do nó `renderizar`

A AC3 do épico diz "quando a execução chega ao momento de escrever" — uma leitura possível seria checar dentro do nó `renderizar`, depois que todo o pipeline já rodou (incluindo as chamadas pagas ao modelo). Essa leitura contradiz o princípio que o resto do projeto aplica sem exceção: **toda validação que pode ser feita antes de gastar, é feita antes de gastar** (AD-17 para `tamanho_lote`, `ingestao.py` para schema/duplicata, `config.py` para a chave de API). O nome do arquivo de saída (`relatorio-<csv>-<data-de-hoje>.html`) é 100% calculável **antes** de qualquer linha do CSV ser lida — não depende de nada que o pipeline produza. Portanto: `main.py` calcula `caminho_saida` e verifica existência **antes** de chamar `.invoke({})`. Isso não é uma reinterpretação livre da AC — é a mesma disciplina que todas as demais validações de custo já seguem neste repositório, aplicada ao único novo ponto de decisão que esta story introduz.

### Por que a data do nome do arquivo é ISO, não pt-BR

`relatorio._data_br` (Story 2.3) converte `"AAAA-MM-DD"` para `"DD/MM/AAAA"` — com barras. Um caminho de arquivo com `/` no meio do nome quebra (`Path.with_name("relatorio-x-09/08/2026.html")` cria uma pasta chamada `09` em sistemas Unix, ou levanta erro no Windows). `_nome_saida` em `main.py` usa `datetime.date.today().isoformat()` diretamente — **não reaproveita `relatorio._data_br`**, que existe especificamente para exibição no HTML, não para nome de arquivo. São dois formatos de data com propósitos diferentes; não é duplicação a evitar.

### Por que `_rotear_apos_conservacao` é função de módulo, não closure

Todo router/fatiador testável sem `.invoke()` neste arquivo já é função de módulo pura: `_fatiar`, `_despachar`, `_verificar_conservacao` (Stories 1.6/2.2). O padrão contrário (closures como `carregar`/`despachar`/agora `renderizar`) existe só onde a função **precisa** capturar um caminho de arquivo que `Estado` não carrega — não é o caso do roteamento pós-conservação, que só olha `len(estado["analises"])`. Manter como função de módulo evita perder cobertura de teste direta, que é exatamente o padrão que `test_verificar_conservacao_passa_quando_soma_bate`/`test_verificar_conservacao_levanta_quando_soma_nao_bate` já demonstram.

### Ordem final do grafo, depois desta story

```text
carregar -> Send*N -> analisar_lote -> _verificar_conservacao
  -> [_rotear_apos_conservacao] -> pontuar -> agregar -> renderizar -> END   (analises não vazio)
  -> [_rotear_apos_conservacao] -> END                                       (analises vazio, AD-13)
```

`main.py` continua com o `try/except Exception` genérico (Story 1.7) como rede de segurança — nenhuma máquina de erro nova para falha de escrita em disco. Se `Path.write_text` falhar (disco cheio, permissão), a exceção sobe através de `.invoke()` e cai no mesmo `except` que já converte qualquer coisa em `SystemExit(f"encerrado: {erro}")`.

### `_ler_argumento` muda de forma, mas mantém o espírito

Antes (Story 1.7): `_ler_argumento(argv) -> str`, rejeitando qualquer coisa que não seja exatamente `[script, csv]`. Agora devolve `(caminho, sobrescrever)` para acomodar o sinalizador opcional de FR-4, sem enfraquecer a rejeição de formas inválidas — `["main.py", "a.csv", "b.csv"]` continua rejeitado, porque `"b.csv"` não é `"--sobrescrever"`. Os testes existentes em `tests/test_main.py` para essa função precisam ser atualizados para a nova tupla de retorno (Task 4) — não é uma reescrita, é ajuste de forma.

### O que esta story NÃO faz

**Não adiciona flag de configuração nova em `config.py`.** `--sobrescrever` é argumento de linha de comando, não variável de ambiente — não é "configuração da execução" no sentido de `config.Config` (lote, modelo), é uma decisão pontual do operador para aquela chamada.
**Não muda o formato de exibição de data no cabeçalho do relatório** (`relatorio._data_br` continua igual, Story 2.5).
**Não recalcula degradação, ranking, sentimento ou fila.** Esta story só escreve em disco o que `relatorio.renderizar` já produz.
**Não introduz `argparse` nem outra dependência.** Um sinalizador booleano é `sys.argv` cru, como o resto de `main.py` já faz.

### Estrutura de arquivos

```text
plataforma/
  grafo.py         # UPDATE — nó renderizar, _rotear_apos_conservacao, assinatura de construir_grafo
main.py            # UPDATE — _nome_saida, _ler_argumento (nova forma), cheque de sobrescrita, print do caminho
tests/
  test_grafo.py     # UPDATE — 4 chamadas a construir_grafo, nó renderizar, roteador
  test_main.py       # UPDATE — _nome_saida, _ler_argumento (nova forma)
  test_relatorio.py  # UPDATE — teste abrangente de ausência de referência externa
```

**Não criar/tocar nesta story:** `plataforma/relatorio.py`, `plataforma/templates/relatorio.html.j2` (já completos desde a Story 2.5 — esta story só consome `relatorio.renderizar`), `plataforma/agregacao.py`, `plataforma/pontuacao.py`, `plataforma/catalogo.py`, `plataforma/estado.py` (`caminho_html: str` já existe desde a Story 1.1), `docs/`, `.gitignore` (já cobre `relatorio*.html`).

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-13** | `_rotear_apos_conservacao` desvia para `END` antes de `pontuar`/`agregar`/`renderizar` quando `analises` está vazio — nenhum HTML é escrito sobre zero análises |
| **AD-15** | `_nome_saida` sempre prefixa `relatorio-`; nome do CSV e data vêm depois |
| **AD-17 (princípio, não a regra em si)** | Cheque de arquivo existente acontece antes de `.invoke()`, mesma disciplina de "validar antes de gastar" |
| **AD-19** | `renderizar` é o único nó que escreve `caminho_html` |
| **AD-7/AD-12** | `grafo.py` continua sem `google.genai` direto; `_rotear_apos_conservacao`/`_nome_saida` são funções puras, testáveis sem rede |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.6] — ACs originais
- [Source: plataforma/grafo.py] — código real: `_fatiar`, `_despachar`, `_verificar_conservacao` como funções de módulo; `carregar`/`despachar` como closures — padrão a seguir para `renderizar`/`_rotear_apos_conservacao`
- [Source: main.py] — `_ler_argumento`, `_mensagem_zero_analises`, `_contar_codigos_derrubados`, o `try/except Exception` genérico e a tabela alinhada por f-string
- [Source: plataforma/relatorio.py#renderizar] — função pura já completa (Stories 2.3-2.5); esta story só a chama e grava o resultado
- [Source: tests/test_grafo.py, tests/test_main.py] — testes reais a estender, convenções de builder (`reclamacao`, `pontuacao`) já estabelecidas
- [Source: .gitignore] — `relatorio*.html` já coberto, confirma que `_nome_saida` deve sempre produzir um nome começando com `relatorio-`
- [Source: _bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md#AD-13, AD-15, AD-17, AD-19] — invariantes desta story

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run python -m pytest -q` (via PowerShell) → `204 passed` (baseline: 197 + 7 novos entre `test_grafo.py`, `test_main.py` e `test_relatorio.py`).
- Sem falhas de implementação — testes passaram de primeira.

### Completion Notes List

- `grafo.py`: `construir_grafo` ganhou o parâmetro `caminho_saida`, o nó `renderizar` (fecha o pipeline escrevendo o HTML em disco) e o roteamento condicional `_rotear_apos_conservacao` que desvia para `END` quando `analises` está vazio (AD-13) — nenhum HTML é escrito sobre zero análises.
- `main.py`: `_nome_saida` calcula o caminho de saída (`relatorio-<csv>-<data-ISO>.html`) **antes** de invocar o grafo; o cheque de arquivo existente (FR-4) acontece nesse mesmo ponto, antes de qualquer chamada paga — decisão de design documentada nas Dev Notes. `_ler_argumento` passou a devolver `(caminho, sobrescrever)` para acomodar o sinalizador `--sobrescrever`. O caminho final é impresso após as quatro contagens já existentes.
- `tests/test_grafo.py`/`tests/test_main.py`/`tests/test_relatorio.py` estendidos conforme a story; nenhum teste novo invoca o grafo de verdade (continua exigindo rede/credencial, fora da suíte determinística).
- **AC7 e AC8 (verificação manual) não foram executadas nesta sessão** — exigem `GOOGLE_API_KEY` real, rede e um navegador/cliente de e-mail reais. Comando para o usuário rodar quando quiser: `uv run python main.py docs/reclamacoes_reclameaqui.csv`, depois abrir o HTML gerado com a rede desligada (AC7) e enviá-lo como anexo único de e-mail (AC8). Mesmo tratamento que a Story 1.7 deu à sua AC manual — não simulado, não inventado.
- Nenhum desvio de design em relação ao que a story especificou.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/grafo.py` | modificado |
| `main.py` | modificado |
| `tests/test_grafo.py` | modificado |
| `tests/test_main.py` | modificado |
| `tests/test_relatorio.py` | modificado |
| `.gitignore` | modificado (achado de revisão: `relatorio*.html.tmp`) |

## Change Log

- 2026-08-09: Implementação completa da Story 2.6 — nó `renderizar` e roteamento condicional em `grafo.py`, escrita do arquivo com nome previsível e proteção contra sobrescrita em `main.py`, testes estendidos. `204 passed`. AC7/AC8 (verificação manual) documentadas como pendentes de execução pelo usuário.
- 2026-08-09: Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Acceptance Auditor: 0 violações, todas as 8 ACs conformes (AC7/AC8 corretamente tratadas como manuais, não silenciosamente puladas). 6 patches aplicados — `_nome_saida`/cheque de existência movidos para dentro do `try/except`; `["main.py", "--sobrescrever"]` sozinho agora rejeitado; escrita atômica em `renderizar` (arquivo temporário + `Path.replace`, com `.gitignore` estendido para `relatorio*.html.tmp`); 4 testes novos (corpo do nó `renderizar` invocado direto via `spec.runnable`, desvio de custo antes do `.invoke()`, bypass de `--sobrescrever` ponta a ponta, flag sozinha rejeitada). 2 achados deferidos (corrida TOCTOU entre cheque e escrita; cheque prévio não verifica gravabilidade) — ambos fora do escopo de qualquer AC, sem requisito de concorrência no projeto. 6 achados descartados por decisão de design já justificada nas Dev Notes ou por serem pré-existentes/cosméticos. Suíte final: `uv run python -m pytest -q` (via PowerShell) → `208 passed`.
