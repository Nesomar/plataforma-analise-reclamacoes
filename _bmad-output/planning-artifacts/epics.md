---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md
  - _bmad-output/specs/spec-plataforma-analise-reclamacoes/SPEC.md
  - _bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md
  - _bmad-output/specs/spec-plataforma-analise-reclamacoes/risk-signals.md
  - _bmad-output/specs/spec-plataforma-analise-reclamacoes/architecture-diagrams.md
  - _bmad-output/specs/spec-plataforma-analise-reclamacoes/roadmap.md
  - docs/gabarito-marcacao.md
  - docs/gabarito.csv
---

# plataforma-analise-reclamacoes - Epic Breakdown

## Overview

Este documento traz a quebra completa em épicos e stories da plataforma-analise-reclamacoes, decompondo os requisitos do PRD e as decisões da spine de arquitetura em stories implementáveis.

Não há documento de UX: o produto entrega um arquivo HTML estático e a spine (AD-10, AD-11, AD-14) já fixa template, autocontenção e tratamento visual. A seção de UX Design Requirements está declarada como não aplicável.

## Requirements Inventory

### Functional Requirements

**Execução e feedback ao operador**

- **FR-1** — O sistema aceita o caminho do CSV como argumento de linha de comando e escreve o HTML ao lado do CSV de entrada, com nome iniciando em `relatorio-`, seguido do nome do arquivo de entrada e da data da execução. O caminho final é impresso ao encerrar.
  **Partido entre épicos** — **FR-1a** (aceitar o caminho como argumento) fica na Story 1.7, porque sem ele o Épico 1 não é executável de ponta a ponta; **FR-1b** (escrever, nomear e imprimir o caminho) fica na Story 2.6, onde existe relatório para escrever.
- **FR-2** — Ao encerrar, o sistema reporta ao operador: total de reclamações lidas, total analisadas com sucesso, total não analisadas e total de sinais derrubados pela verificação de evidência.
- **FR-3** — CSV com coluna ausente, schema divergente ou identificador duplicado é rejeitado antes de qualquer chamada de LLM, com mensagem que nomeia a causa. Realiza CAP-1.
- **FR-4** — Se o arquivo de saída já existir, o sistema encerra sem escrever, nomeando o arquivo existente. Sobrescrever exige sinalizador explícito na linha de comando.

**Análise**

- **FR-5** — Cada reclamação recebe sentimento, produto e sinais de risco. Realiza CAP-2, CAP-3 e CAP-4.
- **FR-6** — Todo sinal de risco marcado carrega ao menos uma citação literal do texto, com no mínimo cinco palavras. Sinal sem citação, ou com citação abaixo do piso, não é registrado. Realiza CAP-4.
- **FR-7** — Antes de compor o resultado, o sistema confirma que cada citação existe no texto original e derruba o sinal específico que aquela citação sustentava, não o conjunto de sinais da reclamação. A derrubada é contabilizada e reportada. Realiza CAP-5.
- **FR-8** — Reclamação cujo produto não é identificável recebe o rótulo `não identificado` e permanece na base analisada, aparecendo como linha visível do ranking com seu total.
- **FR-9** — Item que entra na fila apenas por parcela determinística é exibido com o motivo estrutural que o colocou ali (categoria, `Status`), não com citação vazia.

**Relatório**

- **FR-10** — O relatório é arquivo único que abre em navegador sem servidor, sem instalação e sem qualquer requisição de rede. Realiza CAP-8.
- **FR-11** — A fila de prioridade é o primeiro conteúdo do relatório, antes de qualquer agregado.
- **FR-12** — Cada item da fila exibe o que sustentou sua classificação — citação literal ou motivo estrutural de FR-9 — como conteúdo visível, não como detalhe expansível.
- **FR-13** — O ranking de produtos declara no próprio relatório que volume não equivale a gravidade, inclui `não identificado` como linha visível e marca produto identificado mas genérico como tal, usando a lista canônica de termos genéricos que vive junto do catálogo de sinais.
- **FR-14** — O relatório informa data da execução, total de reclamações analisadas e total não analisado por falha.
- **FR-15** — O relatório apresenta graficamente a distribuição de sentimento e o ranking de produtos, com o gráfico embutido no arquivo (SVG inline ou equivalente), nunca por biblioteca carregada da rede.
- **FR-16** — O relatório declara, em texto visível ao leitor, que a classificação de risco é heurística de engenharia e não parecer jurídico.
- **FR-17** — O relatório é legível em português do Brasil, incluindo rótulos, categorias e números formatados na convenção local.
- **FR-18** — A distribuição de sentimento e o ranking de produtos carregam, ao lado do próprio gráfico e não em nota de rodapé, ressalva fixa que nomeia o que limita cada leitura nesta base.

### NonFunctional Requirements

**Desempenho**

- **NFR-1** — Execução sobre 50 reclamações completa em até 2 minutos, ponta a ponta. `[ASSUMPTION]` — pendente de aferição (Q-8).
- **NFR-2** — O tamanho de lote é configurável sem alteração de código.

**Custo**

- **NFR-3** — Execução completa sobre a base alvo cabe nos limites do tier de teste gratuito da API do Gemini.
- **NFR-4** — O sistema não analisa a mesma reclamação duas vezes por desenho do fluxo. Repetição por falha de transporte é permitida e não conta como reanálise.

**Confiabilidade**

- **NFR-5** — Falha em uma reclamação não interrompe a execução das demais; a afetada é registrada como não analisada e contabilizada.
- **NFR-6** — O sistema marca o relatório como degradado, no próprio arquivo e de forma visível ao leitor, quando (1) acima de 10% de reclamações não analisadas, ou (2) todos os códigos de sinal propostos foram derrubados na verificação de evidência.
- **NFR-7** — Resposta do modelo é casada por identificador, nunca por posição. Identificador faltante é detectado; identificador repetido ou inventado é descartado, não somado.
- **NFR-8** — Duas execuções sobre o mesmo arquivo produzem os mesmos identificadores de reclamação.

**Portabilidade**

- **NFR-9** — O relatório abre corretamente em navegador atual sem plugin e sobrevive ao encaminhamento por e-mail como anexo único.
- **NFR-10** — A chave de API é lida de variável de ambiente. Nenhuma credencial no código ou no repositório.

### Additional Requirements

**Sem starter template.** A arquitetura não especifica scaffold externo. O repositório já existe com `pyproject.toml`, `baseline.py`, `classificador.py`, `.gitignore`, `.env.example` e `README.md`. O trabalho é criar o pacote `plataforma/` do zero dentro do repositório existente — a Story 1.1 é criação de estrutura e contrato de estado, não bootstrap de projeto.

**Invariantes de arquitetura (AD-1 a AD-22)** — cada um é restrição verificável que as ACs precisam honrar:

- **AD-1** — `Sinal = {codigo, citacao, valida}` é par indivisível. Não existem `sinal_b: list[str]`, `evidencia: list[str]` nem `sinal_a: bool`. Piso de cinco palavras verificado no mesmo lugar que a verificação de substring.
- **AD-2** — Citação inválida derruba o código inteiro, inclusive os pares do mesmo código que passaram. A contagem reportada é de **códigos derrubados**.
- **AD-3** — `Motivo.origem ∈ {sinal, atributo}`. `sinal` exige citação não nula e vem do modelo; `atributo` tem citação nula e vem de coluna do CSV. Nenhuma etapa converte uma origem na outra.
- **AD-4** — `Pontuacao = {id, pontos, na_fila, motivos}`. `renderizar` lê `reclamacoes` para exibir e `falhas` para FR-14/NFR-6, mas nenhuma condicional do template consulta `Reclamacao` para derivar por que um item está na fila.
- **AD-5** — `Falha = {ids, causa, no}`, acumulada com redutor `add`. Um lote esgotado produz **uma** `Falha` com os ids do lote. FR-2 reporta eventos e reclamações afetadas; o denominador de NFR-6 é o segundo.
- **AD-6** — Conservação: `len(reclamacoes) == len(analises) + sum(len(f["ids"]) for f in falhas)`, verificado em asserção após o gather e antes de `pontuar`.
- **AD-7** — Apenas `analise.py` importa `google.genai`, direta ou transitivamente. O cliente é construído dentro de `analisar_lote`, nunca em escopo de módulo.
- **AD-8** — `carregar` emite um `Send` por lote para `analisar_lote`. `analises` e `falhas` acumulam por redutor `add`; nenhum lote lê o resultado de outro.
- **AD-9** — `retry_policy=` no `add_node` de `analisar_lote` cobre falha de transporte; o nó não tem laço de repetição. `error_handler=` no mesmo `add_node` é obrigatório e é quem produz a `Falha` de AD-5.
- **AD-10** — Um único `Environment` do Jinja2, em `relatorio.py`, com `autoescape=True` literal (não `select_autoescape`). Nenhum segundo `Environment`. Texto de produto vive no template, não em Python.
- **AD-11** — Todo byte que o navegador renderiza já estava no arquivo quando ele foi escrito. Gráficos são `<svg>` no template; nenhum `<script src>`, nenhum `<link href>` externo.
- **AD-12** — Verificar, pontuar, agregar e renderizar são funções puras alimentadas por `Analise` fabricada à mão. Nenhum teste faz chamada de rede. As três parcelas não exercidas pela base e a verificação de citação falsa têm caso construído à mão.
- **AD-13** — `len(analises) == 0` encerra com causa nomeada e não escreve arquivo. CSV vazio encerra em `carregar`, antes do fan-out. Se o modelo propôs ao menos um código e todos foram derrubados, o relatório é marcado degradado.
- **AD-14** — Distribuição de sentimento e ranking de produtos carregam ressalva no template, ao lado do gráfico, não em nota de rodapé.
- **AD-15** — O nome do arquivo de saída começa sempre com `relatorio-`; nome do CSV e data vêm depois do prefixo.
- **AD-16** — O payload enviado ao modelo carrega **`id` e `texto`, nada mais**. `empresa` e `titulo` ficam fora por construção, não por instrução no prompt.
- **AD-17** — `tamanho_lote` tem piso 2 e teto 25, validados na carga da configuração. A validação recai sobre os lotes emitidos: lote residual de tamanho 1 é fundido ao anterior. Fora da faixa, encerra antes de qualquer chamada paga. Quem fatia é `carregar`.
- **AD-18** — Códigos do catálogo e definições vivem em um único módulo, importado pelo construtor do prompt e pela pontuação. Nenhum código de sinal como literal solto em `analise.py`, `pontuacao.py` ou no template.
- **AD-19** — Cada chave de `Estado` tem exatamente um nó que a escreve. `pontuacoes` é de `pontuar` (inclusive `na_fila` e o corte); `agregados` é de `agregar`, que ordena e conta e nunca decide pertencimento.
- **AD-20** — `Agregados` é `TypedDict`, não `dict`. `Sinal.valida` é `bool` com default `False`, nunca `bool | None`.
- **AD-21** — O modelo devolve o produto como leu, sem julgamento. A lista de termos genéricos vive em `catalogo.py` e `agregar` a aplica. `produto = None` significa apenas *o texto não permitiu identificar*.
- **AD-22** — `Agregados` carrega os números que FR-2, FR-14, NFR-6, CM-2 e CM-3 reportam, calculados em `agregar`. O template exibe; não soma, não divide, não compara com limiar.

**Convenções de consistência:**

- Módulos e funções em português. Nós do grafo nomeados pelo verbo: `carregar`, `analisar_lote`, `pontuar`, `agregar`, `renderizar`.
- Identificador `ID_Reclamacao` da origem, validado único na ingestão. Casamento sempre por `id`.
- Datas ISO-8601 no estado; `DD/MM/AAAA` só na fronteira de leitura do CSV.
- Leitura do CSV com `utf-8-sig` e separador `;`.
- Falha de conteúdo vira `Falha` e a execução segue; falha de infraestrutura encerra sem escrever relatório.
- Configuração por variável de ambiente com default no código, via `python-dotenv`.
- Saída do modelo por `response_schema` do `google-genai`, nunca parsing de texto livre. Resposta fora do schema é falha de conteúdo, não exceção.
- Pesos e corte vêm de `risk-signals.md` e são declarados em um lugar só em `pontuacao.py`, com o código do catálogo como chave.
- Observabilidade é a saída do operador (FR-2). Não há log estruturado, métrica exportada nem trace.

**Stack fixada:** Python ≥3.11 · langgraph 1.2.10 · google-genai ≥2.17.0 · modelo `gemini-3.6-flash` · jinja2 3.1.6 · python-dotenv ≥1.2.2 · pytest 9.1.1.

**Estrutura de arquivos (structural seed):** `plataforma/{estado,catalogo,ingestao,analise,evidencia,pontuacao,agregacao,relatorio,grafo,config}.py`, `plataforma/templates/relatorio.html.j2`, `main.py`, `tests/`.

**Catálogo de sinais (CAP-4) — seis códigos, ratificado em 2026-08-07.** Fonte única: `risk-signals.md`.

- Sinal A, intenção jurídica declarada, **grupo saturado**: `ameaca_explicita`, `lei_citada`
- Sinal B, exposição factual: `dinheiro_retido`, `registro_contraditorio`, `dano_continuado`, `prazo_estourado`

Cada um exige definição escrita com exemplo dentro do prompt — é o fator de maior impacto na acurácia.

**Pesos do score (v1) — ratificados em 2026-08-07 contra `risk-signals.md`:** `dinheiro_retido` = 3 · `ameaca_explicita` = 3 · `lei_citada` = 3 · `registro_contraditorio` = 2 · `dano_continuado` = 2 · `prazo_estourado` = 1 · `Status` = Respondida = −1 (modificador, atributo do CSV). `ameaca_explicita` e `lei_citada` saturam: juntos valem 3, nunca 6. Corte binário a partir de 3 pontos.

**Governança de dados:**

- **DG-1** — Apenas dados sintéticos versionados no repositório.
- **DG-2** — Base real nunca entra no repositório, nem o relatório gerado a partir dela.
- **DG-3** — Relatório sobre base real herda dados pessoais das citações e é documento restrito.
- **DG-4** — A chave de API não é versionada; o arquivo de ambiente está coberto pelo `.gitignore`.
- **DG-5** — O README declara explicitamente que o corpus é sintético.

**Métricas e contramétricas que exigem instrumentação no código:**

- **M-1** — Fila atinge precisão ≥ 95% com recall ≥ 65% contra `docs/gabarito.csv`.
- **M-2** — 100% das citações no relatório final são trecho literal com no mínimo cinco palavras.
- **M-6** — Adicionar etapa nova ao grafo não exige alterar a assinatura de nenhuma etapa existente.
- **CM-1** — Taxa de ocupação da fila; acima de 40% a fila deixou de ordenar.
- **CM-2** — Taxa de sinais derrubados na verificação. Zero constante é indistinguível de mecanismo morto sem teste sintético.
- **CM-3** — Taxa de produto não nomeado = produto nulo **mais** produto genérico.
- **CM-4** — Reclamações não analisadas por falha.

### UX Design Requirements

**Não aplicável.** Não existe documento de UX para este projeto. O único artefato visual é o relatório HTML, e suas exigências visuais já estão cobertas como requisitos funcionais (FR-10 a FR-18) e invariantes de arquitetura (AD-10, AD-11, AD-14). Nenhum UX-DR foi extraído.

### FR Coverage Map

| FR | Épico | O quê |
|---|---|---|
| FR-1a | 1 | Caminho do CSV aceito como argumento de linha de comando |
| FR-1b | 2 | Nome `relatorio-*` ao lado do CSV e caminho impresso ao encerrar |
| FR-2 | 1 | Quatro contagens no terminal do operador |
| FR-3 | 1 | Rejeição de schema divergente ou id duplicado antes de chamada paga |
| FR-4 | 2 | Arquivo de saída existente encerra; flag explícita para sobrescrever |
| FR-5 | 1 | Sentimento, produto e sinais por reclamação |
| FR-6 | 1 | Piso de cinco palavras na citação |
| FR-7 | 1 | Derrubada por código de sinal, contabilizada |
| FR-8 | 2 | `não identificado` como linha visível do ranking |
| FR-9 | 2 | Motivo estrutural exibido sem citação |
| FR-10 | 2 | Arquivo único que abre sem servidor e sem rede |
| FR-11 | 2 | Fila de prioridade como primeiro conteúdo |
| FR-12 | 2 | Evidência visível, não em detalhe expansível |
| FR-13 | 2 | Ressalva de volume ≠ gravidade; genérico marcado no ranking |
| FR-14 | 2 | Data da execução, total analisado, total não analisado |
| FR-15 | 2 | Gráficos como SVG inline |
| FR-16 | 2 | Ressalva de heurística de engenharia, não parecer jurídico |
| FR-17 | 2 | pt-BR em rótulos, categorias e formatação numérica |
| FR-18 | 2 | Ressalva fixa ao lado de cada gráfico |

**Cobertura:** 18/18 FRs. FR-1 é o único partido entre épicos, e a partição está no próprio texto do requisito: a metade que aceita o argumento (FR-1a) é o que torna o Épico 1 executável de ponta a ponta; a metade que escreve e nomeia o arquivo (FR-1b) só faz sentido quando existe relatório para escrever.

NFRs: NFR-2, NFR-4, NFR-5, NFR-7, NFR-8 e NFR-10 no Épico 1; NFR-6 e NFR-9 no Épico 2; NFR-1 e NFR-3 aferidos no Épico 3 (Story 3.2).

## Epic List

### Épico 1: O operador roda a base e sabe se pode confiar no resultado

O operador executa o comando sobre um CSV e o terminal responde com quatro números honestos — lidas, analisadas, não analisadas, sinais derrubados. Todo sinal que sobreviveu carrega citação literal verificada contra o texto original. Falha em um lote não derruba a execução dos demais.

**FRs covered:** FR-1a, FR-2, FR-3, FR-5, FR-6, FR-7
**NFRs:** NFR-2, NFR-4, NFR-5, NFR-7, NFR-8, NFR-10
**ADs:** AD-1, AD-2, AD-3, AD-5, AD-6, AD-7, AD-8, AD-9, AD-16, AD-17, AD-18, AD-19, AD-20, AD-21
**Arquivos:** `estado.py`, `catalogo.py`, `config.py`, `ingestao.py`, `analise.py`, `evidencia.py`, `grafo.py`, `main.py`
**Standalone:** entrega o pipeline de análise verificada e a observabilidade do operador sem depender do Épico 2.

### Épico 2: O gestor abre um arquivo e sabe o que atender primeiro

O gestor recebe o HTML por anexo, abre no navegador sem instalar nada, e a fila de prioridade é a primeira coisa na tela — cada item com a frase do cliente que o colocou ali. Abaixo, ranking e sentimento com as ressalvas que dizem o que aquelas leituras não provam. Execução degradada aparece marcada no próprio arquivo.

**FRs covered:** FR-1b, FR-4, FR-8, FR-9, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15, FR-16, FR-17, FR-18
**NFRs:** NFR-6, NFR-9
**ADs:** AD-4, AD-10, AD-11, AD-13, AD-14, AD-15, AD-22
**Arquivos:** `pontuacao.py`, `agregacao.py`, `relatorio.py`, `templates/relatorio.html.j2`, `grafo.py`, `main.py`
**Standalone:** consome o Épico 1 e entrega o produto completo; nenhum épico posterior é necessário para funcionar.

### Épico 3: A fila prova que acerta e o grafo prova que é extensível

Os números do PRD deixam de ser afirmados e passam a ser medidos sobre a saída real do pipeline. M-1 rodado contra `docs/gabarito.csv`, NFR-1 cronometrado com cache desligado, M-6 demonstrado por diff. As três parcelas que a base nunca exercita ganham caso construído à mão, e a verificação de citação é exercitada por citação falsa injetada de propósito.

**FRs covered:** nenhum novo — este épico mede o que os anteriores construíram
**Cobre:** M-1, M-2, M-3, M-4, M-6, NFR-1, NFR-3, CM-1, CM-2, CM-3, CM-4, Q-4, Q-8
**Arquivos:** `tests/`, instrumentação pontual
**Standalone:** depende de 1 e 2; nenhum dos dois depende dele.

## Epic 1: O operador roda a base e sabe se pode confiar no resultado

O operador executa o comando sobre um CSV e o terminal responde com quatro números honestos — lidas, analisadas, não analisadas, sinais derrubados. Todo sinal que sobreviveu carrega citação literal verificada contra o texto original. Falha em um lote não derruba a execução dos demais.

> **Nota de ordenação.** `evidencia.py` vem antes de `analise.py` porque a spine declara a única exceção de dependência entre filtros: `analise` importa `evidencia`, já que a verificação roda sobre a resposta do modelo antes de o delta entrar no estado.

### Story 1.1: Contrato de estado e catálogo de sinais

As a desenvolvedor do pipeline,
I want o contrato de estado tipado e o catálogo de sinais em módulos próprios,
So that nenhuma etapa posterior invente forma de dado nem repita um código de sinal como literal solto.

**Acceptance Criteria:**

**Given** o módulo `plataforma/estado.py`
**When** ele é importado
**Then** expõe os `TypedDict` `Reclamacao`, `Sinal`, `Analise`, `Falha`, `Motivo`, `Pontuacao`, `Agregados` e `Estado` com os campos definidos em `state-contract.md`
**And** `estado.py` não importa nenhum outro módulo de `plataforma/`

**Given** a estrutura `Sinal`
**When** ela é inspecionada
**Then** tem exatamente `codigo`, `citacao` e `valida`
**And** `valida` é `bool` com default `False`, nunca `bool | None`
**And** não existem os campos `sinal_a`, `sinal_b` nem `evidencia` em lugar nenhum do contrato (AD-1, AD-20)

**Given** a estrutura `Estado`
**When** ela é inspecionada
**Then** `analises` e `falhas` são `Annotated[list[...], add]`
**And** `agregados` é do tipo `Agregados`, nunca `dict` cru (AD-8, AD-20)

**Given** a estrutura `Motivo`
**When** ela é inspecionada
**Then** `origem` é `Literal["sinal", "atributo"]` e `citacao` é `str | None` (AD-3)

**Given** o módulo `plataforma/catalogo.py`
**When** ele é importado
**Then** declara os seis códigos do catálogo de `risk-signals.md` — sinal B: `dinheiro_retido`, `registro_contraditorio`, `dano_continuado`, `prazo_estourado`; sinal A: `ameaca_explicita`, `lei_citada` — cada um com definição escrita e exemplo
**And** `dinheiro_retido` é definido como *a empresa está com dinheiro do cliente*, cobrindo as seis categorias que o gabarito marcou: estorno não feito, conta bloqueada, produto pago e não entregue, produto defeituoso não trocado, assinatura ainda cobrada, e débito sem contratação
**And** `ameaca_explicita` é um código do catálogo como qualquer outro, sujeito à mesma regra de evidência, e não um campo booleano à parte (AD-1)
**And** `ameaca_explicita` e `lei_citada` estão declarados como membros de um grupo saturado, para que `pontuacao.py` os leia sem repetir a regra
**And** declara a lista canônica de termos genéricos de produto
**And** nenhum outro módulo do pacote declara um código de sinal como literal (AD-18, AD-21)

**Given** a suíte de testes
**When** ela roda sem a variável de ambiente da chave de API definida
**Then** importar `estado` e `catalogo` funciona, sem credencial e sem rede (AD-7, AD-12)

### Story 1.2: Configuração validada antes de qualquer chamada paga

As a operador,
I want tamanho de lote e modelo configuráveis por variável de ambiente com faixa validada,
So that eu calibre a execução sem tocar código e sem conseguir configurar uma execução que o SPEC proíbe.

**Acceptance Criteria:**

**Given** um `.env` com `TAMANHO_LOTE=10`
**When** a configuração é carregada
**Then** o valor 10 é adotado sem alteração de código (NFR-2)

**Given** nenhuma variável de ambiente definida
**When** a configuração é carregada
**Then** os defaults declarados no código são adotados e a execução segue

**Given** `TAMANHO_LOTE=1` ou `TAMANHO_LOTE=26`
**When** a configuração é carregada
**Then** a execução encerra com mensagem nomeando a faixa permitida de 2 a 25
**And** nenhuma chamada ao modelo é feita antes desse encerramento (AD-17)

**Given** a chave de API
**When** o sistema precisa dela
**Then** ela é lida exclusivamente de variável de ambiente, via `python-dotenv`
**And** `.env.example` lista os nomes das variáveis sem nenhum valor (NFR-10)

**Given** o módulo `plataforma/config.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai` direta nem transitivamente (AD-7)

### Story 1.3: Ingestão que rejeita base inválida antes de gastar

As a operador,
I want que um CSV com schema errado seja recusado antes de qualquer chamada paga,
So that eu descubra o problema pelo nome dele e não pela fatura da API.

**Acceptance Criteria:**

**Given** `docs/reclamacoes_reclameaqui.csv`
**When** o nó `carregar` executa
**Then** produz 50 `Reclamacao` lidas com `utf-8-sig` e separador `;`
**And** o nome da primeira coluna não carrega BOM colado
**And** cada `data` está em ISO-8601, convertida de `DD/MM/AAAA`

**Given** um CSV sem uma das sete colunas esperadas
**When** o nó `carregar` executa
**Then** a execução encerra com mensagem nomeando a coluna faltante
**And** zero chamadas ao modelo foram feitas (FR-3)

**Given** um CSV com `ID_Reclamacao` repetido
**When** o nó `carregar` executa
**Then** a execução encerra nomeando o identificador repetido
**And** zero chamadas ao modelo foram feitas (FR-3)

**Given** um CSV com cabeçalho e nenhuma linha de dado
**When** o nó `carregar` executa
**Then** a execução encerra com mensagem clara, antes do fan-out, sem escrever arquivo algum (AD-13)

**Given** o mesmo arquivo processado duas vezes
**When** as duas execuções terminam a ingestão
**Then** o conjunto de identificadores produzido é idêntico (NFR-8)

**Given** o módulo `plataforma/ingestao.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai` direta nem transitivamente (AD-7)

### Story 1.4: Verificação de evidência determinística

As a gestor que vai agir sobre a fila,
I want que toda citação seja conferida contra o texto original por comparação de string,
So that nenhum sinal sobreviva sustentado por uma frase que o modelo inventou.

**Acceptance Criteria:**

**Given** um `Sinal` cuja `citacao` é substring exata do texto da reclamação e tem cinco palavras ou mais
**When** a verificação roda
**Then** aquele `Sinal` fica com `valida = True`

**Given** um `Sinal` cuja `citacao` não é substring do texto original
**When** a verificação roda
**Then** todo `Sinal` daquele mesmo `codigo` fica com `valida = False`, inclusive os pares do mesmo código cuja citação passou (AD-2)

**Given** um `Sinal` com citação de quatro palavras que é substring válida do texto
**When** a verificação roda
**Then** aquele `Sinal` fica com `valida = False` — o piso de cinco palavras é verificado no mesmo lugar que a substring (FR-6, AD-1)

**Given** um `Sinal` com `citacao` igual a string vazia
**When** a verificação roda
**Then** fica com `valida = False`, apesar de string vazia ser substring de qualquer texto

**Given** uma `Analise` fabricada à mão com citação falsa injetada de propósito
**When** a suíte de testes roda
**Then** a verificação derruba o código correspondente
**And** nenhuma chamada de rede é feita durante o teste (AD-12, CM-2)

**Given** o módulo `plataforma/evidencia.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai` direta nem transitivamente (AD-7)

### Story 1.5: Análise de um lote pelo modelo

As a operador,
I want que cada lote de reclamações volte do modelo com sentimento, produto e sinais já casados por identificador,
So that uma resposta incompleta ou inventada seja detectada em vez de corromper a base em silêncio.

**Acceptance Criteria:**

**Given** um lote de reclamações
**When** o payload é montado para o modelo
**Then** ele carrega apenas `id` e `texto` de cada reclamação
**And** `empresa` e `titulo` estão ausentes por construção, não por instrução no prompt (AD-16)

**Given** a chamada ao modelo
**When** a resposta é obtida
**Then** ela vem por `response_schema` do `google-genai`, derivado de `Analise` e `Sinal`
**And** nenhum parsing de texto livre é feito
**And** cada item traz `sentimento` em `{positivo, neutro, negativo}`, `produto` (`str | None`) e `sinais` — as três dimensões que FR-5 exige (CAP-2, CAP-3, CAP-4)

**Given** um lote de 20 e uma resposta com 19 itens
**When** o casamento por identificador roda
**Then** o identificador faltante é detectado e vira uma `Falha` que carrega aquele id (NFR-7, AD-5)

**Given** uma resposta que traz um identificador repetido ou um que não estava no lote
**When** o casamento por identificador roda
**Then** o item é descartado e não soma a agregado nenhum (NFR-7)

**Given** uma resposta que não casa com o `response_schema`
**When** ela é processada
**Then** vira falha de conteúdo registrada como `Falha`, não exceção que aborta a execução

**Given** cada sinal devolvido pelo modelo
**When** o delta do nó é montado
**Then** a verificação de evidência já rodou sobre ele antes de o delta entrar no estado (AD-1)

**Given** o campo `produto` devolvido pelo modelo
**When** ele entra no estado
**Then** vem como o modelo leu, sem julgamento de genérico
**And** `produto = None` significa apenas *o texto não permitiu identificar* (AD-21)

**Given** o pacote `plataforma/`
**When** os imports de todos os módulos são inspecionados
**Then** `analise.py` é o único que importa `google.genai`
**And** o cliente é construído dentro de `analisar_lote`, nunca em escopo de módulo
**And** `import plataforma.analise` funciona sem credencial definida (AD-7)

### Story 1.6: Fan-out por lote com falha absorvida

As a operador,
I want que cada lote seja uma execução de nó independente com política de repetição,
So that um lote que falha não gaste token nos que já voltaram corretos nem derrube a execução inteira.

**Acceptance Criteria:**

**Given** 50 reclamações e `tamanho_lote = 10`
**When** o nó `carregar` executa
**Then** ele emite 5 `Send` para `analisar_lote` (AD-8)

**Given** 50 reclamações e `tamanho_lote = 7`
**When** o fatiamento roda
**Then** o lote residual de tamanho 1 é fundido ao anterior
**And** nenhum `Send` é emitido com um único item — a chamada individual por reclamação é proibida (AD-17)

**Given** um lote que esgota a política de repetição
**When** o `error_handler` do `add_node` é acionado
**Then** ele produz uma única `Falha` com os ids daquele lote, a causa e o nó
**And** os demais lotes seguem executando normalmente (AD-9, AD-5, NFR-5)

**Given** uma falha de transporte como limite de taxa
**When** ela ocorre
**Then** a `retry_policy` declarada no `add_node` repete a chamada
**And** o código do nó não contém laço de repetição próprio (AD-9, NFR-4)

**Given** o gather das execuções de lote concluído
**When** o fan-out termina, antes de qualquer nó posterior
**Then** uma asserção verifica `len(reclamacoes) == len(analises) + sum(len(f["ids"]) for f in falhas)` (AD-6)
**And** a asserção vale sozinha nesta story — não depende de `pontuar`, que só existe no Épico 2

**Given** dois lotes quaisquer em execução
**When** um deles é processado
**Then** ele não lê o resultado do outro; `analises` e `falhas` acumulam pelo redutor `add` (AD-8, AD-19)

### Story 1.7: As quatro contagens do operador

As a operador,
I want ver ao encerrar quantas reclamações entraram, saíram, falharam e quantos sinais foram derrubados,
So that eu distinga uma execução limpa de uma execução silenciosamente degradada sem ler log.

**Acceptance Criteria:**

**Given** o comando invocado com o caminho de um CSV como argumento de linha de comando
**When** ele executa
**Then** a execução roda sobre aquele arquivo, sem caminho embutido no código (FR-1a)
**And** invocar sem argumento encerra com mensagem de uso
**And** esta é a metade de FR-1 que o Épico 1 precisa para ser executável; a escrita e a nomeação do HTML são FR-1b, na Story 2.6

**Given** uma execução concluída
**When** o comando encerra
**Then** o terminal imprime quatro números: total lidas, total analisadas, total não analisadas e total de códigos de sinal derrubados na verificação (FR-2)

**Given** o total não analisado
**When** ele é calculado
**Then** vale `sum(len(f["ids"]) for f in falhas)` — reclamações afetadas, não eventos de `Falha`
**And** a contagem de eventos também está disponível ao operador (AD-5)

**Given** o total de derrubados
**When** ele é calculado
**Then** conta **códigos distintos** que tiveram ao menos um `Sinal` com `valida = False`
**And** não conta pares reprovados nem reclamações afetadas (AD-2)

**Given** uma execução em que `len(analises) == 0`
**When** ela chega ao fim do fan-out
**Then** encerra com a causa nomeada e não escreve arquivo algum (AD-13)

**Given** a API indisponível ou sem credencial válida
**When** a execução encerra
**Then** a causa é nomeada — indisponibilidade ou credencial ausente, não uma mensagem genérica
**And** informa **quantos lotes haviam concluído** antes do encerramento
**And** sem esse número o operador não distingue "a chave está errada e nada rodou" de "a API caiu no meio e três de cinco lotes voltaram" (§6 do PRD)

**Given** a base de referência com a API respondendo normalmente
**When** a execução termina
**Then** reporta 50 lidas, 50 analisadas, 0 não analisadas
**And** esta AC é **verificação manual de aceitação** — exige rede e crédito, e é a única do Épico 1 fora da suíte determinística (AD-12)

**Given** o módulo `main.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai` diretamente (AD-7)

## Epic 2: O gestor abre um arquivo e sabe o que atender primeiro

O gestor recebe o HTML por anexo, abre no navegador sem instalar nada, e a fila de prioridade é a primeira coisa na tela — cada item com a frase do cliente que o colocou ali. Abaixo, ranking e sentimento com as ressalvas que dizem o que aquelas leituras não provam. Execução degradada aparece marcada no próprio arquivo.

### Story 2.1: Pontuação que carrega o motivo de cada item da fila

As a gestor,
I want que cada item da fila chegue acompanhado do que o colocou ali,
So that eu decida sobre a evidência e não sobre a palavra do sistema.

**Acceptance Criteria:**

**Given** o módulo `plataforma/pontuacao.py`
**When** os pesos são declarados
**Then** vivem num único mapeamento com o código do catálogo como chave, derivado da tabela de `risk-signals.md`
**And** nenhum código de sinal aparece como literal solto no módulo (AD-18)
**And** o corte binário de 3 pontos é declarado no mesmo lugar

**Given** os pesos por código, ratificados em 2026-08-07 contra a tabela canônica de `risk-signals.md`
**When** eles são declarados
**Then** `dinheiro_retido` = 3, `ameaca_explicita` = 3, `lei_citada` = 3, `registro_contraditorio` = 2, `dano_continuado` = 2, `prazo_estourado` = 1
**And** `Status == "Respondida"` aplica modificador −1, nunca como parcela independente

**Given** uma reclamação com `ameaca_explicita` **e** `lei_citada` ambos válidos
**When** `pontuar` executa
**Then** o grupo do sinal A contribui 3 pontos, não 6 — os dois códigos saturam
**And** a saturação é lida da declaração do grupo em `catalogo.py`, não reimplementada em `pontuacao.py` (AD-18)

**Given** uma reclamação com `dinheiro_retido` válido e `Status = "Respondida"`
**When** `pontuar` executa
**Then** a pontuação é 2 e o item **não** entra na fila
**And** este é o caso que dá precisão de 100% à regra medida — os dois únicos falsos positivos observados são cobranças indevidas com `Status = Respondida` (M-1)

**Given** uma `Analise` com um `Sinal` de `valida = True`
**When** `pontuar` executa
**Then** produz um `Motivo` com `origem = "sinal"` e `citacao` não nula, vinda do modelo (AD-3)

**Given** um item que entra na fila apenas por atributo determinístico — categoria ou `Status`
**When** `pontuar` executa
**Then** produz um `Motivo` com `origem = "atributo"` e `citacao` nula
**And** o rótulo nomeia o motivo estrutural, nunca uma citação vazia (FR-9, AD-3)

**Given** um `codigo` cujo `Sinal` ficou com `valida = False`
**When** `pontuar` executa
**Then** aquele código não soma pontos, inclusive se outro par do mesmo código passou na verificação (AD-2)

**Given** o estado após `pontuar`
**When** ele é inspecionado
**Then** `pontuacoes` contém uma `Pontuacao` por reclamação analisada, com `id`, `pontos`, `na_fila` e `motivos`
**And** `pontuar` é o único nó que escreve `pontuacoes`, incluindo o valor de `na_fila` (AD-19)

**Given** `Analise` fabricada à mão exercitando `ameaca_explicita`, `dano_continuado` e `registro_contraditorio`
**When** a suíte roda
**Then** cada uma das três parcelas produz pontuação, sem nenhuma chamada de rede (AD-12, Q-4)

**Given** o módulo `plataforma/pontuacao.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai` direta nem transitivamente (AD-7)

### Story 2.2: Agregação que fecha com a contagem direta

As a gestor,
I want números agregados que batem com a saída por reclamação,
So that eu não descubra depois que o ranking somava algo diferente do que a fila mostrava.

**Acceptance Criteria:**

**Given** o estado com `analises` e `pontuacoes` preenchidos
**When** `agregar` executa
**Then** produz `Agregados` como `TypedDict`, com ranking de produtos por volume e distribuição de sentimento
**And** cada número agregado bate com a contagem direta sobre a saída por reclamação (CAP-7, AD-20)

**Given** uma `Analise` com `produto = None`
**When** `agregar` executa
**Then** ela entra no ranking sob o rótulo `não identificado`, com seu total
**And** não é descartada nem atribuída a um produto por aproximação (FR-8)

**Given** uma `Analise` cujo `produto` está na lista canônica de termos genéricos de `catalogo.py`
**When** `agregar` executa
**Then** ela é marcada como genérica no ranking
**And** essa marcação é feita por `agregar`, nunca pelo modelo (AD-21)

**Given** o estado completo
**When** `agregar` executa
**Then** `Agregados` carrega as contagens que FR-2, FR-14, NFR-6, CM-2 e CM-3 reportam: lidas, analisadas, não analisadas, códigos derrubados, ocupação da fila e taxa de produto não nomeado (AD-22)
**And** CM-3 soma produto nulo **e** produto genérico, não apenas o nulo

**Given** mais de 10% das reclamações não analisadas
**When** `agregar` executa
**Then** `Agregados` carrega o indicador de degradação já resolvido como booleano
**And** o denominador é reclamações afetadas, não eventos de `Falha` (NFR-6, AD-5)

**Given** uma execução em que o modelo propôs ao menos um código de sinal e todos foram derrubados
**When** `agregar` executa
**Then** o indicador de degradação também fica verdadeiro, ainda que a contagem de não analisadas seja zero (NFR-6, AD-13)

**Given** as reclamações com `na_fila = True`
**When** `agregar` executa
**Then** produz a fila ordenada por `pontos` decrescente
**And** o desempate é por `data` mais antiga primeiro, e persistindo o empate por `id` em ordem crescente — a ordem é total e determinística, para que duas execuções sobre a mesma entrada produzam a mesma fila (NFR-8)

**Given** `agregar`
**When** ele executa
**Then** ordena e conta, e nunca decide pertencimento à fila — `na_fila` já veio de `pontuar` (AD-19)
**And** `agregados` é escrito só por ele

**Given** o módulo `plataforma/agregacao.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai` direta nem transitivamente (AD-7)

### Story 2.3: Relatório com a fila no topo e a evidência à vista

As a gestor,
I want abrir o arquivo e ver primeiro a fila de prioridade, com a frase do cliente em cada item,
So that eu responda *o que atendo primeiro* sem rolar a página nem clicar em nada.

**Acceptance Criteria:**

**Given** o módulo `plataforma/relatorio.py`
**When** o ambiente de template é construído
**Then** existe exatamente um `Environment` do Jinja2, criado nesse módulo, com `autoescape=True` literal
**And** `select_autoescape` não é usado — o seletor casaria `relatorio.html.j2` no `default=False` e deixaria o escape desligado
**And** nenhum outro módulo do pacote constrói um `Environment` (AD-10)

**Given** o relatório renderizado
**When** ele é aberto no navegador
**Then** a fila de prioridade é o primeiro conteúdo, antes de qualquer agregado (FR-11)
**And** o item mais grave é o primeiro da fila — o template preserva a ordem que `agregar` produziu e não reordena (AD-19, AD-22)
**And** sem isso a fila é uma lista com adjetivo, e a UJ-2 depende de a primeira coisa na tela ser também a mais grave

**Given** um item da fila
**When** ele é renderizado
**Then** exibe seu `Motivo` — citação literal quando `origem = "sinal"`, rótulo estrutural quando `origem = "atributo"` — como conteúdo visível
**And** não como detalhe expansível, acordeão ou tooltip (FR-12, FR-9)

**Given** o template
**When** suas condicionais são lidas
**Then** nenhuma delas consulta `Reclamacao` para descobrir **por que** um item está na fila
**And** `reclamacoes` é lido apenas para exibir empresa, título e data (AD-4)

**Given** uma reclamação cujo texto contém caracteres de marcação HTML
**When** ela é renderizada
**Then** aparece escapada e não altera a estrutura da página

**Given** o relatório renderizado
**When** ele é lido
**Then** rótulos, categorias e números estão em português do Brasil, com a convenção numérica local (FR-17)

**Given** uma fila vazia porque nenhuma reclamação atingiu o corte
**When** o relatório é renderizado
**Then** a fila aparece declarada como vazia — fila vazia é informação, não erro (§6 do PRD)

### Story 2.4: Gráficos embutidos com a ressalva ao lado

As a gestor,
I want ver a distribuição de sentimento e o ranking de produtos como gráfico, com a limitação de cada leitura escrita ao lado,
So that eu não dê aos dois a mesma autoridade que dou à fila.

**Acceptance Criteria:**

**Given** o relatório renderizado
**When** os gráficos são inspecionados
**Then** são `<svg>` escrito no próprio template
**And** não há biblioteca de plotagem, `<script src>` nem `<link href>` externo (FR-15, AD-11)

**Given** o gráfico de distribuição de sentimento
**When** ele é renderizado
**Then** carrega ao lado, no corpo do relatório, uma ressalva fixa nomeando o que limita essa leitura nesta base
**And** a ressalva é texto do template, não calculada em tempo de execução (FR-18, AD-14)

**Given** o ranking de produtos
**When** ele é renderizado
**Then** carrega ao lado a ressalva de que volume não equivale a gravidade — o produto mais reclamado tende a ser o mais vendido (FR-13)
**And** a linha `não identificado` aparece visível com seu total (FR-8)
**And** produto genérico aparece marcado como tal, usando a marcação que `agregar` já resolveu (FR-13, AD-21)

**Given** as duas ressalvas
**When** sua posição é verificada
**Then** estão ao lado do respectivo gráfico, nunca em nota de rodapé (FR-18, AD-14)

**Given** os textos de ressalva
**When** eles são localizados no código
**Then** vivem no template, não em Python (AD-10)

### Story 2.5: O relatório declara sua própria confiabilidade

As a gestor,
I want que o arquivo me diga em que execução ele nasceu e se ela foi confiável,
So that eu não trate um relatório sobre metade da base como se fosse sobre a base inteira.

**Acceptance Criteria:**

**Given** o relatório renderizado
**When** seu cabeçalho é lido
**Then** informa a data da execução, o total de reclamações analisadas e o total não analisado por falha (FR-14)
**And** esses números vêm de `Agregados`; o template não soma, não divide e não compara com limiar (AD-22)

**Given** uma execução com o indicador de degradação verdadeiro
**When** o relatório é renderizado
**Then** carrega marca de degradação visível ao leitor no próprio arquivo
**And** essa marca não depende de o leitor procurar por ela (NFR-6)

**Given** uma execução limpa
**When** o relatório é renderizado
**Then** nenhuma marca de degradação aparece — uma execução confiável e uma degradada não têm a mesma aparência

**Given** o relatório renderizado
**When** ele é lido
**Then** declara em texto visível que a classificação de risco é heurística de engenharia e não parecer jurídico (FR-16)
**And** essa declaração recebe o mesmo tratamento estrutural das ressalvas de FR-18 (AD-14)

### Story 2.6: O arquivo entregue nasce seguro e autocontido

As a operador,
I want que o relatório seja escrito com nome previsível, sem nunca apagar um anterior em silêncio,
So that eu possa comparar execuções e não vaze um relatório de base real para o repositório público.

**Acceptance Criteria:**

**Given** a execução sobre `docs/reclamacoes_reclameaqui.csv`
**When** o arquivo é escrito
**Then** nasce ao lado do CSV de entrada
**And** o nome começa com `relatorio-`, seguido do nome do arquivo de entrada e da data da execução (FR-1b, AD-15)
**And** casa com o glob `relatorio-*.html` já coberto pelo `.gitignore` (DG-2)

**Given** a execução concluída
**When** o comando encerra
**Then** o caminho final do arquivo é impresso ao operador (FR-1b)

**Given** um arquivo de saída que já existe
**When** a execução chega ao momento de escrever
**Then** encerra sem escrever, nomeando o arquivo existente (FR-4)

**Given** o sinalizador explícito de sobrescrita na linha de comando
**When** a execução roda sobre um arquivo existente
**Then** sobrescreve (FR-4)

**Given** `len(analises) == 0`
**When** a execução chega ao momento de escrever
**Then** encerra com a causa nomeada e não escreve arquivo algum (AD-13)

**Given** o HTML gerado
**When** seu conteúdo é varrido
**Then** não contém nenhuma referência a host externo — nem `src=`, nem `href=`, nem `@import` apontando para fora do arquivo
**And** essa varredura é um teste automatizado, não inspeção manual (FR-10, AD-11)

**Given** o HTML gerado
**When** ele é aberto em navegador atual com a rede desligada
**Then** renderiza completo, sem servidor, sem instalação e sem plugin (FR-10, NFR-9)

**Given** o HTML gerado enviado como anexo único de e-mail
**When** o destinatário o abre
**Then** renderiza igual ao original (NFR-9)

## Epic 3: A fila prova que acerta e o grafo prova que é extensível

Os números do PRD deixam de ser afirmados e passam a ser medidos sobre a saída real do pipeline. As parcelas que a base nunca exercita já ganharam caso construído nas Stories 1.4 e 2.1; o que falta é o que só existe com o pipeline inteiro montado.

> **Regra deste épico: o número medido é registrado como saiu.** Um resultado que reprova a métrica é entregável deste épico tanto quanto um que aprova. O PRD já registra que os limiares foram fixados com o resultado à vista, e repetir esse movimento aqui esvaziaria a medição.

### Story 3.1: A fila do pipeline medida contra o gabarito

As a avaliador técnico,
I want ver a precisão e o recall da fila que o pipeline realmente produz,
So that eu saiba que a métrica mede o produto e não um classificador de medição que roda por fora dele.

**Acceptance Criteria:**

**Given** o pipeline completo executado sobre `docs/reclamacoes_reclameaqui.csv`
**When** o campo `na_fila` das `pontuacoes` é comparado com `docs/gabarito.csv`
**Then** a comparação usa a saída do próprio pipeline, nunca `baseline.py` nem `classificador.py` (M-1)
**And** o casamento entre saída e gabarito é por `ID_Reclamacao`, nunca por posição

**Given** a comparação concluída
**When** os números são calculados
**Then** precisão, recall e as contagens de TP, FP e FN são registrados
**And** o critério de aceitação é precisão ≥ 95% com recall ≥ 65% (M-1)

**Given** um resultado que não atinge o critério
**When** ele é registrado
**Then** o número real é reportado como saiu, com os itens divergentes nomeados por identificador
**And** o limiar não é reajustado para acomodar o resultado
**And** a story está **pronta quando a medição está registrada** — um resultado abaixo do limiar abre um item de correção de curso, não reprova o épico nem bloqueia a entrega

**Given** a fila produzida
**When** sua ocupação é calculada
**Then** a proporção da base que entrou na fila é registrada
**And** acima de 40% dispara alerta: a fila deixou de ordenar (CM-1)

**Given** a saída do pipeline
**When** CM-2, CM-3 e CM-4 são lidos de `Agregados`
**Then** os três valores são registrados junto com a medição de M-1
**And** CM-2 em zero constante é anotado como indistinguível de mecanismo morto, já que o caso sintético da Story 1.4 é o único que o exercita

**Given** as citações presentes no relatório final
**When** elas são verificadas
**Then** 100% são trecho literal do texto original com no mínimo cinco palavras (M-2)

### Story 3.2: O tempo e o custo de uma execução, medidos

As a operador,
I want saber quanto uma execução real demora e quanto ela consome,
So that o teto de dois minutos deixe de ser suposição e eu saiba se cabe no tier gratuito.

**Acceptance Criteria:**

**Given** o pipeline completo e o cache de análises desligado
**When** uma execução ponta a ponta roda sobre as 50 reclamações
**Then** o tempo total é cronometrado e registrado (M-3, NFR-1)
**And** a medição com cache ligado é descartada — ela mede o disco, não o pipeline (Q-8)

**Given** o tempo medido
**When** ele é comparado ao teto de 2 minutos
**Then** a marca `[ASSUMPTION]` de NFR-1 é substituída pelo número real no PRD
**And** Q-8 é movida para resolvida, com a data da medição

**Given** um tempo acima do teto
**When** ele é registrado
**Then** é reportado como saiu, e a decisão entre ajustar o teto ou o pipeline fica explícita, não implícita

**Given** a mesma execução
**When** o consumo é apurado
**Then** o número de chamadas ao modelo e o volume de tokens são registrados
**And** confirma-se que a execução completa cabe no tier de teste gratuito da API (M-4, NFR-3)

**Given** o número de chamadas
**When** ele é conferido
**Then** equivale ao número de lotes emitidos, e nenhuma reclamação foi analisada duas vezes por desenho do fluxo (NFR-4, AD-17)

### Story 3.3: A extensibilidade do grafo, demonstrada por diff

As a desenvolvedor que vai plugar o roadmap,
I want provar que uma etapa nova entra sem alterar as existentes,
So that a única métrica que mede o objetivo declarado do projeto pare de ser uma afirmação.

**Acceptance Criteria:**

**Given** o grafo do v1 completo
**When** um nó novo sem efeito é acrescentado ao `StateGraph`
**Then** o diff não toca a assinatura de nenhum nó existente (M-6, CAP-9)
**And** o diff não toca `estado.py` além de acrescentar chave, se acrescentar

**Given** o nó novo acrescentado
**When** o pipeline roda
**Then** produz o mesmo relatório de antes, sem regressão

**Given** o exercício concluído
**When** ele é registrado
**Then** o diff é anexado como evidência de M-6
**And** o nó de demonstração é removido do código entregue

**Given** os itens de `roadmap.md`
**When** eles são conferidos contra o resultado do exercício
**Then** os pontos que a spine declara **não** aditivos — cache (exige versão do prompt no estado), cascata (`Sinal.valida` é booleano), loop de crítica (exige terceiro balde além de `analises` e `falhas`), níveis de criticidade (`na_fila` é booleano) — são registrados como tais
**And** M-6 é declarada atendida no eixo que ela cobre, sem ser inflada para cobrir esses quatro
