# Story 1.3: Ingestão que rejeita base inválida antes de gastar

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a operador,
I want que um CSV com schema errado seja recusado antes de qualquer chamada paga,
so that eu descubra o problema pelo nome dele e não pela fatura da API.

## Acceptance Criteria

**AC1 — CSV válido produz 50 `Reclamacao`, sem BOM colado e com data ISO-8601**

**Given** `docs/reclamacoes_reclameaqui.csv`
**When** `carregar()` executa
**Then** produz 50 `Reclamacao` lidas com `utf-8-sig` e separador `;`
**And** o nome da primeira coluna não carrega BOM colado (`ﬄID_Reclamacao` não ocorre)
**And** cada `data` está em ISO-8601 (`AAAA-MM-DD`), convertida de `DD/MM/AAAA`

**AC2 — Coluna obrigatória ausente encerra antes de qualquer chamada paga (FR-3)**

**Given** um CSV sem uma das sete colunas esperadas
**When** `carregar()` executa
**Then** levanta `ValueError` nomeando a(s) coluna(s) faltante(s)
**And** zero chamadas ao modelo foram feitas — `carregar()` não tem como fazer uma, ela não importa `google.genai`

**AC3 — `ID_Reclamacao` repetido encerra nomeando o identificador (FR-3)**

**Given** um CSV com `ID_Reclamacao` repetido
**When** `carregar()` executa
**Then** levanta `ValueError` nomeando o identificador repetido
**And** zero chamadas ao modelo foram feitas

**AC4 — CSV sem linha de dado encerra com causa nomeada (AD-13)**

**Given** um CSV com cabeçalho e nenhuma linha de dado
**When** `carregar()` executa
**Then** levanta `ValueError` com mensagem clara, antes de qualquer processamento posterior

**AC5 — Determinismo entre execuções (NFR-8)**

**Given** o mesmo arquivo processado duas vezes
**When** as duas chamadas a `carregar()` terminam
**Then** o conjunto de identificadores produzido é idêntico nas duas

**AC6 — Sem SDK do modelo nos imports (AD-7)**

**Given** o módulo `plataforma/ingestao.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai`, direta nem transitivamente

## Tasks / Subtasks

- [x] **Task 1 — Criar `plataforma/ingestao.py`** (AC: 1, 2, 3, 4, 6)
  - [x] Declarar `COLUNAS_ESPERADAS` como tupla das sete colunas do CSV de origem: `ID_Reclamacao`, `Data`, `Empresa`, `Titulo`, `Descricao`, `Cidade_Estado`, `Status` (fonte: `state-contract.md`, confirmado contra o arquivo real)
  - [x] Escrever `carregar(caminho: str) -> list[Reclamacao]`, único nó desta story
  - [x] Abrir com `encoding="utf-8-sig"` e `csv.DictReader(..., delimiter=";")` — `utf-8` cru cola BOM no nome da primeira coluna (armadilha já documentada em `project-context.md:47`)
  - [x] Checar `leitor.fieldnames` contra `COLUNAS_ESPERADAS` **antes** de iterar as linhas — falha rápida, sem ler dado nenhum, se faltar coluna
  - [x] Levantar `ValueError` nomeando a(s) coluna(s) faltante(s) e a lista esperada (AC2)
  - [x] Iterar as linhas construindo `Reclamacao` (`id=ID_Reclamacao`, `data=`data convertida, `empresa=Empresa`, `titulo=Titulo`, `texto=Descricao`, `cidade_estado=Cidade_Estado`, `status=Status`), acumulando num `set` de ids vistos
  - [x] Levantar `ValueError` nomeando o `ID_Reclamacao` repetido assim que ele se repetir (AC3) — não esperar o arquivo inteiro para reportar
  - [x] Converter `Data` de `DD/MM/AAAA` para ISO-8601 com `datetime.strptime(valor, "%d/%m/%Y").strftime("%Y-%m-%d")` (stdlib, sem dependência nova)
  - [x] Capturar `ValueError` de `strptime` e relevantar nomeando `id` da linha e o valor de `Data` observado — sem isso o erro cru do stdlib escapa sem dizer qual linha, quebrando o padrão de mensagem que `config.py` já fixou. Não é AC coberta por teste obrigatório; é consistência de estilo
  - [x] Depois do laço, se a lista resultante estiver vazia, levantar `ValueError` nomeando o caminho do arquivo (AC4) — cabeçalho sem nenhuma linha de dado cai aqui, não em erro de coluna
  - [x] Retornar a lista de `Reclamacao`
  - [x] Docstring de módulo no padrão de `config.py`: uma linha de propósito, parágrafo com o porquê não-óbvio (BOM, fail-fast de coluna, id como identificador de origem), tudo em português
  - [x] Comentário explica o porquê, nunca o quê — citar a fonte (`state-contract.md`, `FR-3`, `AD-13`) como os módulos anteriores já fazem

- [x] **Task 2 — Criar `tests/test_ingestao.py`** (AC: 1, 2, 3, 4, 5, 6)
  - [x] Caso feliz: `carregar("docs/reclamacoes_reclameaqui.csv")` devolve 50 itens; primeiro `id` bate com a primeira linha real do arquivo; toda `data` casa com `AAAA-MM-DD` (regex ou `datetime.fromisoformat`)
  - [x] Determinismo: chamar `carregar()` duas vezes sobre o mesmo caminho e comparar `{r["id"] for r in resultado}` — precisa ser o mesmo `set` (AC5)
  - [x] Coluna faltante: escrever um CSV sintético em `tmp_path` (não tocar `docs/`) sem `Cidade_Estado`, esperar `ValueError` cuja mensagem cite `"Cidade_Estado"`
  - [x] Id duplicado: CSV sintético de 3 linhas com o mesmo `ID_Reclamacao` em duas delas, esperar `ValueError` citando o id repetido
  - [x] Cabeçalho sem linha de dado: CSV sintético só com a linha de cabeçalho, esperar `ValueError`
  - [x] BOM: escrever o CSV sintético com `encoding="utf-8-sig"` e confirmar que `carregar()` não quebra por causa do BOM (prova negativa de que a leitura crua não é usada)
  - [x] Nenhum teste depende de rede ou de `GOOGLE_API_KEY` (AD-12) — todos os CSVs sintéticos são escritos à mão no teste

- [x] **Task 3 — Registrar `plataforma.ingestao` na verificação de AD-7** (AC: 6)
  - [x] Em `tests/test_import_sem_credencial.py`, acrescentar `"plataforma.ingestao"` à lista `MODULOS`
  - [x] **Não** acrescentar `ingestao` ao `parametrize` de `test_modulos_folha_so_importam_o_que_a_story_permite` em `tests/test_contrato.py` — ver Dev Notes, esse teste é especificamente para módulos-folha que não importam nada de `plataforma/`, e `ingestao.py` importa `estado` por desenho (a aresta `ingestao --> estado` já está desenhada em `ARCHITECTURE-SPINE.md`)
  - [x] Rodar `uv run pytest` e confirmar verde

## Dev Notes

### O que esta story NÃO faz — leia antes de codar

**Fatiamento em lotes e emissão de `Send` não são desta story.** A Story 1.2 registrou como dívida que `AD-17` fala em "quem fatia é `carregar`", mas o épico real move essa parte para a **Story 1.6** ("Fan-out por lote com falha absorvida") — foi lá, não aqui, que as ACs sobre `tamanho_lote`, fusão do lote residual de 1 e `Send` acabaram. **Esta story (1.3) só lê, valida schema, valida unicidade de id e converte data.** Não importar `plataforma.config`, não fatiar nada, não montar `Send`. Se você chegou aqui achando que precisa ler `TAMANHO_LOTE`, está na story errada.
[Source: epics.md#Story 1.3 vs #Story 1.6 — a lista de ACs de 1.3 não menciona lote nenhum; ARCHITECTURE-SPINE.md#AD-17]

**Validação do valor de `Status` contra o `Literal` de cinco opções não é desta story.** Nenhuma AC pede — só coluna presente, id único e cabeçalho com dado. Não inventar validação adicional.

### Por que `ingestao.py` não entra no teste de módulos-folha

`tests/test_contrato.py::test_modulos_folha_so_importam_o_que_a_story_permite` existe para módulos que **não importam nada de `plataforma/`** — hoje `estado`, `catalogo`, `config`. A própria docstring do teste diz "nenhum import de `plataforma/`". `ingestao.py` quebra essa premissa por desenho: ele precisa de `Reclamacao` para construir o retorno tipado, e a spine já desenha essa aresta (`ingestao --> estado` no diagrama de `ARCHITECTURE-SPINE.md`). A AC6 desta story ("não importa `google.genai`") já está coberta por `test_import_sem_credencial.py`, que testa exatamente isso e não exige lista-branca fechada de terceiros. **Não force `ingestao` para dentro do teste de folha** — vai falhar contra a própria definição do teste (`permitidos` não incluiria `"plataforma"` nem `"."`) e forçar a exceção ali confundiria "não importa nada de `plataforma/`" com "importa só o que está pré-aprovado", que são regras diferentes.

### O que a Story 1.1 e 1.2 estabeleceram e este módulo deve seguir

- **Docstring de módulo:** uma linha de propósito terminada em ponto, linha em branco, parágrafo com o porquê não-óbvio. Sem `Args/Returns`, sem lista de funções.
- **Comentário explica o porquê e cita a fonte** (`FR-3`, `AD-13`, `state-contract.md`). Nunca o quê.
- **Tudo em português:** módulo, função, parâmetro, docstring, mensagem de erro.
- **Type hint só na assinatura de função pública** — `carregar(caminho: str) -> list[Reclamacao]`.
- **Asserção/erro com mensagem que nomeia o valor observado**, no padrão que `config.py` já fixou: nunca um `ValueError` cru do stdlib passando batido.
- **`ingestao.py` não importa `google.genai`**, nem direta nem transitivamente — mesmo padrão de AD-7 que `estado`, `catalogo` e `config` já respeitam.
[Source: plataforma/estado.py, plataforma/catalogo.py, plataforma/config.py, project-context.md]

### Formato do arquivo de origem — validado contra o CSV real

| Característica | Valor |
|---|---|
| Separador | `;` |
| Codificação | UTF-8 **com BOM** — ler com `utf-8-sig` |
| Colunas (nesta ordem no arquivo real) | `ID_Reclamacao`, `Data`, `Empresa`, `Titulo`, `Descricao`, `Cidade_Estado`, `Status` |
| Formato de data | `DD/MM/AAAA` |
| Linhas de dado | 50, todos os `ID_Reclamacao` já únicos na origem |

Mapeamento coluna do CSV → campo de `Reclamacao`: `ID_Reclamacao`→`id`, `Data`→`data` (convertida), `Empresa`→`empresa`, `Titulo`→`titulo`, **`Descricao`→`texto`** (nome diferente, não é 1:1), `Cidade_Estado`→`cidade_estado`, `Status`→`status`.
[Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md#Formato do arquivo de origem — verificado nesta sessão lendo o cabeçalho real de docs/reclamacoes_reclameaqui.csv]

### Contrato de retorno

`plataforma/estado.py` já define `Reclamacao` — não redeclarar campos aqui, importar de lá:

```python
class Reclamacao(TypedDict):
    id: str
    data: str          # ISO-8601
    empresa: str
    titulo: str
    texto: str
    cidade_estado: str
    status: Literal["Respondida", "Não respondida", "Resolvido", "Não resolvido", "Em réplica"]
```

TypedDict aceita construção por chamada (`Reclamacao(id=..., data=..., ...)`), que é dict puro em runtime — sem necessidade de framework de validação adicional.
[Source: plataforma/estado.py]

### Testando sem rede (AD-12)

Todo teste de erro (coluna faltante, id duplicado, CSV vazio) usa CSV **sintético escrito à mão** em `tmp_path`, nunca editando `docs/reclamacoes_reclameaqui.csv`, que é o corpus de referência usado pelo caso feliz e por `M-1`/`M-2` no Épico 3. Nenhum teste faz chamada de rede — `ingestao.py` nem tem como, já que não importa o SDK.

### Estrutura de arquivos

```text
plataforma/
  ingestao.py          # NOVO — carregar(caminho) -> list[Reclamacao]
tests/
  test_ingestao.py      # NOVO
  test_import_sem_credencial.py  # UPDATE — plataforma.ingestao em MODULOS
```

**Não criar nesta story:** `analise.py`, `evidencia.py`, `pontuacao.py`, `agregacao.py`, `relatorio.py`, `grafo.py`, `main.py`, `templates/`.

**Não tocar:** `baseline.py`, `classificador.py`, `docs/reclamacoes_reclameaqui.csv` (só leitura), `plataforma/config.py` (esta story não o usa).

### Bibliotecas e versões

Nada a instalar. `csv` e `datetime` são stdlib. Nenhuma linha nova em `pyproject.toml`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-7** | `ingestao.py` não importa `google.genai`; verificado por `test_import_sem_credencial.py` |
| **AD-12** | Testes de erro usam CSV fabricado à mão, sem rede |
| **AD-13** (parcial) | CSV vazio (cabeçalho sem linha de dado) levanta erro nomeado — a parte "não escreve arquivo" não se aplica aqui, pois `ingestao.py` não escreve nada |
| **FR-3** | Coluna ausente ou id duplicado encerram antes de qualquer chamada paga |
| **NFR-8** | Duas execuções sobre o mesmo arquivo produzem o mesmo conjunto de ids — trivialmente verdadeiro sem estado mutável entre chamadas, mas coberto por teste explícito |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3] — ACs originais
- [Source: _bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md#AD-7, AD-12, AD-13, AD-17] — invariantes; AD-17 confirma que o fatiamento é da Story 1.6
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md#Formato do arquivo de origem] — schema do CSV e regras de identificador
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/SPEC.md#CAP-1] — intent e success de ingestão
- [Source: plataforma/estado.py] — contrato `Reclamacao`
- [Source: plataforma/config.py, plataforma/catalogo.py] — padrão de módulo e de mensagem de erro das stories 1.1/1.2
- [Source: tests/test_contrato.py, tests/test_import_sem_credencial.py] — testes existentes e por que `ingestao` não entra no parametrize de folha
- [Source: _bmad-output/implementation-artifacts/1-2-configuracao-validada-antes-de-qualquer-chamada-paga.md#Dívidas conhecidas] — a aresta `config -.-> ingestao` ausente no diagrama, e a base com menos de 2 reclamações, ambas registradas como não resolvidas por esta story (a segunda é problema de fatiamento, Story 1.6)
- [Source: docs/reclamacoes_reclameaqui.csv] — cabeçalho real lido nesta sessão, confirma a ordem e os nomes exatos das sete colunas

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-auto)

### Debug Log References

- `uv run pytest -q` — 70 passed (baseline era 64; 6 testes novos em `tests/test_ingestao.py`, mais o módulo extra coberto por `test_import_sem_credencial.py`)
- `uv run python -c "import plataforma.ingestao, sys; assert not [m for m in sys.modules if m.startswith('google')]"` — sem saída, sem erro (AD-7 confirmado)
- Pós-revisão (Blind Hunter + Edge Case Hunter): `uv run pytest -q` — 72 passed. Guarda contra linha de CSV com menos campos que o cabeçalho acrescentada; dois testes de mensagem de erro reforçados; teste de arquivo zero-byte acrescentado.

### Completion Notes List

- `plataforma/ingestao.py` criado com `carregar(caminho: str) -> list[Reclamacao]`, seguindo exatamente as tasks do spec: `COLUNAS_ESPERADAS`, fail-fast de coluna via `fieldnames`, unicidade de id via `set` com erro no primeiro repeat, conversão de `Data` com `strptime`/`strftime` e erro renomeado com id da linha, e erro nomeando o caminho quando a lista final está vazia.
- `tests/test_ingestao.py` criado com os 6 casos do Task 2 (caso feliz, determinismo, coluna faltante, id duplicado, CSV vazio, prova de BOM via escrita `utf-8-sig` do CSV sintético).
- `tests/test_import_sem_credencial.py` atualizado: `"plataforma.ingestao"` acrescentado a `MODULOS`.
- `ingestao` **não** foi acrescentado ao `parametrize` de `test_modulos_folha_so_importam_o_que_a_story_permite` em `tests/test_contrato.py`, conforme instrução explícita do spec e das Dev Notes — esse teste é só para módulos que não importam nada de `plataforma/`.
- Nenhum desvio do spec. Único ajuste feito durante a implementação: o primeiro `id` real do CSV é `"RA249827706"` (confirmado por leitura direta do arquivo, não `"RA2498277060"` como um primeiro rascunho do teste assumiu) — corrigido antes de rodar a suíte.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/ingestao.py` | novo |
| `tests/test_ingestao.py` | novo |
| `tests/test_import_sem_credencial.py` | modificado |
