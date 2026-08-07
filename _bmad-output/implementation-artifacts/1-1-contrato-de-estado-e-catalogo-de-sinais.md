---
baseline_commit: d4b529c077d5a2e373e8a3245cae3761a2e1fa4a
---

# Story 1.1: Contrato de estado e catálogo de sinais

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a desenvolvedor do pipeline,
I want o contrato de estado tipado e o catálogo de sinais em módulos próprios,
so that nenhuma etapa posterior invente forma de dado nem repita um código de sinal como literal solto.

## Acceptance Criteria

**AC1 — `estado.py` expõe o contrato completo**

**Given** o módulo `plataforma/estado.py`
**When** ele é importado
**Then** expõe os `TypedDict` `Reclamacao`, `Sinal`, `Analise`, `Falha`, `Motivo`, `Pontuacao`, `ItemRanking`, `DistribuicaoSentimento`, `Agregados` e `Estado`
**And** os campos são exatamente os da seção *Contrato de estado — forma exata* deste documento
**And** `estado.py` não importa nenhum outro módulo de `plataforma/`

**AC2 — `Sinal` é par indivisível (AD-1, AD-20)**

**Given** a estrutura `Sinal`
**When** ela é inspecionada
**Then** tem exatamente `codigo`, `citacao` e `valida`
**And** `valida` é `bool` com default `False`, nunca `bool | None`
**And** não existem os campos `sinal_a`, `sinal_b` nem `evidencia` em lugar nenhum do contrato

**AC3 — `Estado` acumula por redutor e tipa a fronteira (AD-8, AD-20)**

**Given** a estrutura `Estado`
**When** ela é inspecionada
**Then** `analises` e `falhas` são `Annotated[list[...], add]`
**And** `agregados` é do tipo `Agregados`, nunca `dict` cru

**AC4 — `Motivo` carrega proveniência (AD-3)**

**Given** a estrutura `Motivo`
**When** ela é inspecionada
**Then** `origem` é `Literal["sinal", "atributo"]` e `citacao` é `str | None`

**AC5 — `catalogo.py` é fonte única de códigos, pesos e termos genéricos (AD-18, AD-21)**

**Given** o módulo `plataforma/catalogo.py`
**When** ele é importado
**Then** declara os **seis** códigos do catálogo de `risk-signals.md` — sinal B: `dinheiro_retido`, `registro_contraditorio`, `dano_continuado`, `prazo_estourado`; sinal A: `ameaca_explicita`, `lei_citada` — cada um com definição escrita e exemplo
**And** `dinheiro_retido` é definido como *a empresa está com dinheiro do cliente*, cobrindo as seis categorias do gabarito: estorno não feito, conta bloqueada, produto pago e não entregue, produto defeituoso não trocado, assinatura ainda cobrada, débito sem contratação
**And** `ameaca_explicita` é um código do catálogo como qualquer outro, sujeito à mesma regra de evidência, e não um campo booleano à parte (AD-1)
**And** `ameaca_explicita` e `lei_citada` estão declarados como membros de um grupo saturado, para que `pontuacao.py` os leia sem repetir a regra
**And** declara a lista canônica de termos genéricos de produto
**And** nenhum outro módulo do pacote declara um código de sinal como literal

**AC6 — Tudo importável sem credencial e sem rede (AD-7, AD-12)**

**Given** a suíte de testes
**When** ela roda sem a variável de ambiente `GOOGLE_API_KEY` definida
**Then** importar `plataforma.estado` e `plataforma.catalogo` funciona
**And** nenhuma chamada de rede é feita

## Tasks / Subtasks

- [x] **Task 1 — Preparar dependência de teste** (AC: 6)
  - [x] Acrescentar `pytest>=9.1.1` ao `pyproject.toml` em `[dependency-groups] dev` (uv suporta PEP 735 nativamente; **não** usar `[project.optional-dependencies]`)
  - [x] Rodar `uv sync` e confirmar que `pytest` aparece no `uv.lock`
  - [x] **Não** acrescentar `langgraph` nem `jinja2` nesta story — nenhum é usado aqui, e a spine manda instalar na story que primeiro precisar

- [x] **Task 2 — Criar o pacote e o contrato de estado** (AC: 1, 2, 3, 4)
  - [x] Criar `plataforma/__init__.py` vazio
  - [x] Criar `plataforma/estado.py` com os dez `TypedDict` da seção *Contrato de estado — forma exata*
  - [x] Importar **apenas** `typing` e `operator.add` — nenhum import de `plataforma/`, nenhum de terceiro
  - [x] Docstring de módulo no padrão do repo: uma linha de propósito, depois o porquê não-óbvio (este contrato é a única parte do v1 que não é aditiva)

- [x] **Task 3 — Criar o catálogo** (AC: 5)
  - [x] Criar `plataforma/catalogo.py` com os seis códigos, definição escrita e exemplo por código
  - [x] Reaproveitar o texto de `classificador.py:50-77` para `dinheiro_retido` e `ameaca_explicita` — é prosa já validada contra o gabarito, não reescrever do zero
  - [x] Declarar o grupo saturado do sinal A como dado, não como regra em código
  - [x] Declarar a lista canônica de termos genéricos de produto
  - [x] `catalogo.py` não importa `estado.py` nem nenhum outro módulo de `plataforma/`

- [x] **Task 4 — Testes** (AC: 1, 2, 3, 4, 5, 6)
  - [x] Criar `tests/test_contrato.py` — forma de `Sinal`, `Motivo`, `Estado`, ausência dos campos proibidos, redutor `add` presente em `analises` e `falhas`
  - [x] Criar `tests/test_catalogo.py` — seis códigos exatos, grupo saturado, definição não vazia por código, lista de genéricos não vazia
  - [x] Um teste que importa os dois módulos com `GOOGLE_API_KEY` removida do ambiente (`monkeypatch.delenv(..., raising=False)`)
  - [x] Rodar `uv run pytest` e confirmar verde

### Review Findings

_Code review de 2026-08-07. Três camadas adversariais em paralelo (Blind Hunter, Edge Case Hunter, Acceptance Auditor), contexto frio. Nenhum AC violado no código de produção — o contrato bate campo a campo e os seis códigos batem com `risk-signals.md`. O peso dos achados está nos **testes**: várias guardas não detectam a regressão que existem para prevenir._

- [x] [Review][Decision→Patch] **`Agregados` não tem denominador para CM-2 nem para NFR-6.2** — PRD:189 define CM-2 como **taxa** de sinais derrubados; PRD:114 dispara NFR-6 quando *"todos os códigos de sinal propostos foram derrubados"*. Ambos exigem o total de códigos **propostos**, que não existia em campo nenhum. **Decidido por Neo: acrescentar `codigos_propostos: int` agora**, enquanto nada consome o contrato — ver *Divergências ratificadas* abaixo. `plataforma/estado.py:80`
- [x] [Review][Decision→Patch] **`TERMOS_GENERICOS` não declara regra de normalização** — comparação exata contra `produto` preenchido pelo modelo em texto livre; `"Produto"`, `"produtos"` e a forma NFD de `"serviço"` não casavam. **Decidido por Neo: normalização em `catalogo.py`**, junto do dado, como `nao_nomeia_produto()` — ver *Divergências ratificadas*. `plataforma/catalogo.py`

- [x] [Review][Patch] `__required_keys__` nunca era usado — `valida: NotRequired[bool]` e `total=False` passavam verdes [tests/test_contrato.py]
- [x] [Review][Patch] Detector de import evadido por `from . import catalogo`, import indentado e `importlib`; não cobria terceiros [tests/test_contrato.py]
- [x] [Review][Patch] Só `Sinal` e `Motivo` tinham asserção de conjunto exato de campos; `Agregados` e outras seis não tinham nenhuma [tests/test_contrato.py]
- [x] [Review][Patch] `ESTRUTURAS` era lista fixa e só verificava presença — `TypedDict` novo com `evidencia` escapava da varredura [tests/test_contrato.py]
- [x] [Review][Patch] Cláusulas de exclusão inventadas em `registro_contraditorio`, `prazo_estourado` e `lei_citada` — removidas; a definição agora reproduz a linha de `risk-signals.md` e só o exemplo é escrito aqui [plataforma/catalogo.py]
- [x] [Review][Patch] Teste das seis categorias buscava substring na definição inteira, incluindo as exclusões [tests/test_catalogo.py]
- [x] [Review][Patch] Comentário afirmava "preservado em conteúdo" com o `SOMENTE` ausente — operador restaurado e o comentário agora nomeia as duas cláusulas vindas de `risk-signals.md` [plataforma/catalogo.py]
- [x] [Review][Patch] AC5 "nenhum outro módulo declara código como literal" não tinha teste — varredura do pacote acrescentada [tests/test_catalogo.py]
- [x] [Review][Patch] Assert tautológico e sem mensagem [tests/test_import_sem_credencial.py]
- [x] [Review][Patch] `sys.modules.pop` sem restauração [tests/test_import_sem_credencial.py]
- [x] [Review][Patch] `project-context.md` com quatro afirmações tornadas falsas por este diff [_bmad-output/project-context.md]
- [x] [Review][Patch] `CATALOGO` sem proteção contra mutação — agora `MappingProxyType` em dois níveis [plataforma/catalogo.py]
- [x] [Review][Patch] `testpaths` ausente [pyproject.toml]

**Verificação dos patches (não é leitura, é execução):** as duas regressões que as guardas antigas deixavam passar foram injetadas em `estado.py` e a suíte agora falha em ambas — `from . import catalogo` quebra `test_modulos_folha_so_importam_o_que_a_story_permite` e `valida: NotRequired[bool]` quebra `test_campos_exatos_e_todos_obrigatorios[Sinal]`. Antes dos patches, as duas passavam verdes. Arquivo restaurado, suíte em **37 passed**.

- [x] [Review][Defer] Invariantes do contrato sem verificação executável: `Motivo.citacao` não-nula sse `origem == "sinal"`, `len(fila) == total_na_fila`, `nao_analisadas` como cópia de `falhas` [plataforma/estado.py:52,78,81-82] — deferido, é lógica das Stories 2.1/2.2
- [x] [Review][Defer] Redutor `add` sem deduplicação por `id`: lote reexecutado anexa a mesma `Analise` e quebra a asserção de conservação por excesso [plataforma/estado.py:93-94] — deferido, o fan-out nasce na Story 1.6
- [x] [Review][Defer] `Literal` de `status` e `sentimento` sem validação em runtime — o projeto proíbe `mypy`, então um sexto status entra no estado sem ruído [plataforma/estado.py:19-20,36] — deferido, a fronteira de leitura é a Story 1.3
- [x] [Review][Defer] `Reclamacao.data` é `str` obrigatório sem valor legal para data ausente ou fora de `DD/MM/AAAA` [plataforma/estado.py:15] — deferido, decisão da ingestão (Story 1.3)
- [x] [Review][Defer] `ocupacao_fila` e `taxa_produto_nao_nomeado` são `float` puro sem caso definido para divisão 0/0 [plataforma/estado.py:83-84] — deferido, o cálculo nasce na Story 2.2
- [x] [Review][Defer] `caminho_html: str` não representa "relatório não gerado", e `Estado` é `total=True` sem forma legal de estado inicial [plataforma/estado.py:91-97] — deferido, veio assim da seção *forma exata* do spec
- [x] [Review][Defer] AC6 "nenhuma chamada de rede" verificado só pela ausência de `google*` em `sys.modules`; não há guard de socket [tests/test_import_sem_credencial.py] — deferido, ganha valor real quando `analise.py` nascer (Story 1.5)
- [x] [Review][Defer] `state-contract.md` § *Regras* ainda afirma que "`evidencia` é campo de primeira classe", contradizendo AC2 [_bmad-output/specs/.../state-contract.md:82] — deferido, resíduo de documento fora deste diff

**Dismissed (13):** `GRUPO_SINAL_A` não ressuscita o campo proibido — o nome vem de `risk-signals.md` § *Sinal A* e o que AC2 proíbe é campo do contrato · `CODIGOS_ESPERADOS` duplica os literais de propósito, um teste que importa a lista do módulo sob teste é tautológico · igualdade exata de `TERMOS_GENERICOS` é a guarda contra invenção de termo, exatamente o risco que a story nomeia · o título do AC5 cita "pesos", mas as Dev Notes proíbem declará-los aqui e `risk-signals.md` § *Pesos do v1* ratifica `pontuacao.py` — o código está certo, o título é resíduo · `pytest>=9.1.1` sem teto foi prescrito literalmente pela Task 1 · demais itens são lógica de stories futuras ou teóricos.

## Dev Notes

### Contrato de estado — forma exata

Base: `state-contract.md`. **`Agregados`, `ItemRanking` e `DistribuicaoSentimento` não existem lá** — `state-contract.md` referencia `Agregados` sem nunca declará-lo. A forma abaixo foi derivada de AD-22 (toda contagem que o PRD reporta tem campo no estado), de FR-2, FR-8, FR-13, FR-14, NFR-6, CM-1, CM-2, CM-3, e da AC de ordenação da fila da Story 2.2. **Implementar exatamente assim** — as Stories 2.2 e 2.3 dependem destas chaves.

```python
from operator import add
from typing import Annotated, Literal, TypedDict


class Reclamacao(TypedDict):
    id: str                  # ID_Reclamacao do CSV — já único na origem
    data: str                # ISO-8601, convertido de DD/MM/AAAA
    empresa: str
    titulo: str
    texto: str               # coluna Descricao do CSV
    cidade_estado: str
    status: Literal["Respondida", "Não respondida",
                    "Resolvido", "Não resolvido", "Em réplica"]


class Sinal(TypedDict):
    codigo: str              # um dos seis de catalogo.py
    citacao: str             # literal, piso de 5 palavras
    valida: bool             # default False — não verificado é indistinguível
                             # de reprovado, e o terceiro estado só criaria
                             # caminho para esquecer de rodar a verificação


class Analise(TypedDict):
    id: str                  # liga de volta — obrigatório
    sentimento: Literal["positivo", "neutro", "negativo"]
    produto: str | None      # como o modelo leu, sem julgamento de genérico
    sinais: list[Sinal]      # par indivisível código↔citação
    prazo_prometido_dias: int | None
    data_evento: str | None  # ISO-8601 ou None


class Falha(TypedDict):
    ids: list[str]           # reclamações que ficaram sem análise
    causa: str
    no: str                  # nome do nó que falhou


class Motivo(TypedDict):
    origem: Literal["sinal", "atributo"]
    rotulo: str
    citacao: str | None      # não-nula sse origem == "sinal"


class Pontuacao(TypedDict):
    id: str
    pontos: int
    na_fila: bool
    motivos: list[Motivo]    # o que o relatório exibe


class ItemRanking(TypedDict):
    rotulo: str              # produto como o modelo leu, ou "não identificado"
    total: int
    generico: bool           # termo da lista canônica de catalogo.py


class DistribuicaoSentimento(TypedDict):
    positivo: int
    neutro: int
    negativo: int


class Agregados(TypedDict):
    data_execucao: str                    # ISO-8601; o template formata em pt-BR
    lidas: int                            # FR-2, FR-14
    analisadas: int                       # FR-2, FR-14
    nao_analisadas: int                   # sum(len(f["ids"]) for f in falhas)
    eventos_falha: int                    # len(falhas) — AD-5 pede os dois
    codigos_propostos: int                # denominador de CM-2 e de NFR-6.2
    codigos_derrubados: int               # CM-2, FR-2
    fila: list[str]                       # ids na ordem de exibição da fila
    total_na_fila: int
    ocupacao_fila: float                  # CM-1
    taxa_produto_nao_nomeado: float       # CM-3 — nulo MAIS genérico
    ranking_produtos: list[ItemRanking]   # FR-8, FR-13
    distribuicao_sentimento: DistribuicaoSentimento
    degradado: bool                       # NFR-6, já resolvido como booleano
    motivo_degradacao: str | None         # qual das duas condições disparou


class Estado(TypedDict):
    reclamacoes: list[Reclamacao]
    analises: Annotated[list[Analise], add]   # acumula entre execuções de lote
    falhas: Annotated[list[Falha], add]       # acumula entre execuções de lote
    pontuacoes: list[Pontuacao]
    agregados: Agregados
    caminho_html: str
```

**Esta story só declara a forma.** Quem preenche `Agregados` é o nó `agregar`, na Story 2.2. Não escrever lógica de cálculo aqui.

### Divergências ratificadas no code review de 2026-08-07

Duas mudanças em relação ao que estas Dev Notes prescreviam originalmente, decididas por Neo durante a triagem do code review. Registradas aqui porque as Stories 2.1 e 2.2 leem esta seção como fonte.

**1. `Agregados` ganhou `codigos_propostos: int`** — já incorporado ao bloco acima. A forma original tinha só `codigos_derrubados`, mas CM-2 é definida no PRD (linha 189) como **taxa** de sinais derrubados e a segunda condição de NFR-6 (PRD linha 114) dispara quando *"todos os códigos de sinal propostos foram derrubados"*. As duas precisam do total proposto, que não existia em campo nenhum. Corrigido agora, enquanto nada consome o contrato — o alvo declarado era não obrigar a Story 2.2 a alterar a única parte não-aditiva do v1.

**2. `catalogo.py` ganhou a função `nao_nomeia_produto(produto)`** — variância deliberada em relação a *"estrutura simples de dados; nenhuma classe, nenhuma lógica"*. É função pura, sem estado, de um `return`. Existe porque `TERMOS_GENERICOS` é comparado contra `produto` preenchido pelo modelo em texto livre: sem regra de normalização única, `"Produto"`, `"produtos"` e a forma NFD de `"serviço"` escapam da lista, e cada consumidor inventa a sua — movendo CM-3, que o PRD reporta como 38%. A regra vive junto da lista canônica pelo mesmo motivo que a lista vive junto do catálogo. Cobre também vazio e só-espaços, que não são nulos nem genéricos e escapariam das duas metades de CM-3. **A Story 2.2 chama esta função; não reimplementar a comparação em `agregacao.py`.**

### Catálogo — forma sugerida

Estrutura simples de dados; nenhuma classe, nenhuma lógica.

```python
GRUPO_SINAL_A = ("ameaca_explicita", "lei_citada")  # saturam: juntos valem 3, nunca 6

CATALOGO = {
    "dinheiro_retido": {
        "definicao": "...",   # as seis categorias — texto de classificador.py:50-64
        "exemplo": "...",
    },
    # ... os outros cinco
}

TERMOS_GENERICOS = frozenset({"fatura", "compra", "produto", "serviço", ...})
```

Regras que a forma precisa honrar:

- **Definição escrita com exemplo dentro do prompt é o fator de maior impacto na acurácia** (`risk-signals.md`). A definição não é comentário — é dado que `analise.py` injeta no prompt.
- Os **pesos** vivem em `pontuacao.py` (Story 2.1), com o código do catálogo como chave. **Não** declarar peso aqui — mas a chave precisa ser a mesma string.
- `TERMOS_GENERICOS` é consumido por `agregacao.py` (Story 2.2) e medido por CM-3. A lista é sobre **nomes de produto**, não sobre códigos de sinal.

**A lista de termos genéricos não tem versão fechada em nenhuma fonte.** O PRD (CM-3) nomeia quatro e diz *"e afins"*; a medição de 2026-08-06 encontrou 18 de 50 identificações caindo em substantivos que não nomeiam produto algum. Fixar a lista inicial com **exatamente os quatro medidos** — `fatura`, `compra`, `produto`, `serviço` —, guardar em `frozenset`, e deixar comentário `# ponytail:` registrando que a lista cresce por medição, não por palpite. **Não inventar termos** — cada termo acrescentado sem evidência infla CM-3 e muda um número que o PRD reporta.

### Fonte pronta para reaproveitar — não reescrever

`classificador.py:42-77` já carrega prosa validada contra o gabarito humano:

- **linhas 50-64** → definição de `dinheiro_retido`. Enumera exatamente as seis categorias, com a lista do que **não** vale (serviço ruim, lentidão, mau atendimento, propaganda enganosa sem cobrança) e o teste operacional: *"existe uma quantia do cliente parada na empresa agora, ou saindo do bolso dele agora?"*
- **linhas 69-73** → definição de `ameaca_explicita`, incluindo a exclusão de retórica: *"é um absurdo", "isso é fraude", "exijo" são retórica, não anúncio de ação*.

Esse texto produziu precisão de 100% na regra medida. Adaptar de prosa de prompt para valor de dicionário, **preservando o conteúdo**.

Os outros quatro códigos (`registro_contraditorio`, `dano_continuado`, `prazo_estourado`, `lei_citada`) têm descrição de uma linha em `risk-signals.md` § *Catálogo de códigos* e precisam de exemplo escrito do zero.

### Armadilhas específicas desta story

- **`from typing import TypedDict` está correto aqui.** `state-contract.md` manda assim e a doc do LangGraph usa assim. Existe um caso conhecido em que Python < 3.12 exige `typing_extensions.TypedDict` — quando um `TypedDict` alimenta um modelo Pydantic. Isso pode aparecer na **Story 1.5**, ao derivar o `response_schema` de `Analise` e `Sinal`. Se aparecer, o sintoma é erro de resolução de tipo do Pydantic, e a correção é trocar o import em `estado.py`. **Não antecipar** — `typing-extensions` já está no `uv.lock` como transitivo se for preciso.
- **`plataforma/__init__.py` vazio é obrigatório.** Sem ele, o import por namespace package torna a descoberta do pytest dependente do diretório de execução.
- **`pytest` não está declarado, mas `.pytest_cache/` existe** na raiz — alguém já rodou por fora. Não tomar como prova de que a dependência está resolvida.
- **`pyproject.toml` não tem `[build-system]`.** `baseline.py` roda hoje por `uv run python baseline.py`, com import resolvido pelo diretório de trabalho. Se `uv run pytest` não achar `plataforma`, a correção mínima é `[tool.pytest.ini_options] pythonpath = ["."]` — **não** introduzir build backend nem instalar o pacote.
- **`valida: bool` com default `False` é semântica, não conveniência** (AD-20). `TypedDict` não tem default de verdade; a garantia é que **todo caminho que constrói um `Sinal` preenche `valida`**, e nenhum o deixa ausente ou `None`. Documentar isso no código.

### Convenções obrigatórias

Do `project-context.md` (carregado automaticamente), o que incide nesta story:

- Português em módulos, funções, variáveis, docstrings e mensagens.
- Sem classes em código de domínio — `TypedDict` e funções puras.
- Docstring de módulo: propósito em uma linha, depois o porquê não-óbvio.
- Comentário explica *por que*, nunca *o que*.
- `# ponytail:` prefixa simplificação deliberada com teto nomeado.
- Executar sempre por `uv run python`, nunca `python` direto.
- Não introduzir `ruff`, `black`, `mypy` ou hooks.
- Não acrescentar dependência fora da lista fechada da spine.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-1** | `Sinal` é `{codigo, citacao, valida}`; nenhum campo paralelo |
| **AD-3** | `Motivo.origem` é `Literal["sinal","atributo"]`, `citacao` é `str \| None` |
| **AD-7** | Nem `estado.py` nem `catalogo.py` importam `google.genai`, direta ou transitivamente |
| **AD-8** | `analises` e `falhas` são `Annotated[list, add]` |
| **AD-12** | Ambos os módulos são importáveis e testáveis sem rede e sem credencial |
| **AD-18** | Códigos e definições vivem só em `catalogo.py` |
| **AD-20** | `Agregados` é `TypedDict`; `Sinal.valida` é `bool`, nunca `bool \| None` |
| **AD-21** | `TERMOS_GENERICOS` vive em `catalogo.py`; `agregar` a aplica depois |

Direção de dependência (spine): `estado` não importa ninguém. `catalogo` também não — ele é folha, consumido por `analise`, `pontuacao` e `agregacao`.

### Bibliotecas e versões

| Item | Versão | Nesta story |
|---|---|---|
| Python | `>=3.11` | `TypedDict`, `Literal`, `Annotated`, `str \| None` — tudo stdlib em 3.11 |
| `pytest` | `>=9.1.1` | **a instalar** — `[dependency-groups] dev` |
| `langgraph` | `1.2.10` | **não** nesta story; `Annotated[list, add]` é `typing` + `operator`, não LangGraph |
| `jinja2` | `3.1.6` | não |
| `google-genai` | `>=2.17.0` | não — e AD-7 proíbe importá-lo daqui |

Nenhuma dependência externa nova além do `pytest`. O contrato de estado é stdlib puro por desenho — é o que faz AD-12 ser verificável.

### Estrutura de arquivos

```text
plataforma/
  __init__.py      # NOVO — vazio
  estado.py        # NOVO — os dez TypedDict
  catalogo.py      # NOVO — seis códigos, grupo saturado, termos genéricos
tests/
  test_contrato.py # NOVO
  test_catalogo.py # NOVO
pyproject.toml     # UPDATE — acrescentar pytest em [dependency-groups] dev
```

**Não criar nesta story:** `ingestao.py`, `analise.py`, `evidencia.py`, `pontuacao.py`, `agregacao.py`, `relatorio.py`, `grafo.py`, `config.py`, `main.py`, `templates/`. Cada um nasce na story que primeiro precisa dele.

**Não tocar:** `baseline.py`, `classificador.py`, `docs/`. São medição preexistente; a Story 3.1 depende de eles continuarem intactos.

### Requisitos de teste

- **Sem rede, sem credencial.** É a verificação executável de AD-7 e AD-12.
- **Sem mocks do SDK** — nada aqui depende dele.
- Verificar a forma por introspecção: `__annotations__`, `__required_keys__`, `get_type_hints(..., include_extras=True)` para confirmar o `Annotated[..., add]`.
- Testar a **ausência** dos campos proibidos (`sinal_a`, `sinal_b`, `evidencia`), não só a presença dos corretos. É o que impede a regressão que AD-1 existe para prevenir.
- `assert` com mensagem que nomeia o valor observado, no padrão de `baseline.py:90`.
- Sem meta de cobertura — nenhuma é declarada no projeto.

### Project Structure Notes

Alinhado ao seed estrutural da spine. Uma variância deliberada: a spine lista `plataforma/estado.py` sem mencionar `__init__.py`; ele é acrescentado por previsibilidade de import e não altera a direção de dependência.

`ItemRanking` e `DistribuicaoSentimento` são estruturas novas, não previstas no seed — existem porque `Agregados` precisa de forma tipada em toda fronteira (AD-20) e listas de dicts crus dentro de um `TypedDict` reintroduzem exatamente a divergência que AD-20 previne.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1] — ACs originais
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md#Estruturas] — forma canônica; `Agregados` ausente lá
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/risk-signals.md#Catálogo de códigos] — seis códigos, grupo saturado
- [Source: .../ARCHITECTURE-SPINE.md#AD-1, AD-3, AD-7, AD-8, AD-12, AD-18, AD-20, AD-21]
- [Source: .../ARCHITECTURE-SPINE.md#Structural Seed] — layout do pacote
- [Source: _bmad-output/planning-artifacts/prds/.../prd.md#FR-2, FR-8, FR-13, FR-14, NFR-6, CM-1, CM-2, CM-3] — origem dos campos de `Agregados`
- [Source: _bmad-output/project-context.md] — convenções e armadilhas do repositório
- [Source: classificador.py:42-77] — prosa validada de `dinheiro_retido` e `ameaca_explicita`

## Dev Agent Record

### Agent Model Used

claude-opus-5

### Debug Log References

- `uv run pytest` na fase RED: `ModuleNotFoundError: No module named 'plataforma'` nos dois módulos de teste — falha esperada, confirma que os testes exercitam código real.
- Causa raiz confirmada da armadilha prevista nas Dev Notes: `pyproject.toml` não tem `[build-system]`, o pacote não é instalado e o import não resolve. Corrigido com `[tool.pytest.ini_options] pythonpath = ["."]`, a correção mínima que a story prescreve — nenhum build backend introduzido.
- `uv run pytest` final: **15 passed**.
- Regressão em `baseline.py`: `autoteste ok` e as métricas inalteradas (categoria + Status: precisão 100%, recall 68%, F1 0.81).

### Completion Notes List

- **Contrato implementado exatamente como a seção *Contrato de estado — forma exata***. As dez estruturas existem, `estado.py` importa só `operator.add` e `typing`, e nada de `plataforma/`.
- **AD-1/AD-20 verificados por ausência, não só por presença.** `test_campos_proibidos_ausentes_do_contrato_inteiro` varre as dez estruturas atrás de `sinal_a`, `sinal_b` e `evidencia` — é o teste que impede a regressão que AD-1 existe para prevenir. `Sinal.valida` é asserido como `bool` puro.
- **AD-8 verificado pela metadata do `Annotated`,** não pelo texto do tipo: `get_type_hints(Estado, include_extras=True)` + `get_args` compara com `(list[Analise], add)` — a função redutora em si, não seu nome.
- **`dinheiro_retido` e `ameaca_explicita` preservam a prosa de `classificador.py:50-77`,** que produziu precisão de 100% na regra medida, inclusive a lista do que **não** vale, o teste operacional (*"existe uma quantia do cliente parada na empresa agora?"*) e a exclusão de retórica. Um teste verifica que as seis categorias do gabarito continuam nomeadas na definição.
- **Os outros quatro códigos ganharam exemplo escrito do zero,** partindo da descrição de uma linha de `risk-signals.md`. Cada um explicita o que **não** vale, para não virar código guarda-chuva.
- **`TERMOS_GENERICOS` fixado nos quatro termos medidos**, com `# ponytail:` registrando que a lista cresce por medição, não por palpite — acrescentar termo sem evidência muda CM-3, um número que o PRD reporta.
- **AD-7 testado, não só declarado:** `test_nenhum_dos_dois_arrasta_o_sdk` limpa `sys.modules`, importa os dois módulos e falha se qualquer `google*` aparecer. AD-12 coberto por `monkeypatch.delenv` de `GOOGLE_API_KEY` e `GEMINI_API_KEY`.
- **`typing.TypedDict` mantido** conforme as Dev Notes. A troca por `typing_extensions` não foi antecipada — se aparecer, é na Story 1.5.
- **Nada de lógica.** Esta story só declara a forma; quem preenche `Agregados` é o nó `agregar` na Story 2.2. Nenhum arquivo fora da lista foi criado; `baseline.py`, `classificador.py` e `docs/` intocados.
- **Divergência `GEMINI_API_KEY`/`GOOGLE_API_KEY` não resolvida aqui** — é dívida de `config.py`, que nasce na Story 1.2. O teste de AC6 remove as duas variáveis para não depender de qual delas o ambiente tem.

### File List

- `pyproject.toml` — MODIFICADO (`[dependency-groups] dev` com `pytest`, `[tool.pytest.ini_options] pythonpath`)
- `uv.lock` — MODIFICADO (`pytest==9.1.1` e transitivos)
- `plataforma/__init__.py` — NOVO (vazio)
- `plataforma/estado.py` — NOVO
- `plataforma/catalogo.py` — NOVO
- `tests/test_contrato.py` — NOVO
- `tests/test_catalogo.py` — NOVO
- `tests/test_import_sem_credencial.py` — NOVO
- `_bmad-output/project-context.md` — MODIFICADO (code review: quatro afirmações tornadas falsas por esta story)
- `_bmad-output/implementation-artifacts/deferred-work.md` — NOVO (code review: 8 itens deferidos)

## Change Log

| Data | Mudança |
|---|---|
| 2026-08-07 | Implementação da Story 1.1: contrato de estado (`plataforma/estado.py`), catálogo de sinais (`plataforma/catalogo.py`) e três módulos de teste. `pytest` declarado em `[dependency-groups] dev`. Status → review. |
| 2026-08-07 | Code review adversarial (3 camadas paralelas): 15 achados corrigidos, 8 deferidos, 13 descartados. Duas decisões de Neo alteraram o contrato — `Agregados.codigos_propostos` e `catalogo.nao_nomeia_produto()`, ambas registradas em *Divergências ratificadas*. As guardas de teste foram refeitas: `__required_keys__` no lugar de `get_type_hints`, detecção de import por AST, descoberta dinâmica das estruturas e varredura do pacote atrás de literais de código. Suíte: 15 → 37 testes. |
