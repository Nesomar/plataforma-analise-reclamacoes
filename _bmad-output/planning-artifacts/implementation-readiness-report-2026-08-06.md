---
stepsCompleted: ['step-01-document-discovery', 'step-02-prd-analysis', 'step-03-epic-coverage-validation', 'step-04-ux-alignment', 'step-05-epic-quality-review', 'step-06-final-assessment']
readinessStatus: 'PRONTO'
resolvedOn: '2026-08-07'
documentsIncluded:
  - '_bmad-output/planning-artifacts/prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/epics.md'
  - '_bmad-output/specs/spec-plataforma-analise-reclamacoes/SPEC.md'
  - '_bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md'
  - '_bmad-output/specs/spec-plataforma-analise-reclamacoes/risk-signals.md'
  - '_bmad-output/specs/spec-plataforma-analise-reclamacoes/roadmap.md'
---

# Relatório de Avaliação de Prontidão para Implementação

**Data:** 2026-08-06
**Projeto:** plataforma-analise-reclamacoes

## Passo 1 — Inventário de Documentos

### PRD

**Documentos inteiros:**
- `prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md` (27.204 bytes, 2026-08-06)

**Companheiros (contexto, não fonte primária):**
- `reconcile-brainstorm.md`, `reconcile-dados.md`, `reconcile-spec.md`
- `review-avaliador-portfolio.md`, `review-delta-arquitetura.md`, `review-edge-cases.md`, `review-rubric.md`

**Documentos shardados:** nenhum

### Arquitetura

**Documentos inteiros:**
- `architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md` (22.925 bytes, 2026-08-06)

**Companheiros:**
- `reviews/reconcile-prd.md`, `reviews/reconcile-spec.md`, `reviews/review-adversarial.md`, `reviews/review-rubrica.md`, `reviews/review-tecnologia.md`
- `arquitetura.html` (projeção de apresentação — não é fonte de verdade)

**Documentos shardados:** nenhum

### Épicos e Stories

**Documentos inteiros:**
- `planning-artifacts/epics.md` (47.333 bytes, 2026-08-06) — 3 épicos, 16 stories

**Documentos shardados:** nenhum

### UX Design

**Documentos inteiros:** nenhum encontrado
**Documentos shardados:** nenhum encontrado

### SPEC (contrato canônico — fora de `planning_artifacts`)

- `specs/spec-plataforma-analise-reclamacoes/SPEC.md` (10.448 bytes)
- `state-contract.md`, `risk-signals.md`, `roadmap.md`, `architecture-diagrams.md`

### Dados de referência (`project_knowledge`)

- `docs/gabarito-marcacao.md`, `docs/gabarito.csv`, `docs/gabarito-v1.csv`, `docs/reclamacoes_reclameaqui.csv`

## Problemas Identificados no Passo 1

| Severidade | Achado | Impacto |
|---|---|---|
| ✅ OK | Zero duplicados (nenhum doc em forma inteira + shardada) | Nenhuma resolução necessária |
| ⚠️ AVISO | Documento de UX ausente em `planning-artifacts/` | Produto possui superfície de UI (páginas de relatório e de avaliador citadas no PRD). Avaliação de UX será feita apenas a partir do que PRD e epics descrevem. Decisão do usuário: prosseguir. |
| ⚠️ AVISO | `project-context.md` ausente, apesar de referenciado nos `persistent_facts` da skill | Regras de projeto para IA não carregadas nesta execução |

**Decisão do usuário:** prosseguir sem documento de UX dedicado; lacuna tratada como achado do relatório.

---

## Passo 2 — Análise do PRD

**Fonte:** `_bmad-output/planning-artifacts/prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md` (lido integralmente, 219 linhas)

### Requisitos Funcionais

**Execução e feedback ao operador**

- **FR-1** — O sistema aceita o caminho do CSV como argumento de linha de comando e escreve o HTML ao lado do CSV de entrada. O nome começa com `relatorio-`, seguido do nome do arquivo de entrada e da data da execução — o prefixo vem primeiro para que o relatório nasça coberto pelo `.gitignore` e não entre no repositório público (DG-2). O caminho final é impresso ao encerrar.
- **FR-2** — Ao encerrar, o sistema reporta ao operador: total de reclamações lidas, total analisadas com sucesso, total não analisadas, e total de sinais derrubados pela verificação de evidência.
- **FR-3** — CSV com coluna ausente, schema divergente ou identificador duplicado é rejeitado antes de qualquer chamada de LLM, com mensagem que nomeia a causa. Formato de origem validado em `state-contract.md` — separador `;`, UTF-8 com BOM, datas em `DD/MM/AAAA`. Realiza CAP-1.
- **FR-4** — Se o arquivo de saída já existir, o sistema encerra sem escrever, nomeando o arquivo existente. Sobrescrever exige sinalizador explícito na linha de comando.

**Análise**

- **FR-5** — Cada reclamação recebe sentimento, produto e sinais de risco. Realiza CAP-2, CAP-3 e CAP-4.
- **FR-6** — Todo sinal de risco marcado carrega ao menos uma citação literal do texto, com no mínimo cinco palavras. Sinal sem citação, ou com citação curta demais, não é registrado. Realiza CAP-4.
- **FR-7** — Antes de compor o resultado, o sistema confirma que cada citação existe no texto original e derruba o sinal específico que aquela citação sustentava — não o conjunto de sinais da reclamação. A derrubada é contabilizada e reportada (FR-2). Realiza CAP-5.
- **FR-8** — Reclamação cujo produto não é identificável recebe o rótulo `não identificado` e permanece na base analisada. O rótulo aparece como linha visível do ranking, com seu total. Não é descartada nem atribuída por aproximação.
- **FR-9** — Item que entra na fila apenas por parcela determinística — que não produz citação — é exibido com o motivo estrutural que o colocou ali (categoria, `Status`), não com citação vazia.

**Relatório**

- **FR-10** — O relatório é arquivo único que abre em navegador sem servidor, sem instalação e sem qualquer requisição de rede. Realiza CAP-8.
- **FR-11** — A fila de prioridade é o primeiro conteúdo do relatório, antes de qualquer agregado.
- **FR-12** — Cada item da fila exibe o que sustentou sua classificação — citação literal ou motivo estrutural de FR-9 — como conteúdo visível e não como detalhe expansível.
- **FR-13** — O ranking de produtos declara no próprio relatório que volume não equivale a gravidade e inclui `não identificado` como linha visível (FR-8). Produto identificado mas genérico é marcado como tal no ranking — a lista de termos genéricos é uma só e vive junto do catálogo de sinais; CM-3 mede sobre ela.
- **FR-14** — O relatório informa a data da execução, o total de reclamações analisadas e o total não analisado por falha.
- **FR-15** — O relatório apresenta graficamente a distribuição de sentimento e o ranking de produtos. Gráfico embutido no arquivo (SVG inline ou equivalente), nunca por biblioteca carregada da rede (FR-10).
- **FR-16** — O relatório declara, em texto visível ao leitor, que a classificação de risco é heurística de engenharia e não parecer jurídico.
- **FR-17** — O relatório é legível em português do Brasil, incluindo rótulos, categorias e números formatados na convenção local.
- **FR-18** — A distribuição de sentimento e o ranking de produtos carregam, ao lado do próprio gráfico e não em nota de rodapé, a ressalva que nomeia o que limita cada leitura. O texto é fixo, escrito para esta base — não é calculado em tempo de execução.

**Total de FRs: 18**

### Requisitos Não-Funcionais

**Desempenho**

- **NFR-1** — Execução sobre 50 reclamações completa em até 2 minutos, ponta a ponta. `[ASSUMPTION]` — teto não informado pelo usuário.
- **NFR-2** — Tamanho de lote configurável sem alteração de código.

**Custo**

- **NFR-3** — Execução completa sobre a base alvo cabe nos limites do tier de teste gratuito da API do Gemini.
- **NFR-4** — O sistema não analisa a mesma reclamação duas vezes por desenho do fluxo. Repetição por falha de transporte não conta como reanálise e é permitida.

**Confiabilidade**

- **NFR-5** — Falha em uma reclamação não interrompe a execução das demais. A reclamação afetada é registrada como não analisada e contabilizada (FR-2, FR-14).
- **NFR-6** — O sistema marca o relatório como degradado, no próprio arquivo e de forma visível ao leitor, quando: (1) acima de 10% de reclamações não analisadas; ou (2) todos os códigos de sinal propostos foram derrubados na verificação de evidência.
- **NFR-7** — Resposta do modelo casada por identificador, nunca por posição. Detecta identificador faltante e identificador não pedido — item repetido ou inventado é descartado, não somado.
- **NFR-8** — Duas execuções sobre o mesmo arquivo produzem os mesmos identificadores de reclamação.

**Portabilidade**

- **NFR-9** — O relatório abre corretamente em navegador atual sem plugin e sobrevive ao encaminhamento por e-mail como anexo único.
- **NFR-10** — A chave de API é lida de variável de ambiente. Nenhuma credencial no código ou no repositório.

**Total de NFRs: 10**

### Requisitos Adicionais

**Governança de dados (DG-1 a DG-5)**

- **DG-1** — Apenas dados sintéticos versionados no repositório (verificado 2026-08-06).
- **DG-2** — Base real nunca entra no repositório, nem o relatório dela derivado.
- **DG-3** — Relatório sobre base real herda dados pessoais das citações e é documento restrito.
- **DG-4** — Chave de API não versionada; arquivo de ambiente coberto pelo `.gitignore` (cumprido 2026-08-06).
- **DG-5** — README declara explicitamente que o corpus é sintético (cumprido 2026-08-06).

**Comportamento em falha (§6)** — 14 linhas de tabela governadas pela regra: falha de infraestrutura encerra sem gerar relatório; falha de conteúdo é absorvida e contabilizada. Dois casos-limite explícitos: *nenhuma reclamação analisada* (encerra sem escrever) e *todos os códigos de sinal derrubados* (relatório degradado).

**Métricas (§7.1)** — M-1 (precisão ≥ 95%, recall ≥ 65% contra `docs/gabarito.csv`), M-2 (100% de citações literais com ≥ 5 palavras), M-3 (≤ 2 min), M-4 (tier gratuito), M-5 (legibilidade — **não avaliável sobre esta base**), M-6 (extensibilidade do grafo: nova etapa não altera assinatura de etapa existente).

**Contramétricas (§7.2)** — CM-1 (ocupação da fila < 40%), CM-2 (taxa de sinais derrubados; zero constante = mecanismo possivelmente morto), CM-3 (produto não nomeado = nulo + genérico; medido 38%), CM-4 (não analisadas por falha > 0 exige investigação).

**Fora de escopo (§8)** — sem interface além do HTML, sem autenticação, sem histórico entre execuções, sem agendamento.

**Questões em aberto (§9.1)** — Q-5 (origem da base real, ADIADA, não bloqueia v1), Q-8 (aferição de NFR-1 nunca cronometrada ponta a ponta).

### Avaliação de Completude do PRD

| Dimensão | Avaliação |
|---|---|
| Numeração e rastreabilidade | **Forte** — FRs e NFRs numerados sem lacuna (FR-1..18, NFR-1..10); referências cruzadas a CAP-*, DG-*, M-*, CM-* consistentes |
| Vínculo com o SPEC | **Forte** — o PRD declara explicitamente que não repete o SPEC e aponta as capacidades realizadas (CAP-1, 2, 3, 4, 5, 8) |
| Honestidade sobre limitações | **Forte, incomum** — §1 declara que 2 das 3 leituras do produto não são exercidas pela base; M-5 marcada como não avaliável |
| Comportamento em falha | **Forte** — tabela §6 cobre 14 modos de falha com regra organizadora explícita |
| Critérios de aceitação mensuráveis | **Forte** — M-1 com números medidos e limiar justificado; ressalva registrada de que limiares foram fixados após medir |
| Lacunas | NFR-1 permanece `[ASSUMPTION]` não aferido (Q-8); CAP-6, CAP-7 e CAP-9 não têm FR que os realize de forma nominal — a verificar no Passo 3 |

---

## Passo 3 — Validação de Cobertura dos Épicos

**Fonte:** `_bmad-output/planning-artifacts/epics.md` (lido integralmente, 802 linhas — 3 épicos, 16 stories)

### Matriz de Cobertura — Requisitos Funcionais

Cobertura verificada **contra as Acceptance Criteria reais**, não apenas contra o FR Coverage Map declarado no documento.

| FR | Requisito (resumo) | Cobertura em stories | Status |
|---|---|---|---|
| FR-1 | CSV como argumento; HTML `relatorio-*` ao lado; caminho impresso | Épico 2 / Story 2.6 | ✓ Coberto |
| FR-2 | Quatro contagens ao operador | Épico 1 / Story 1.7 | ✓ Coberto |
| FR-3 | Rejeição de schema/id duplicado antes de chamada paga | Épico 1 / Story 1.3 | ✓ Coberto |
| FR-4 | Arquivo existente encerra; flag para sobrescrever | Épico 2 / Story 2.6 | ✓ Coberto |
| FR-5 | Sentimento, produto e sinais por reclamação | Épico 1 / Story 1.5 | ✓ Coberto |
| FR-6 | Piso de cinco palavras na citação | Épico 1 / Story 1.4 | ✓ Coberto |
| FR-7 | Derrubada por código de sinal, contabilizada | Épico 1 / Stories 1.4 + 1.7 | ✓ Coberto |
| FR-8 | `não identificado` como linha visível do ranking | Épico 2 / Stories 2.2 + 2.4 | ✓ Coberto |
| FR-9 | Motivo estrutural sem citação | Épico 2 / Stories 2.1 + 2.3 | ✓ Coberto |
| FR-10 | Arquivo único, sem servidor, sem rede | Épico 2 / Story 2.6 | ✓ Coberto |
| FR-11 | Fila como primeiro conteúdo | Épico 2 / Story 2.3 | ✓ Coberto |
| FR-12 | Evidência visível, não expansível | Épico 2 / Story 2.3 | ✓ Coberto |
| FR-13 | Volume ≠ gravidade; genérico marcado | Épico 2 / Stories 2.2 + 2.4 | ✓ Coberto |
| FR-14 | Data, total analisado, total não analisado | Épico 2 / Story 2.5 | ✓ Coberto |
| FR-15 | Gráficos SVG inline | Épico 2 / Story 2.4 | ✓ Coberto |
| FR-16 | Ressalva de heurística, não parecer jurídico | Épico 2 / Story 2.5 | ✓ Coberto |
| FR-17 | pt-BR em rótulos e formatação | Épico 2 / Story 2.3 | ✓ Coberto |
| FR-18 | Ressalva fixa ao lado de cada gráfico | Épico 2 / Story 2.4 | ✓ Coberto |

### Matriz de Cobertura — Requisitos Não-Funcionais

| NFR | Cobertura em stories | Status |
|---|---|---|
| NFR-1 | Story 3.2 (cronometragem com cache desligado) | ✓ Coberto |
| NFR-2 | Story 1.2 (`TAMANHO_LOTE` por ambiente) | ✓ Coberto |
| NFR-3 | Story 3.2 (apuração de chamadas e tokens) | ⚠️ Coberto, **mas mapeado errado** — o resumo de cobertura (linha 172) atribui NFR-3 ao Épico 1; nenhuma AC do Épico 1 o exercita |
| NFR-4 | Stories 1.6 + 3.2 | ✓ Coberto |
| NFR-5 | Story 1.6 (`error_handler` absorve o lote) | ✓ Coberto |
| NFR-6 | Stories 2.2 + 2.5 (duas condições, indicador em `Agregados`) | ✓ Coberto |
| NFR-7 | Story 1.5 (casamento por id; faltante, repetido, inventado) | ✓ Coberto |
| NFR-8 | Story 1.3 (identificadores idênticos entre execuções) | ✓ Coberto |
| NFR-9 | Story 2.6 (rede desligada, anexo de e-mail) | ✓ Coberto |
| NFR-10 | Story 1.2 (chave só por ambiente, `.env.example` sem valor) | ✓ Coberto |

### Requisitos Ausentes

Nenhum FR sem caminho de implementação. Os achados abaixo são de **precisão de cobertura**, não de ausência de FR.

#### Prioridade média

**A. Linha da tabela §6 do PRD sem AC: "API indisponível ou sem credencial"**

- **Texto do PRD:** *"Encerra com a causa nomeada, sem gerar relatório, informando quantos lotes haviam concluído."*
- **Cobertura atual:** parcial. `len(analises) == 0` encerra com causa nomeada e não escreve arquivo (Stories 1.7 e 2.6, AD-13). Mas **nenhuma AC exige informar quantos lotes haviam concluído** ao encerrar por indisponibilidade da API.
- **Impacto:** o operador perde o dado que distingue "a chave está errada e nada rodou" de "a API caiu no meio e 3 de 5 lotes voltaram". É diagnóstico, e é o único caso da tabela §6 sem AC correspondente.
- **Recomendação:** acrescentar AC à Story 1.7 (é onde vive a saída do operador).

**B. Contradição interna no epics.md sobre o tamanho do catálogo de sinais**

- **Linha 123** (`Additional Requirements`): *"Catálogo de sinais (CAP-4): `cobranca_indevida`, `prazo_estourado`, `registro_contraditorio`, `servico_nao_contratado`, `lei_citada`"* — **cinco códigos**.
- **Linha 241** (AC da Story 1.1): *"declara os sete códigos do catálogo — os cinco (...) mais `ameaca_explicita` e `dano_continuado`"* — **sete códigos**.
- **Impacto:** o mesmo documento manda declarar 5 e verificar 7. A Story 2.1 atribui peso aos sete, e a Story 2.1 exige caso de teste para `ameaca_explicita` e `dano_continuado` (Q-4). O número correto é 7; o inventário na linha 123 ficou desatualizado.
- **Recomendação:** corrigir a linha 123 para os sete códigos, ou marcá-la explicitamente como "os cinco do sinal B de `risk-signals.md`".

#### Prioridade baixa

**C. Pesos por código marcados `[ASSUMPTION]` não ratificados** — Story 2.1, linha 483: a correspondência entre as parcelas nomeadas em `risk-signals.md` e os códigos do catálogo está declarada como pendente de ratificação *antes da implementação*. Bloqueia a Story 2.1, não o épico inteiro.

**D. DG-1, DG-3 e DG-5 sem AC** — DG-2 é verificado pela Story 2.6 (glob `relatorio-*.html` no `.gitignore`) e DG-4 pela Story 1.2 (`.env.example`). DG-1 (corpus sintético), DG-3 (relatório de base real é restrito) e DG-5 (README declara o corpus) já constam como **cumpridos** no PRD e são de repositório, não de código. Sem impacto na implementação; registrado por completude.

**E. M-5 sem cobertura, por decisão** — o PRD declara M-5 não avaliável sobre esta base. Os épicos não a mencionam. Coerente, não é lacuna.

### Estatísticas de Cobertura

- **Total de FRs no PRD:** 18
- **FRs cobertos nos épicos (verificado em AC):** 18
- **Percentual de cobertura de FR:** **100%**
- **Total de NFRs no PRD:** 10
- **NFRs cobertos nos épicos (verificado em AC):** 10 (**100%**) — 1 com atribuição de épico incorreta no mapa
- **FRs presentes nos épicos e ausentes do PRD:** nenhum
- **Invariantes de arquitetura (AD-1 a AD-22):** 22/22 referenciados em pelo menos uma AC
- **Métricas com story dedicada:** M-1, M-2, M-3, M-4, M-6 e CM-1 a CM-4 (Épico 3); M-5 excluída por decisão registrada

---

## Passo 4 — Alinhamento de UX

### Status do Documento de UX

**Não encontrado.** Nenhum arquivo casando `*ux*.md` em `planning-artifacts/`, inteiro ou shardado.

**A interface está implícita?** **Sim.** O produto entrega uma superfície visual e um dos dois papéis do PRD só interage com ela:

- §2.2 do PRD define o **Leitor** (gestor) que *"recebe o HTML pronto por e-mail ou chat e abre no navegador"* e *"nunca vê terminal"*.
- **UJ-2** é uma jornada de UI ponta a ponta: abrir o anexo, ver a fila no topo, ler a frase do cliente, decidir.
- **FR-10 a FR-18** — nove requisitos funcionais — são todos sobre apresentação: ordem do conteúdo, visibilidade da evidência, gráficos, ressalvas, idioma e formatação numérica.

Portanto: **UX ausente com UI implicada — aviso emitido.** Avaliação feita, por decisão do usuário no Passo 1, contra o substituto que o projeto adotou.

### O Substituto Adotado

O `epics.md` (linha 21 e seção *UX Design Requirements*) declara UX como **não aplicável** e delega as exigências visuais aos FRs e a três invariantes de arquitetura. A delegação se sustenta:

| Preocupação de UX | Onde está resolvida |
|---|---|
| Estrutura e hierarquia da página | FR-11 (fila primeiro), FR-12 (evidência visível), AD-4 (template não deriva, só exibe) |
| Tecnologia de renderização | AD-10 (um `Environment` Jinja2, `autoescape=True` literal) |
| Autocontenção do artefato | AD-11, FR-10, FR-15, NFR-9 (nenhum byte vem da rede) |
| Enquadramento epistêmico (o que cada leitura não prova) | FR-13, FR-16, FR-18, AD-14 (ressalva ao lado do gráfico, não em rodapé) |
| Localização | FR-17 (pt-BR, convenção numérica local) |
| Segurança de conteúdo do usuário | AD-10 + AC da Story 2.3 (texto com marcação HTML aparece escapado) |

### Alinhamento UX ↔ PRD ↔ Arquitetura

Sem documento de UX, a validação é entre PRD e Arquitetura sobre a superfície visual.

- **PRD ↔ Arquitetura: alinhados.** Cada FR de relatório tem AD que o vincula — FR-10/FR-15 → AD-11; FR-11/FR-12 → AD-4; FR-13/FR-16 → AD-10; FR-18 → AD-14; FR-1 → AD-15; FR-14/NFR-6 → AD-22. Nenhum FR de apresentação órfão de invariante.
- **UJ-2 é suportada explicitamente.** AD-4 justifica o acesso de `renderizar` a `reclamacoes` citando UJ-2 nominalmente: *"sem os quais a fila é uma lista de identificadores e a UJ-2 não acontece"*.
- **Nenhum componente de UI sem suporte arquitetural.** Não há filtro, ordenação interativa nem exportação — §8 do PRD os exclui, e a arquitetura não os prevê. Coerente.

### Avisos

**⚠️ AVISO 1 (médio) — A ordenação da fila não tem AC.**
"Fila de prioridade" implica ordem por prioridade, e AD-19 atribui a ordenação a `agregar` (*"ordena e conta, nunca decide pertencimento"*). Mas nenhuma AC declara que os itens da fila são exibidos em ordem decrescente de `pontos`: a Story 2.2 diz que `agregar` produz "ranking de produtos por volume e distribuição de sentimento" sem mencionar a ordenação da fila, e a Story 2.3 exige apenas que a fila seja o primeiro conteúdo. Uma implementação que renderiza a fila na ordem de leitura do CSV passa em todas as ACs e quebra a promessa central de UJ-2 (*"a primeira coisa na tela"* precisa ser também *a mais grave*).
**Recomendação:** acrescentar AC à Story 2.2 (`agregar` ordena a fila por `pontos` decrescente, com desempate declarado) e à Story 2.3 (o template preserva a ordem recebida).

**⚠️ AVISO 2 (baixo) — Acessibilidade dos gráficos SVG não especificada.**
FR-15 e AD-11 fixam SVG inline. Nenhum requisito trata de `<title>`/`<desc>`, `role`, contraste ou alternativa textual. O ranking e a distribuição existem também como número no `Agregados`, então há caminho barato — mas nenhuma AC o exige. Público conhecido é um gestor único; risco real é baixo.

**⚠️ AVISO 3 (baixo) — Comportamento em base grande não definido.**
Nada define truncamento, paginação ou limite de itens da fila. Sobre 50 reclamações é irrelevante; sobre uma base real (Q-5, adiada) um HTML autocontido com milhares de itens é um problema de entrega por e-mail que colide com NFR-9. Consistente com Q-5 estar adiada — registrado, não bloqueante.

**Sem impedimento.** A ausência de documento de UX é aceitável neste projeto porque a superfície é um artefato estático de leitura única e as decisões visuais estão fixadas em FR e AD verificáveis. O AVISO 1 é a única lacuna com consequência funcional.

---

## Passo 5 — Revisão de Qualidade dos Épicos

Validação contra os padrões do workflow `create-epics-and-stories`: valor de usuário, independência de épicos, ausência de dependência prospectiva, dimensionamento e completude das ACs.

### 5.1 Estrutura dos Épicos

#### Foco em valor de usuário

| Épico | Título | Persona atendida | Veredito |
|---|---|---|---|
| 1 | *O operador roda a base e sabe se pode confiar no resultado* | Operador (§2.1 do PRD) | ✓ Valor de usuário — resultado, não marco técnico |
| 2 | *O gestor abre um arquivo e sabe o que atender primeiro* | Leitor/gestor (§2.2, UJ-2) | ✓ Valor de usuário |
| 3 | *A fila prova que acerta e o grafo prova que é extensível* | Avaliador técnico (§1 do PRD: *"Um avaliador técnico é parte do público"*) | 🟡 Limítrofe — ver Concern-1 |

Nenhum épico nomeado por camada técnica (`Setup Database`, `API Development`, `Infrastructure`). Os três títulos são frases de resultado observável.

#### Independência dos épicos

| Teste | Resultado |
|---|---|
| Épico 1 funciona sozinho | ⚠️ **Quase** — ver Issue-1 |
| Épico 2 funciona com a saída do Épico 1 | ✓ Sim |
| Épico 3 funciona com as saídas de 1 e 2 | ✓ Sim |
| Épico N exige Épico N+1 | ⚠️ **Um caso** — ver Issue-1 |
| Dependência circular | ✓ Nenhuma |

### 5.2 Dependências entre Stories

**Épico 1** — fluxo estritamente para trás, sem referência prospectiva:

`1.1 estado+catálogo` → `1.2 config` → `1.3 ingestão` → `1.4 evidência` → `1.5 análise` (usa 1.1, 1.4) → `1.6 fan-out` (usa 1.3, 1.5) → `1.7 contagens` (usa todas)

A nota de ordenação na abertura do Épico 1 justifica `evidencia` antes de `analise` citando a exceção de dependência declarada na spine. Correto e documentado.

**Épico 2** — `2.1 pontuação` → `2.2 agregação` → `2.3 relatório` → `2.4 gráficos` → `2.5 confiabilidade` → `2.6 escrita do arquivo`. Sem referência prospectiva.

**Épico 3** — `3.1 M-1/contramétricas`, `3.2 tempo/custo`, `3.3 extensibilidade`. Independentes entre si; todas dependem de 1 e 2. Sem referência prospectiva.

**Ponto forte registrado:** a Story 1.6 traz AC explícita de que a asserção de conservação (AD-6) *"vale sozinha nesta story — não depende de `pontuar`, que só existe no Épico 2"*. É exatamente a defesa contra dependência prospectiva que este passo procura, e ela está escrita.

### 5.3 Achados por Severidade

#### 🔴 Violações Críticas

**Nenhuma.** Nenhum épico técnico sem valor de usuário, nenhuma dependência circular, nenhuma story do tamanho de um épico.

#### 🟠 Problemas Maiores

**Issue-1 — FR-1 está no Épico 2, mas o Épico 1 precisa dele para ser executável.**

- **Onde:** `FR Coverage Map` (linha 153) atribui FR-1 ao Épico 2; a AC é a Story 2.6.
- **Conflito:** as ACs da Story 1.7 falam em *"quando o **comando** encerra"* e *"a base de referência com a API respondendo normalmente / a execução termina / reporta 50 lidas, 50 analisadas"*. Executar a base pela linha de comando exige a metade de FR-1 que trata do argumento do CSV — entregue só no Épico 2.
- **Impacto:** o Épico 1 não é verificável de ponta a ponta sem uma story do Épico 2. É a violação de independência que este passo proíbe (Épico N exigindo Épico N+1).
- **Correção recomendada:** partir FR-1 nas duas metades que ele já contém — *aceitar o caminho do CSV como argumento* vai para a Story 1.7 (Épico 1); *escrever o HTML com nome `relatorio-` e imprimir o caminho* permanece na Story 2.6 (Épico 2). É reetiquetagem do mapa de cobertura, não trabalho novo.

**Issue-2 — AC não ratificada bloqueando a Story 2.1.**

- **Onde:** Story 2.1, AC dos pesos, marcada `[ASSUMPTION] — correspondência entre as parcelas nomeadas em risk-signals.md e os códigos do catálogo, a ratificar antes da implementação`.
- **Impacto:** uma AC declarada como suposição pendente não é implementável nem testável. A Story 2.1 alimenta 2.2 → 2.3 → 2.4 e a medição de M-1 na 3.1; um mapeamento de pesos errado desloca o corte de 3 pontos e invalida M-1 sem que nada falhe.
- **Correção recomendada:** ratificar o mapeamento parcela→código contra `risk-signals.md` antes de abrir a Story 2.1, e remover a marca `[ASSUMPTION]` da AC.

**Issue-3 — Contradição no tamanho do catálogo (repetida do Passo 3).**

- Linha 123 declara 5 códigos; a AC da Story 1.1 exige 7. A Story 2.1 atribui peso aos 7 e a Story 2.1 exige teste para `ameaca_explicita` e `dano_continuado`.
- **Impacto:** a Story 1.1 é a primeira do backlog e abre com uma instrução ambígua sobre a estrutura que todas as demais consomem.
- **Correção recomendada:** corrigir a linha 123 para os sete códigos.

**Issue-4 — Ordenação da fila sem AC (repetida do Passo 4).**

- Nenhuma AC exige que a fila seja renderizada em ordem decrescente de `pontos`. Implementação em ordem de leitura do CSV passa em tudo e quebra UJ-2.
- **Correção recomendada:** AC em 2.2 (`agregar` ordena, com regra de desempate) e em 2.3 (o template preserva a ordem recebida).

#### 🟡 Preocupações Menores

**Concern-1 — Épico 3 não entrega FR novo.**
Declara explicitamente *"FRs covered: nenhum novo — este épico mede o que os anteriores construíram"*. Pelo padrão estrito, um épico de medição é marco técnico. **Aceito** porque: (a) o PRD nomeia o avaliador técnico como público real; (b) M-6 é a única métrica que mede o objetivo declarado do projeto (§7.1: *"as cinco acima medem o produto; o produto é o pretexto"*); (c) o épico é o último e nada depende dele. Registrado como desvio consciente, não como defeito.

**Concern-2 — Contrato de estado materializado inteiro na Story 1.1.**
A AC exige que `estado.py` exponha `Pontuacao` e `Agregados` — estruturas cujo primeiro consumidor é a Story 2.1, um épico adiante. Trip direto na regra *"entidades criadas quando primeiro necessárias"*. **Aceito** porque AD-19 e AD-20 exigem um contrato de estado único e tipado, `state-contract.md` já é artefato canônico, e o custo é declarativo (nenhuma lógica antecipada). Registrado por transparência.

**Concern-3 — Duas stories em voz de desenvolvedor.**
Story 1.1 (*"As a desenvolvedor do pipeline"*) e Story 3.3 (*"As a desenvolvedor que vai plugar o roadmap"*). Não são stories de usuário final. A 3.3 é defensável (M-6 mede extensibilidade para quem estende); a 1.1 é uma story de fundação com rótulo honesto. Sem ação recomendada além do registro.

**Concern-4 — AC da Story 1.7 depende de serviço externo.**
*"Given a base de referência com a API respondendo normalmente… Then reporta 50 lidas, 50 analisadas, 0 não analisadas"* não é verificável sem rede e sem crédito, e o resultado depende do modelo. Não colide com AD-12 (que cobre só as etapas não-modelo), mas é a única AC do Épico 1 que não roda numa suíte determinística.
**Sugestão:** marcar como verificação manual de aceitação, distinguindo-a das ACs automatizáveis.

**Concern-5 — Story 2.6 acumula duas responsabilidades.**
Política de escrita do arquivo (nome, colisão, flag de sobrescrita, encerramento com zero análises) e verificação de autocontenção (varredura de referências externas, render offline, anexo de e-mail). São dois eixos de teste distintos numa story só. Dimensionamento ainda aceitável; candidata natural a divisão se a story estourar.

**Concern-6 — "Pronto" da Story 3.1 ambíguo.**
Uma AC fixa o critério de aceitação em precisão ≥ 95% / recall ≥ 65%; outra manda reportar o número como saiu, sem reajustar limiar. A regra de abertura do Épico 3 resolve a tensão a favor da segunda, mas a story não diz se um resultado abaixo do limiar a conclui ou a reprova.
**Sugestão:** declarar explicitamente que a story está pronta quando a medição está registrada, e que um resultado abaixo do limiar abre um item de correção de curso, não bloqueia o épico.

**Concern-7 — NFR-3 atribuído ao épico errado no mapa** (repetido do Passo 3). Resumo de cobertura o coloca no Épico 1; a AC vive na Story 3.2.

### 5.4 Checagens Especiais

| Checagem | Resultado |
|---|---|
| Arquitetura especifica starter template? | **Não** — e os épicos declaram isso explicitamente (linha 80), com a Story 1.1 corretamente definida como criação de estrutura e contrato, não bootstrap |
| Greenfield ou brownfield? | **Híbrido tratado corretamente** — repositório existente (`pyproject.toml`, `baseline.py`, `classificador.py`, `.gitignore`, `.env.example`, `README.md`); pacote `plataforma/` criado do zero dentro dele |
| Ponto de integração com o existente | ✓ Declarado na Story 3.1: a medição usa a saída do próprio pipeline, **nunca** `baseline.py` nem `classificador.py` |
| Story de CI/CD ausente | ✓ **Correto** — a spine adia CI, deploy e provisionamento de forma nominal (§ Deferred), e classifica separadamente o que foi *decidido* (observabilidade = saída do operador) do que foi *adiado* |
| Criação de entidades sob demanda | 🟡 Concern-2 |
| Rastreabilidade a FR mantida | ✓ Toda AC cita o FR, NFR, AD ou métrica que a origina |

### 5.5 Checklist de Conformidade

| Critério | Épico 1 | Épico 2 | Épico 3 |
|---|---|---|---|
| Entrega valor de usuário | ✓ | ✓ | 🟡 (Concern-1) |
| Funciona de forma independente | 🟠 (Issue-1) | ✓ | ✓ |
| Stories bem dimensionadas | ✓ | 🟡 (Concern-5) | ✓ |
| Sem dependência prospectiva | ✓ | ✓ | ✓ |
| Entidades criadas quando necessárias | 🟡 (Concern-2) | ✓ | ✓ |
| Critérios de aceitação claros | ✓ | 🟠 (Issue-2) | 🟡 (Concern-6) |
| Rastreabilidade a FR mantida | ✓ | ✓ | ✓ |

### 5.6 Qualidade das Acceptance Criteria

- **Formato BDD:** 100% das ACs em Given/When/Then. Nenhuma exceção.
- **Testabilidade:** alta. As ACs nomeiam módulo, campo, valor e verificação (*"inspeciona os imports"*, *"casa com o glob `relatorio-*.html`"*, *"o lote residual de tamanho 1 é fundido ao anterior"*). Só uma AC é vaga por dependência externa (Concern-4).
- **Cobertura de erro:** forte e incomum. Caminho de erro coberto em ingestão (coluna faltante, id duplicado, CSV vazio), análise (id faltante, repetido, inventado, resposta fora do schema), lote (retry esgotado), evidência (citação inexistente, curta, vazia) e escrita (arquivo existente, zero análises).
- **Especificidade:** resultados esperados são numéricos ou estruturais, não adjetivos. Nenhum caso de *"o usuário consegue X"*.
- **Lacuna de cobertura de erro:** a linha *"API indisponível ou sem credencial"* da §6 do PRD não tem AC que exija informar quantos lotes haviam concluído (achado A do Passo 3).

---

## Sumário e Recomendações

### Status Geral de Prontidão

## ⚠️ PRONTO COM RESSALVAS

> **Atualizado em 2026-08-07: ✅ PRONTO.** Todos os achados 🟠 foram resolvidos — ver *Adendo — Resolução dos Achados* ao final. O veredito abaixo é o da avaliação original, preservado para leitura.

Os quatro artefatos de planejamento são internamente consistentes, mutuamente rastreáveis e detalhados o bastante para implementar. **Cobertura de FR: 18/18. Cobertura de NFR: 10/10. Invariantes de arquitetura referenciados em AC: 22/22.** Nenhuma violação crítica.

Não é **PRONTO** liso porque quatro itens de severidade média têm consequência funcional se entrarem na implementação como estão, e três deles são corrigíveis em minutos de edição de documento.

### Questões Críticas Exigindo Ação Imediata

Nenhuma questão **crítica** (🔴). As quatro abaixo são maiores (🟠) e devem ser resolvidas **antes** de abrir a story correspondente:

| # | Questão | Bloqueia | Esforço |
|---|---|---|---|
| **Issue-2** | AC de pesos da Story 2.1 marcada `[ASSUMPTION]`, pendente de ratificação contra `risk-signals.md`. Mapeamento errado desloca o corte de 3 pontos e invalida M-1 sem que nada falhe visivelmente. | Story 2.1 (e, por consequência, 2.2→2.4 e a medição M-1 da 3.1) | Decisão + edição |
| **Issue-1** | FR-1 inteiro atribuído ao Épico 2, mas a Story 1.7 do Épico 1 precisa do argumento de CSV da linha de comando para ser executável. Quebra a independência do Épico 1. | Verificação de fim do Épico 1 | Reetiquetagem do mapa |
| **Issue-4** | Nenhuma AC exige que a fila seja ordenada por `pontos` decrescente. Uma implementação em ordem de leitura do CSV passa em todas as ACs e quebra a promessa central de UJ-2. | Stories 2.2 e 2.3 | 2 ACs novas |
| **Issue-3** | `epics.md` declara 5 códigos de sinal na linha 123 e exige 7 na AC da Story 1.1. A Story 1.1 é a primeira do backlog. | Story 1.1 | Correção de 1 linha |

### Próximos Passos Recomendados

1. **Ratificar o mapeamento parcela→código de `risk-signals.md`** e remover a marca `[ASSUMPTION]` da AC de pesos da Story 2.1. É a única decisão de produto pendente; as outras três são edição.
2. **Corrigir a linha 123 do `epics.md`** para os sete códigos do catálogo, alinhando-a com a AC da Story 1.1 e com os pesos da Story 2.1.
3. **Partir FR-1 nas duas metades que ele já contém:** *aceitar o caminho do CSV como argumento* → Story 1.7 (Épico 1); *escrever o HTML `relatorio-*` e imprimir o caminho* → Story 2.6 (Épico 2). Atualizar o `FR Coverage Map`.
4. **Acrescentar AC de ordenação da fila:** em 2.2, `agregar` ordena por `pontos` decrescente com regra de desempate declarada; em 2.3, o template preserva a ordem recebida.
5. **Acrescentar AC à Story 1.7** cobrindo a linha *"API indisponível ou sem credencial"* da §6 do PRD: encerrar com a causa nomeada **informando quantos lotes haviam concluído**.
6. **Corrigir a atribuição de NFR-3** no resumo de cobertura (linha 172): está no Épico 1, é verificado na Story 3.2.
7. **Declarar explicitamente o "pronto" da Story 3.1:** a story conclui quando a medição está registrada; resultado abaixo do limiar abre correção de curso, não reprova o épico.
8. **Opcional, antes da Story 1.7:** marcar a AC dependente de API real como verificação manual de aceitação, separando-a das ACs automatizáveis.

### O Que Está Notavelmente Bem

Registrado porque é raro e porque sustenta o veredito de prontidão:

- **Rastreabilidade completa nos dois sentidos.** Toda AC cita o FR, NFR, AD ou métrica que a origina; todo FR tem AC verificável. A auditoria foi feita contra as ACs reais, não contra o mapa declarado.
- **Honestidade epistêmica carregada até a AC.** O PRD registra que 2 das 3 leituras do produto não são exercidas pela base; FR-18 e AD-14 obrigam a ressalva ao lado do gráfico; a Story 2.4 a torna testável. A limitação atravessa os quatro artefatos sem se diluir.
- **Cobertura de caminho de erro acima do usual.** Ingestão, análise, lote, evidência e escrita têm AC de falha. A §6 do PRD tem 14 linhas e 13 delas têm AC.
- **A defesa contra dependência prospectiva está escrita no artefato.** A AC de conservação da Story 1.6 declara nominalmente que vale sozinha, sem `pontuar`.
- **`[ASSUMPTION]` usado como marca visível, não como texto afirmativo.** NFR-1 e os pesos da Story 2.1 estão marcados. É o motivo pelo qual esta auditoria os encontrou.

### Riscos Registrados, Não Bloqueantes

- **NFR-1 nunca cronometrado** (Q-8). Story 3.2 o resolve; o teto de 2 minutos permanece derivado, não medido.
- **CM-2 em zero constante** é indistinguível de mecanismo morto. A Story 1.4 injeta citação falsa de propósito — a mitigação existe e está declarada como tal.
- **Q-5 (origem da base real) adiada.** Não bloqueia o v1: FR-3 faz uma base de formato desconhecido falhar de forma segura antes de qualquer chamada paga.
- **Sem documento de UX.** Aceitável para um artefato HTML estático de leitura única, com as decisões visuais fixadas em FR-10..18 e AD-10/11/14. Acessibilidade dos SVG e comportamento em base grande ficam sem requisito (Avisos 2 e 3 do Passo 4).

### Nota Final

Esta avaliação identificou **15 achados em 3 categorias** — 0 críticos, 4 maiores, 7 menores e 4 riscos registrados. Nenhum impede a implementação; quatro devem ser resolvidos antes de abrir a story afetada, e três desses são edição de documento.

O planejamento está entre os mais rastreáveis que este tipo de auditoria costuma encontrar: a diferença entre "PRONTO COM RESSALVAS" e "PRONTO" aqui são cerca de vinte minutos de edição mais uma decisão de produto sobre os pesos. Os achados podem ser usados para corrigir os artefatos, ou o time pode escolher prosseguir como está — desde que a Issue-2 seja resolvida antes da Story 2.1, porque é a única cuja consequência é silenciosa.

---

**Avaliação conduzida em:** 2026-08-06
**Avaliador:** Product Manager (workflow `bmad-check-implementation-readiness`)
**Artefatos auditados:** PRD, ARCHITECTURE-SPINE, SPEC + companions, epics.md
**Passos concluídos:** 6 de 6

---

## Adendo — Resolução dos Achados (2026-08-07)

Todos os achados 🟠 e os menores acionáveis foram resolvidos. **Status revisado: ✅ PRONTO.**

### Achado novo, encontrado ao ratificar a Issue-2

A ratificação dos pesos expôs um defeito mais grave que o registrado: **o catálogo de sinais não cobria a parcela que M-1 validou.**

`risk-signals.md` mede que uma única dimensão explica 16 das 19 marcações do gabarito — *a empresa está com dinheiro do cliente* —, distribuída em **seis** categorias. O catálogo tinha código para **duas** (`cobranca_indevida`, `servico_nao_contratado`). Um `pontuar` que só enxerga códigos do catálogo perderia as outras quatro, e o recall cairia muito abaixo do piso de 65% de M-1. Somado a isso: `cobranca_indevida` (3) + `servico_nao_contratado` (3) = 6 faria o modificador `Status = Respondida` (−1) parar de eliminar os falsos positivos, desligando em silêncio o mecanismo que dá precisão de 100%. E `lei_citada` não tinha peso em parcela nenhuma — o valor 2 no `epics.md` era invenção.

**Decisão ratificada (usuário, 2026-08-07):** catálogo de **seis códigos**, com a parcela validada virando código único.

| Código | Peso | Grupo | Situação |
|---|---|---|---|
| `dinheiro_retido` | 3 | — | **Validada** — 16 de 19 marcações do gabarito |
| `ameaca_explicita` | 3 | A, satura | Não exercida (0 de 50) |
| `lei_citada` | 3 | A, satura | Não exercida (0 de 50) |
| `registro_contraditorio` | 2 | — | Não exercida |
| `dano_continuado` | 2 | — | Não sustentada |
| `prazo_estourado` | 1 | — | Fraca |
| `Status` = Respondida | −1 | modificador | **Validada** |

`cobranca_indevida` e `servico_nao_contratado` são absorvidos por `dinheiro_retido`. `ameaca_explicita` e `lei_citada` saturam: juntos valem 3, nunca 6.

**Conferência contra a regra medida** — a pontuação reproduz, nesta base, a regra de precisão 100%:

| Situação | Cálculo | Fila | Confere com |
|---|---|---|---|
| Dinheiro retido, `Status` ≠ Respondida | 3 | entra | Regra adotada, 13 TP |
| Dinheiro retido, `Status` = Respondida | 3 − 1 = 2 | fora | Os 2 FP que a regra base cometia |
| Só prazo estourado | 1 | fora | TechVibe e Moda Certa, fora do gabarito |
| Registro contraditório + prazo estourado | 3 | entra | Consequência aceita; nula nesta base |

### Achados resolvidos

| # | Achado | Resolução | Onde |
|---|---|---|---|
| **Issue-2** | Pesos `[ASSUMPTION]` | Ratificados contra tabela canônica; `[ASSUMPTION]` removido da AC; duas ACs novas de saturação e de modificador | `risk-signals.md`, Story 2.1 |
| **Issue-3** | 5 vs 7 códigos | Catálogo unificado em 6 códigos, com `dinheiro_retido` definido pelas seis categorias | `risk-signals.md`, `SPEC.md`, `prd.md`, Story 1.1 |
| **Issue-1** | FR-1 quebrando independência do Épico 1 | Partido em FR-1a (argumento → Story 1.7) e FR-1b (escrita e nome → Story 2.6); mapa e listas de épico atualizados | `epics.md` |
| **Issue-4** | Fila sem ordenação | AC em 2.2 (ordem por `pontos` desc, desempate por `data` e `id` — ordem total e determinística) e em 2.3 (template preserva, não reordena) | Stories 2.2 e 2.3 |
| **Achado A** | §6 "API indisponível" sem AC | AC nova: causa nomeada **e** quantos lotes haviam concluído | Story 1.7 |
| **Concern-7** | NFR-3 no épico errado | Reatribuído ao Épico 3 / Story 3.2 no resumo de cobertura e nas listas dos épicos | `epics.md` |
| **Concern-6** | "Pronto" da Story 3.1 ambíguo | AC explícita: pronta quando a medição está registrada; resultado abaixo do limiar abre correção de curso | Story 3.1 |
| **Concern-4** | AC dependente de API real | Marcada como verificação manual de aceitação, separada da suíte determinística | Story 1.7 |

### Achados mantidos como aceitos

Concern-1 (Épico 3 sem FR novo), Concern-2 (contrato de estado inteiro na Story 1.1), Concern-3 (duas stories em voz de desenvolvedor) e Concern-5 (Story 2.6 com dois eixos) permanecem registrados como desvios conscientes, com a justificativa já documentada no Passo 5. Os quatro riscos da seção *Riscos Registrados* seguem válidos — NFR-1 não cronometrado, CM-2 possivelmente indistinguível de mecanismo morto, Q-5 adiada, sem documento de UX.

### Artefatos alterados em 2026-08-07

- `specs/spec-plataforma-analise-reclamacoes/risk-signals.md` — catálogo revisado, tabela de pesos canônica, `Status` promovido de candidato a modificador ratificado
- `specs/spec-plataforma-analise-reclamacoes/SPEC.md` — critério de sucesso de CAP-4 deixa de citar "cinco tipos"
- `planning-artifacts/prds/.../prd.md` — exemplo do glossário atualizado
- `planning-artifacts/epics.md` — catálogo, pesos, FR-1a/1b, ordenação da fila, ACs novas em 1.1, 1.7, 2.1, 2.2, 2.3 e 3.1

