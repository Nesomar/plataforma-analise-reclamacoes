---
title: Reconciliação PRD → Architecture Spine
type: review
created: 2026-08-06
input: ../../../prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md
target: ../ARCHITECTURE-SPINE.md
also_read:
  - ../../../../specs/spec-plataforma-analise-reclamacoes/SPEC.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/state-contract.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/risk-signals.md
  - ../.memlog.md
---

# Reconciliação PRD → Spine

## Como ler este documento

A spine é substrato de build: ela fixa invariantes, não repete requisitos. Nenhum achado
aqui é da forma *"o requisito X não está copiado na spine"*. Os achados são de quatro tipos:

- **PORTA FECHADA** — um AD torna um FR/NFR impossível ou caro de cumprir.
- **SEM DONO** — nenhum AD, convenção ou módulo do Structural Seed diz de quem é a responsabilidade; dois desenvolvedores implementam diferente.
- **CONFLITO DE FONTE** — spine e companion vinculante dizem coisas incompatíveis.
- **POSTURA PERDIDA** — qualidade que o PRD sustenta como regra virou prosa sem contraparte executável.

A spine cobre bem a espinha dorsal do fluxo. Os doze ADs são densos, cada um previne
uma falha nomeada, e AD-1/AD-3/AD-5/AD-12 carregam sozinhos a maior parte da postura do
PRD. Os achados abaixo são as bordas: fronteira de entrada, fronteira de saída,
e o caminho triste.

---

## 1. Portas que a spine fecha

### 1.1 `[PORTA FECHADA — alta]` AD-4 deixa o item da fila sem identidade

**Regra:** *"`Pontuacao = {id, pontos, na_fila, motivos}`. O nó `renderizar` lê apenas
`pontuacoes` e `agregados`; ele nunca abre `reclamacoes`."*

`Pontuacao` carrega `id`, pontos, o flag e os motivos. Não carrega `empresa`, `titulo`,
`data` nem `status`. AD-4 proíbe `renderizar` de abrir `reclamacoes`.

O que UJ-2 exige da tela: *"O item do topo diz **cobrança indevida, valor recorrente** e
mostra a frase exata do cliente"*, e Ricardo **encaminha aquele caso para o time de
cobrança**. Encaminhar exige saber de qual reclamação e de qual empresa se trata. Com
AD-4 na letra, a fila renderiza `RA645276696 · 3 pontos · "sigo sendo cobrado"` — id
opaco, sem empresa, sem título, sem data.

A cláusula tem um qualificador (*"para justificar uma classificação"*) que pode ser lido
como permissão para ler `reclamacoes` com fins de exibição. Mas a primeira metade da frase
(*"lê apenas `pontuacoes` e `agregados`"*) é absoluta. **É exatamente aqui que dois
desenvolvedores divergem:** um enriquece a fila dentro de `agregar` e mantém AD-4 intacto;
o outro importa `reclamacoes` no `renderizar` e fura o invariante. Ambos acham que estão
seguindo a spine.

**O que falta:** uma frase dizendo quem enriquece a linha da fila. A leitura que preserva
o invariante é `agregados` carregar a fila já pronta para exibição (id, empresa, título,
data, pontos, motivos), com `agregar` sendo o único que cruza `pontuacoes` com
`reclamacoes`. Sem isso declarado, AD-4 é uma porta fechada sobre FR-11 e FR-12.

### 1.2 `[PORTA FECHADA — alta]` AD-9 converte queda de API em relatório limpo

O PRD §6 abre com a regra que organiza tudo: **falha de infraestrutura encerra sem gerar
relatório; falha de conteúdo é absorvida e contabilizada.** A linha da tabela é explícita:

> *API indisponível ou sem credencial → Encerra com a causa nomeada, **sem gerar
> relatório**, informando quantos lotes haviam concluído.*

A spine implementa o outro lado: AD-9 põe `RetryPolicy` no nó, e o memlog registra que
*"execução que esgota o retry produz uma `Falha` com os ids daquele lote"*. `Falha` é
falha de conteúdo por AD-5 — acumulada, contabilizada, absorvida.

Consequência mecânica com a API fora do ar: os 5 lotes esgotam o retry, produzem 5
`Falha` com 50 ids, AD-6 fecha a conservação (`50 == 0 + 50`), `pontuar`/`agregar`/
`renderizar` executam sobre lista vazia e **o relatório é escrito** — marcado como
degradado por NFR-6, mas escrito. É o cenário que a regra organizadora do PRD existe
para proibir: *"Nunca sai um relatório de aparência limpa sobre uma execução que não foi."*

A convenção de Erro na tabela de Consistency Conventions repete a regra do PRD em prosa
(*"Falha de infraestrutura encerra sem escrever relatório"*), mas **nenhum AD diz onde a
linha é traçada**. Transporte esgotado é infra ou conteúdo? A spine responde as duas
coisas em lugares diferentes.

**O que falta:** um critério de aborto entre o gather e `pontuar`. AD-6 já é o ponto de
inspeção natural — ele roda exatamente ali. Bastaria dizer: se `len(analises) == 0`, ou
se a causa das falhas for de transporte esgotado em todos os lotes, a execução encerra
sem escrever, informando os lotes concluídos. Hoje AD-6 verifica que a soma bate e deixa
passar o zero.

**Corolário:** *"sem credencial"* na mesma linha da tabela é ainda mais grave — sem uma
verificação de presença da chave antes do primeiro `Send`, o modo de falha é 5 lotes
esgotando retry contra um 401. Nada na spine diz que `config.py` ou `main.py` valida a
presença da chave antes de despachar.

### 1.3 `[PORTA FECHADA — média]` A convenção de datas não tem fronteira de saída

**Convenção:** *"Datas: ISO-8601 no estado; `DD/MM/AAAA` só na fronteira de leitura do CSV."*

"Só na fronteira de leitura" fecha a fronteira de escrita. FR-17 exige que o relatório seja
*"legível em português do Brasil, incluindo rótulos, categorias e **números formatados na
convenção local**"*, e FR-14 exige que o relatório informe a data da execução. Seguindo a
convenção na letra, o gestor recebe `2026-03-14` numa fila que ele lê em português, e
`1234.5` onde deveria ler `1.234,5`.

**O que falta:** a convenção precisa de uma segunda metade — a formatação pt-BR acontece
no template (filtro Jinja2), nunca no estado. Isso é coerente com AD-10, que já manda o
texto de produto viver no template; só não foi dito para número e data. Sem isso, um
desenvolvedor formata em `agregacao.py`, outro no template, e um terceiro segue a
convenção e entrega ISO ao leitor.

### 1.4 `[PORTA FECHADA — média]` FR-1 escreve o relatório dentro do repositório

FR-1 manda escrever o HTML **ao lado do CSV de entrada**. O CSV do projeto vive em
`docs/`, dentro do repositório. Logo, por desenho, o artefato de saída nasce na árvore
de trabalho versionada.

DG-2 e DG-3 dizem o oposto para base real: a base não entra no repositório *"em nenhuma
circunstância, nem o relatório gerado a partir dela"*, e o relatório *"herda os dados
pessoais contidos nessas citações e deve ser tratado como documento restrito"*.

A spine não resolve a colisão. O Structural Seed **não lista `.gitignore`**, e nenhuma
convenção define um padrão ignorado para a saída. O comportamento default do fluxo que a
spine descreve é: gerar um documento restrito num diretório rastreado pelo git.

**O que falta:** uma convenção de uma linha — padrão de nome da saída (`*.relatorio.html`
ou `saida/`) coberto pelo `.gitignore`, e `.gitignore` presente no Structural Seed. É a
única contraparte arquitetural que DG-2 e DG-3 poderiam ter, e ela é barata.

---

## 2. Requisitos sem dono claro na spine

Percurso completo. "Coberto" significa que existe AD, convenção ou módulo do Structural
Seed que responde *quem faz isso*.

### 2.1 Requisitos funcionais

| Req | Dono na spine | Veredito |
|---|---|---|
| FR-1 CLI + caminho de saída | `main.py` (CLI); nada define quem **deriva** o nome do arquivo | **SEM DONO (média)** — ver 2.3 |
| FR-2 Relatório ao operador | AD-5 (dois números: eventos e reclamações) | Parcial — *sinais derrubados* sem dono, ver 2.4 |
| FR-3 Rejeição de CSV inválido | `ingestao.py`, explícito no seed | Coberto |
| FR-4 Saída já existe | `main.py` tem a flag; **quando** a checagem roda não é dito | **SEM DONO (alta)** — ver 2.3 |
| FR-5 Sentimento/produto/sinais | `analise.py` + AD-7 | Coberto |
| FR-6 Piso de cinco palavras | **nenhum** | **SEM DONO (alta)** — ver 2.4 |
| FR-7 Derrubada por citação inválida | AD-2 | Coberto (com desvio de granularidade, ver 2.5) |
| FR-8 `não identificado` | `agregacao.py` implícito; a normalização `None → rótulo` não tem lugar | **SEM DONO (média)** — ver 2.6 |
| FR-9 Motivo estrutural | AD-3 (`origem == "atributo"`) | Coberto — dos melhores da spine |
| FR-10 Arquivo único sem rede | AD-11 | Coberto |
| FR-11 Fila primeiro | Template por AD-10; nenhum invariante fixa a ordem | Fraco (baixa) — ordem de template, difícil errar |
| FR-12 Evidência visível, não expansível | AD-3, AD-4 para o **dado**; nada para o **"não expansível"** | Parcial — ver §4 |
| FR-13 Ressalva do ranking | AD-10 explícito ("texto de produto vive no template") | Coberto |
| FR-14 Metadados no relatório | AD-5 | Coberto |
| FR-15 Gráficos embutidos | AD-11 (`<svg>` no template); **a aritmética das barras** não tem dono | Parcial (baixa) — ver 2.7 |
| FR-16 Ressalva jurídica | AD-10 posiciona o texto; nada garante presença | Parcial — ver §4 |
| FR-17 pt-BR e números locais | Convenção de nomeação cobre módulos, não a saída | **SEM DONO (média)** — ver 1.3 |

### 2.2 Requisitos não-funcionais

| Req | Dono na spine | Veredito |
|---|---|---|
| NFR-1 2 minutos | Deferred reconhece Q-8; AD-9 fixa concorrência 1 | Tensão declarada, não lacuna |
| NFR-2 Lote configurável | `config.py` | Coberto |
| NFR-3 Tier gratuito | AD-8 (retry não re-executa lotes bons); **teto de tentativas** ausente de `config.py` | Parcial (média) — ver 2.8 |
| NFR-4 Sem reanálise por desenho | AD-8, AD-9 | Coberto — a distinção desenho/transporte está bem fixada |
| NFR-5 Falha não interrompe | AD-5 | Coberto |
| NFR-6 Marca degradado > 10% | AD-5 define o **denominador**; ninguém define **quem calcula o flag nem onde ele mora** | **SEM DONO (alta)** — ver 2.9 |
| NFR-7 Casamento por id | Convenção de Identificador, explícita nos dois sentidos | Coberto |
| NFR-8 Ids estáveis entre execuções | Convenção de Identificador (vem da origem) | Coberto |
| NFR-9 Sobrevive ao e-mail | AD-11 | Coberto |
| NFR-10 Chave de ambiente | Convenção de Credencial | Coberto |

### 2.3 `[SEM DONO — alta]` Quando a colisão de arquivo de saída é detectada

FR-4 e a linha correspondente da tabela §6 exigem encerrar sem escrever. A spine diz que
`main.py` tem *"CLI: caminho do CSV e flag de sobrescrita"* e que `relatorio.py` produz
`caminho_html`. Nada diz **onde a colisão é testada**.

As duas implementações plausíveis não custam o mesmo:

- Checar em `main.py` antes de `carregar`: aborta em milissegundos, zero chamada paga.
- Checar em `renderizar`: aborta depois de gastar a execução inteira contra o tier gratuito.

A segunda contradiz o espírito de FR-3 (*"antes de qualquer chamada paga"*) e pressiona
NFR-3 sem nenhuma regra dizendo que é errado. Como o próprio nome do arquivo depende da
data da execução e do nome do CSV (FR-1), a derivação do caminho tem que ser possível
antes do grafo rodar — e é essa possibilidade que a spine não afirma.

**Custo de fechar:** uma linha na convenção de Erro ou em AD-5 — *"o caminho de saída é
derivado e verificado em `main.py`, antes de compilar o grafo"*.

### 2.4 `[SEM DONO — alta]` O piso de cinco palavras, e o que conta como "sinal derrubado"

Duas lacunas ligadas, ambas atingindo métrica.

**(a) FR-6 não tem módulo.** *"Todo sinal de risco marcado carrega ao menos uma citação
literal do texto, com no mínimo cinco palavras."* O memlog lista o piso como restrição
herdada e vinculante. A spine não o menciona em nenhum AD. AD-1 garante que o par
`{codigo, citacao}` é indivisível — garante que a citação **existe**, não que ela **basta**.
AD-2 governa a verificação de substring, não o comprimento.

Três lugares onde o piso pode cair, com resultados diferentes:

1. **Só no prompt** — o modelo se autopolicia. M-2 (*100% das citações com no mínimo cinco
   palavras*) passa a ser esperança, não invariante, e AD-12 não consegue testá-lo sem rede.
2. **Em `evidencia.py`** — junto da verificação de substring, determinístico e testável.
   É a leitura que AD-12 sustenta e quase certamente a intenção.
3. **Em `pontuacao.py`** — o sinal existe no estado mas não pontua, e a contagem de FR-2 muda.

O PRD dá a justificativa exata de por que isso não é detalhe: *"String vazia é substring
de qualquer texto: sem piso, a verificação de FR-7 aprova o nada."* O piso é a precondição
de FR-7 funcionar, e é a única regra do PRD marcada como vinculante no memlog que não
virou AD.

**(b) A unidade de "sinal derrubado" é indefinida sob AD-2.** FR-2 manda reportar *"total
de sinais derrubados pela verificação de evidência"*, e CM-2 usa esse número como
contramétrica de fabricação. AD-1 modela `Sinal = {codigo, citacao, valida}` — pares.
AD-2 diz que uma citação ruim derruba **o código inteiro, inclusive os pares que passaram**.

Para um código com 3 pares, 1 inválido, o contador vale:

- **1** — pares reprovados na verificação;
- **3** — pares efetivamente descartados;
- **1** — códigos derrubados.

Três desenvolvedores, três números, todos defensáveis pela leitura da spine. E as duas
linhas distintas da tabela §6 (citação inexistente / citação curta) sugerem que o PRD
quer contar as duas coisas, sem dizer se somam no mesmo número de FR-2. CM-2 é a
contramétrica que o PRD destaca como a que *"disparou exatamente o alerta que foi
desenhada para dar"* — ela merece uma unidade declarada.

**O que falta:** o piso de cinco palavras nomeado em `evidencia.py` (AD-2 ou AD-12), e
uma frase fixando a unidade do contador — código derrubado, não par.

### 2.5 `[CONFLITO DE FONTE — média]` AD-2 aperta FR-7 além da letra

FR-7: *"derruba **o sinal específico** que aquela citação sustentava — não o conjunto de
sinais da reclamação."* AD-2: *"se qualquer `Sinal` de um dado `codigo` falha na
verificação, aquele `codigo` é ausente — **inclusive os pares do mesmo código que
passaram**."*

Não é contradição — o PRD contrasta *sinal* com *reclamação inteira*, e AD-2 fica entre os
dois. É uma decisão deliberada e registrada no memlog, defensável pelo custo assimétrico
do falso positivo. Mas o texto de FR-7 fica falso na letra depois de AD-2, e o número de
FR-2 muda de sentido. Vale um alinhamento no PRD ou uma nota em AD-2 dizendo que ele
substitui a granularidade de FR-7.

### 2.6 `[SEM DONO — média]` O produto genérico de CM-3 não tem lugar nenhum

FR-8 trata o produto **nulo**. CM-3 é a contramétrica que o PRD reescreveu justamente
porque contar só o nulo *"media exatamente o caso que o modelo evita"*: produto nulo é
2% da base, produto genérico (`fatura`, `compra`, `produto`, `serviço`, `pedido`) é 36%,
e o número real é **38%**.

Na spine não há dono para a lista de genéricos nem para a decisão do que fazer com eles:
`agregacao.py` é descrito como *"ranking, distribuição, ordenação da fila"*, e o rótulo
`não identificado` de FR-8/FR-13 não aparece em nenhum AD. Um desenvolvedor entrega um
ranking cujo topo é `fatura` — tecnicamente correto, e exatamente o defeito que CM-3
existe para expor. Outro colapsa genéricos em `não identificado` e o ranking muda de forma.

Relacionado: `Analise.produto` é `str | None`; quem converte `None` no rótulo visível —
`agregacao` ou o template — não está dito. AD-10 (*texto vive no template*) empurra para
o template; a necessidade de FR-13 de mostrar o **total** da linha empurra para `agregacao`.

### 2.7 `[SEM DONO — baixa]` A aritmética do gráfico

AD-11 manda o `<svg>` ser *"escrito no template"*. O memlog chama de *"aritmética de
retângulo"*. Se a escala das barras é calculada em Jinja2, ela é lógica não trivial num
lugar que AD-12 não alcança confortavelmente (`renderizar` é função pura, então o HTML de
saída é testável — mas afirmar sobre coordenadas de SVG num teste é desagradável). Se é
calculada em `agregacao.py`, os agregados passam a carregar geometria de apresentação.
Nenhuma das duas é errada; nenhuma está escolhida. Baixa porque o custo do erro é um
gráfico feio, não um número falso.

### 2.8 `[SEM DONO — média]` O teto de tentativas do retry não é um botão

`config.py` é descrito como *"lote, concorrência, modelo — de env com default"*. AD-9 põe
`RetryPolicy` no nó. O número de tentativas é o parâmetro que multiplica chamadas contra
NFR-3 (tier gratuito) e que decide quando a linha *"se persistir, encerra"* da tabela §6
dispara. Ele não está entre os botões declarados, e a spine já reconhece em Deferred que
NFR-1 nunca foi cronometrado — ou seja, ninguém sabe ainda qual o valor certo. É
exatamente o tipo de coisa que AD-9 chama de *"política do nó"* e deveria estar exposta
ao lado do tamanho de lote.

### 2.9 `[SEM DONO — alta]` O flag de degradado não tem casa

NFR-6 é a regra de honestidade mais concreta do PRD, com limiar numérico: acima de 10%
de reclamações não analisadas, o relatório é marcado como degradado, *"de forma visível
ao leitor"*. AD-5 resolve metade — define que o denominador é reclamações afetadas, não
eventos de falha. A outra metade fica aberta:

- **Quem calcula?** `agregar` ou o template. `agregados: dict` é um dicionário sem tipo no
  contrato de estado, então nada obriga que o flag exista ali.
- **O limiar é configurável?** Não está em `config.py` nem fixado como constante em lugar nenhum.
- **Se o template calcula**, a regra vira `{% if ... > 0.1 %}` dentro de Jinja2 — fora do
  alcance confortável de AD-12 e do espírito de AD-4 (*quem decide carrega a decisão;
  quem renderiza não a reconstrói*). AD-4 fala explicitamente de motivos, não do degradado;
  o princípio é o mesmo e não foi estendido.

Dois desenvolvedores: um põe `agregados["degradado"]` e `agregados["taxa_falha"]`; o outro
faz a divisão no template. O segundo viola o princípio de AD-4 sem violar a letra de AD-4.

---

## 3. Tabela de Comportamento em Falha (§6 do PRD), linha a linha

| # | Linha da tabela | Sustentada por | Veredito |
|---|---|---|---|
| 1 | CSV com schema divergente | `ingestao.py`, seed explícito ("antes de qualquer chamada paga") | **Sustentada** |
| 2 | **CSV vazio** | nada | **DIVERGE — ver 3.1** |
| 3 | Identificador duplicado | Convenção de Identificador + `ingestao.py` | **Sustentada** |
| 4 | Arquivo de saída já existe | `main.py` tem a flag; o momento da checagem não | **AMBÍGUA — ver 2.3** |
| 5 | **API indisponível / sem credencial** | AD-9 diz o contrário na prática | **CONTRADITÓRIA — ver 1.2** |
| 6 | Limite de taxa atingido | AD-9 (`RetryPolicy`) | Sustentada na primeira metade; a segunda (*"se persistir, encerra"*) herda o problema da linha 5, e o teto de tentativas não é botão (2.8) |
| 7 | Resposta malformada ou incompleta | AD-5 + AD-6 | **Sustentada** — das mais bem cobertas |
| 8 | Id repetido ou inexistente | Convenção de Identificador | **Sustentada** |
| 9 | Mais de 10% não analisada | AD-5 (denominador) apenas | **AMBÍGUA — ver 2.9** |
| 10 | Citação inexistente no texto | AD-2 | **Sustentada**, com granularidade alterada (2.5) e unidade de contagem aberta (2.4b) |
| 11 | Citação vazia ou < 5 palavras | nada | **SEM DONO — ver 2.4a** |
| 12 | Nenhuma reclamação atinge o corte | nada | **AMBÍGUA — ver 3.2** |

### 3.1 CSV vazio: o invariante aceita o comportamento proibido

*"Encerra com mensagem clara, sem gerar relatório vazio."*

Um CSV com cabeçalho correto e zero linhas passa em tudo que `ingestao.py` verifica —
schema válido, unicidade trivialmente satisfeita. `carregar` emite zero `Send`. O gather
recebe nada. AD-6 avalia `0 == 0 + 0` e **passa**. `pontuar`, `agregar` e `renderizar`
executam sobre listas vazias e produzem o relatório vazio que a linha proíbe.

O invariante de conservação — que existe justamente para pegar reclamação evaporando —
é satisfeito pelo caso em que nada existiu. Nada na spine diz que base vazia é falha de
infraestrutura. É a mesma lacuna estrutural de 1.2, no outro extremo do pipeline: **a
spine não tem uma regra de "abortar quando o denominador é zero".**

### 3.2 Fila vazia: "declarada como tal" não é o mesmo que vazia

*"Gera o relatório normalmente, com a fila vazia declarada como tal — fila vazia é
informação, não erro."*

O comportamento correto é uma afirmação visível ao leitor (*nenhuma reclamação atingiu o
corte de prioridade nesta execução*), não a ausência de conteúdo. A spine não distingue
os dois. Um desenvolvedor entrega `{% for %}` sobre lista vazia e uma seção em branco;
o gestor abre e não sabe se a fila está vazia ou se o relatório quebrou. Isso interage
diretamente com 3.1: **sem uma regra, "base vazia" e "fila vazia" produzem exatamente a
mesma tela**, e o PRD trata uma como erro fatal e a outra como informação legítima.

**As linhas que dois desenvolvedores implementariam diferente**, em ordem de dano: 5
(relatório limpo sobre execução que não aconteceu), 2 (relatório vazio proibido), 11
(M-2 vira inverificável), 9 (degradado calculado em dois lugares), 4 (tier queimado antes
do aborto), 12 (silêncio confundido com falha).

---

## 4. A postura do PRD: o que virou regra e o que virou prosa

O PRD tem uma postura declarada e coerente: **honestidade sobre limitação, recusa de
esconder degradação do leitor, e o caminho triste como parte do que está sendo avaliado.**
Vale reconhecer o quanto disso a spine capturou antes de dizer o que perdeu.

### O que sobreviveu como regra — e sobreviveu bem

- **AD-5** é a postura convertida em estrutura. *"Prevents: um relatório sobre 5 de 50
  reclamações reportar '1 falha' e ter aparência de execução limpa."* A decisão de `Falha`
  carregar os **ids** em vez de um contador é precisamente a recusa de esconder degradação,
  em forma de tipo. É o melhor AD do documento sob esse critério.
- **AD-3** impede fabricar citação para valor de coluna. Honestidade sobre a **origem** do
  que o leitor vê, como enum no tipo (`origem ∈ {sinal, atributo}`), não como convenção.
- **AD-12** é a postura de portfólio explicitada: *"as três parcelas que a base não
  exercita ... têm caso construído à mão — a suíte é a única coisa que as executa."*
  O memlog é ainda mais claro: *"teste é entregável, não andaime"*. Q-4 sobreviveu inteiro.
- **AD-11** trata FR-10 como invariante e não como intenção, com a justificativa do modo
  de falha silencioso (*"testar com a internet ligada"*).

Essa é uma taxa de sobrevivência alta. O que segue são as bordas.

### 4.1 A honestidade sobre *vazio* não sobreviveu — só a honestidade sobre *falha*

Esta é a perda mais significativa, e ela é sistemática, não pontual.

A spine codifica com rigor a honestidade sobre execução **que falhou**: AD-5, AD-6, NFR-6.
Não codifica nada sobre execução que **funcionou e não significa nada** — e é exatamente
essa a descoberta central da §1 do PRD:

> *"Das três leituras que o produto promete, apenas a fila de prioridade é exercida por
> esta base. As outras duas são estrutura construída e não validada."*

- **Sentimento é constante.** 50 de 50 negativas. FR-15 manda desenhar o gráfico de
  distribuição; ele será uma barra única de 100%. M-5 é declarada **não avaliável**.
- **O ranking é raso.** 18 de 50 caem em `fatura`, `compra`, `produto`, `serviço`.
  *"O ranking ordena palavras, não produtos."*

O relatório produzido pela spine como escrita apresenta essas duas leituras **com a mesma
autoridade visual da fila de prioridade**, que é a única validada. FR-13 cobre um caso
vizinho e menor (*volume ≠ gravidade*) e é o único que virou regra (AD-10). A declaração
de que duas das três leituras são estrutura não validada não tem contraparte alguma.

O produto que a spine descreve é menos honesto que o PRD que a originou — e a diferença
aparece na tela do gestor, não no log do operador. Para uma peça de portfólio cujo público
inclui um avaliador técnico, essa é uma linha de texto no template que vale mais do que
qualquer AD adicional.

### 4.2 FR-12 "visível, não expansível" não é regra

O PRD é explícito: a evidência é *"conteúdo visível e não detalhe expansível"*. É a
tradução direta de UJ-2 — Ricardo lê a frase, concorda, e **age antes de olhar qualquer
outro número da página**. Se a citação está atrás de um clique, o fluxo de UJ-2 não
acontece.

Nada na spine impede `<details><summary>ver evidência</summary>`. Ao contrário: é o que um
desenvolvedor faz naturalmente para caber uma fila de 19 itens numa tela, e ele acha que
está melhorando o relatório. AD-10 governa **onde o texto mora**, não **como ele aparece**.
A postura mais específica do PRD sobre a tela não tem defesa arquitetural.

### 4.3 A ressalva jurídica de FR-16 é uma string sem invariante

AD-10 diz apenas: *"Texto de produto (FR-13, FR-16) vive no template, não em Python."*
Isso resolve editabilidade, não presença. FR-16 existe por uma razão que o PRD explicita:
*"O produto entrega uma fila rotulada como risco jurídico, com citação literal do cliente,
a um gestor que vai agir sobre ela."* É a ressalva ética do produto inteiro, e ela vive
num template, apagável sem quebrar teste nenhum, sem nenhum AD dizendo que ela é obrigatória.

AD-12 torna `renderizar` uma função pura testável sem rede — logo, um teste que afirma a
presença da ressalva no HTML de saída é trivial de escrever. Que ela seja verificável não
significa que alguém foi instruído a verificar.

### 4.4 Onde a postura foi corretamente traduzida e vale registrar

Para não deixar a impressão errada: AD-1, AD-2, AD-3, AD-5, AD-6 e AD-12 são traduções
fiéis e às vezes mais rigorosas do que o PRD pedia. AD-2 escolhe deliberadamente o lado
caro do trade-off (derruba o código inteiro) pela razão declarada no SPEC de que falso
positivo custa mais. AD-12 transforma uma questão resolvida do PRD (Q-4) em invariante de
suíte. A postura sobreviveu no caminho triste da **execução**. Ela evaporou no caminho
triste da **leitura** — o que o gestor vê quando o pipeline funcionou perfeitamente e não
tinha nada para dizer.

---

## 5. Governança de dados: DG-1 a DG-5

| DG | Contraparte arquitetural | Veredito |
|---|---|---|
| DG-1 Só dados sintéticos versionados | nenhuma | Sem contraparte — aceitável, é fato do repositório, não regra de build |
| DG-2 Base real nunca entra no repositório | nenhuma; **FR-1 empurra na direção oposta** | **LACUNA — ver 1.4** |
| DG-3 Relatório de base real é documento restrito | nenhuma | **LACUNA — ver 5.1** |
| DG-4 Chave não versionada, `.env` no `.gitignore` | Convenção de Credencial (*"nunca em código, template, teste ou repositório"*) | Coberto em espírito; `.gitignore` e `.env.example` **ausentes do Structural Seed** |
| DG-5 README declara corpus sintético | nenhuma; README ausente do Structural Seed | **LACUNA — ver 5.2** |

### 5.1 DG-3 pede uma linha no template, e não a tem

*"O relatório gerado reproduz citações literais do texto do cliente. Um relatório produzido
a partir de base real herda os dados pessoais contidos nessas citações e deve ser tratado
como documento restrito."*

O único lugar onde essa regra pode agir é o próprio artefato — o HTML que circula por
e-mail, fora de qualquer controle de acesso (o PRD é explícito: *"o controle de acesso é
o e-mail que carrega o anexo"*). A spine já tem a mecânica pronta: AD-10 põe texto no
template, e FR-16 é precedente exato de uma ressalva obrigatória no relatório. DG-3 não
recebeu o mesmo tratamento, embora seja o mesmo padrão: um aviso que precisa chegar a
quem decide o que fazer com o arquivo.

Isso vale mais do que parece para uma peça de portfólio: o relatório é o único artefato
que o avaliador vê rodando, e DG-3 é o que separa um projeto que pensou sobre dados
pessoais de um que só disse que pensou.

### 5.2 DG-5 e o Structural Seed sem README

DG-5 existe *"para que um avaliador não presuma o contrário"* — o público-alvo é
literalmente o avaliador técnico que a §1 do PRD nomeia como parte do público. O
Structural Seed lista `baseline.py` e `classificador.py` como *"medição, preexistente"*,
mas não lista `README.md`, `.gitignore` nem `.env.example` — os três artefatos que
carregam DG-1, DG-4 e DG-5 e os três que já existem no repositório fora do controle da
spine.

Numa arquitetura cujo `purpose` declarado é *"spine de invariantes para implementação,
mais peça visual para avaliador técnico"* (memlog), o README é entregável, não ruído.

---

## 6. Resumo: o menor conjunto de acréscimos que fecha o essencial

Nenhum destes exige AD novo, com uma exceção. Sete frases fecham quase tudo.

| # | Onde | Acréscimo | Fecha |
|---|---|---|---|
| 1 | AD-6 | Se `len(analises) == 0` após o gather, a execução encerra sem escrever, informando lotes concluídos | 1.2, 3.1 (linhas 2 e 5 da tabela §6) |
| 2 | AD-4 | `agregar` é quem cruza `pontuacoes` com `reclamacoes`; a fila chega em `agregados` pronta para exibição | 1.1 (FR-11, FR-12, UJ-2) |
| 3 | AD-2 ou AD-12 | O piso de cinco palavras vive em `evidencia.py`; o contador de FR-2/CM-2 conta **códigos derrubados** | 2.4 (FR-6, M-2, CM-2, linha 11) |
| 4 | AD-4 ou AD-5 | `agregados` carrega `degradado` e a taxa; o template lê, não calcula. Limiar em `config.py` | 2.9 (NFR-6, linha 9) |
| 5 | Convenções | Datas e números pt-BR são formatados no template. Caminho de saída derivado e verificado em `main.py` antes do grafo. Saída coberta pelo `.gitignore` | 1.3, 1.4, 2.3 (FR-17, FR-4, DG-2) |
| 6 | AD-10 ou AD novo | O relatório declara três coisas obrigatórias e testáveis: a ressalva de FR-16, a ressalva de DG-3, e o estado das leituras não validadas (§1) | 4.1, 4.3, 5.1 |
| 7 | Structural Seed | `README.md`, `.gitignore`, `.env.example` listados | DG-1, DG-4, DG-5 |

---

## Anexo — `[CONFLITO DE FONTE — alta]` O contrato de estado contradiz a spine

Fora do escopo pedido (é PRD→spine), mas é o achado com maior probabilidade de produzir
duas implementações diferentes, e ele bloqueia vários pontos acima. Registrado aqui porque
nenhum outro documento o pegaria.

`state-contract.md` é `companion` da spine e o SPEC declara que os companions são *"o
contrato completo do que construir"*. Ele ainda descreve o modelo que os ADs substituíram:

| `state-contract.md` diz | A spine diz |
|---|---|
| `sinal_b: list[str]` e `evidencia: list[str]` em `Analise` | AD-1: *"`sinal_b: list[str]` e `evidencia: list[str]` **não existem**"* |
| `scores: dict[str, int]` no `Estado` | AD-4: `Pontuacao = {id, pontos, na_fila, motivos}` |
| `Estado` sem `falhas` | AD-5: `Falha` acumulada com redutor `add` |
| Nenhum `Sinal`, `Motivo` ou `Pontuacao` | `estado.py` no seed: *"Reclamacao · Sinal · Analise · Falha · Motivo · Pontuacao · Estado"* |

O memlog registra as substituições como decisões tomadas (*"scores dict de inteiros
substituído por pontuacoes list de Pontuacao"*), então a spine está certa e o companion
está velho. Mas um desenvolvedor instruído a seguir o contrato canônico encontra dois
`Analise` incompatíveis e nenhuma indicação de qual vence — e o próprio contrato se
declara *"a única parte do v1 que não é aditiva"*.

O memlog também registra que `architecture-diagrams.md` ficou desatualizado por AD-8
(o grafo deixou de ser linear e ganhou fan-out), com nota *"corrigir no fechamento"*.
Ambos continuam abertos.
