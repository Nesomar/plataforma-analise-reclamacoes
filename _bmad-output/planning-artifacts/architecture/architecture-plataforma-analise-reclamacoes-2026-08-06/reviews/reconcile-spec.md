# Reconciliação SPEC ↔ ARCHITECTURE-SPINE

**Alvo:** `../ARCHITECTURE-SPINE.md`
**Insumos:** `SPEC.md`, `state-contract.md`, `risk-signals.md`, `architecture-diagrams.md`, `roadmap.md` (todos em `_bmad-output/specs/spec-plataforma-analise-reclamacoes/`), com o `prd.md` lido como referência para os FR/NFR/M/CM/Q que a spine cita.
**Data:** 2026-08-06
**Escopo:** verificar se as 9 capacidades têm lugar e governança, se as restrições sobrevivem como regra, se os não-objetivos continuam fechados, se a afirmação de aditividade do roadmap se sustenta, e se o catálogo de sinais tem dono.

---

## 0. As duas mudanças deliberadas

Duas divergências entre a spine e os companions estão registradas como decisão, não como erro, e os companions já estão marcados para atualização:

- `state-contract.md` trazia `sinal_b: list[str]` + `evidencia: list[str]`; AD-1 substitui por `Sinal = {codigo, citacao, valida}`.
- `architecture-diagrams.md` desenha um grafo linear de cinco nós; AD-8 introduz fan-out por lote via `Send`.

Nenhuma das duas é reportada aqui como achado. O que **é** reportado é o resíduo: o que mais, dentro dos companions, deixa de ser verdadeiro por causa delas e ainda não está anotado.

### 0.1 Resíduo de AD-1 — `sinal_a` ficou órfão `[ALTO]`

AD-1 nomeia explicitamente os dois campos que deixam de existir: `sinal_b` e `evidencia`. **Não diz nada sobre `sinal_a: bool`.** Lido ao pé da letra, `sinal_a` permanece no `Analise` como booleano solto.

Isso é exatamente o buraco que AD-1 existe para tapar, deixado aberto no campo vizinho. `sinal_a` é a intenção declarada de acionar a empresa — a classificação de risco de maior gravidade do catálogo, com peso 3 em `risk-signals.md`. Como booleano, ele é uma classificação de risco **sem citação associada**, o que colide de frente com:

- a restrição *"Sem citação literal não há classificação de risco"*;
- o critério de sucesso de CAP-4 (*"Nenhum sinal é marcado sem citação associada"*);
- FR-6 (*"Todo sinal de risco marcado carrega ao menos uma citação"*);
- a própria `Rule` de AD-1 (*"Nenhum caminho de código produz um código de sinal sem a citação que o sustenta"*) — que só é verdadeira se `sinal_a` não for um caminho de código.

E é o pior campo possível para deixar de fora, porque `sinal_a` é a parcela que a base do projeto **não exercita** (0 de 50 em `risk-signals.md`): nenhuma execução real vai revelar o problema, só a base real vai.

**Correção:** AD-1 deve dizer que `sinal_a` também deixa de existir e vira um `Sinal` com código próprio (`ameaca_explicita`) dentro da mesma lista, sujeito à mesma verificação de AD-2. Se houver razão para mantê-lo separado, a razão precisa estar escrita e a exceção à regra da citação precisa ser explícita.

### 0.2 Resíduo de AD-1 — o terceiro diagrama também caduca `[MÉDIO]`

O anotado é o primeiro diagrama de `architecture-diagrams.md`. Mas o **terceiro** ("Fluxo da evidência") também deixa de descrever o sistema: ele mostra `citação inválida → sinal derrubado para falso`, um par por vez. AD-2 amplia o raio para o código inteiro, inclusive os pares do mesmo código que passaram na verificação. O diagrama precisa mostrar o raio novo, ou registra uma regra mais branda do que a que vale.

O segundo diagrama ("Lote e escalada") **continua válido** sob AD-8 e não deve ser mexido — o merge por `id` que ele estabelece é precisamente o que o fan-out preserva. Vale registrar isso na anotação para ninguém corrigir demais.

### 0.3 Resíduo de AD-8 — o diagrama de dependência da própria spine se contradiz `[ALTO]`

`architecture-diagrams.md` atribui o fatiamento em lotes ao nó `analisar_lotes` (*"Fatia em lotes, saída estruturada, casa resposta por `id`"*). AD-8 move essa responsabilidade para `carregar`, que passa a emitir um `Send` por lote.

Consequência não anotada: **`ingestao.py` passa a consumir `config.tamanho_lote`**. E o diagrama "Direção de dependência" da própria spine desenha apenas `config -.-> analise` e `config -.-> grafo`. O `carregar` que fatia não tem acesso desenhado à configuração que diz de quanto é a fatia.

Duas saídas, e a spine precisa escolher uma:

- **(a)** `config -.-> ingestao` entra no diagrama, e a linha de `ingestao.py` no Structural Seed passa a mencionar o fatiamento;
- **(b)** o fatiamento fica em `grafo.py`, que já lê `config` e já é quem constrói os `Send` — provavelmente mais limpo, porque mantém `ingestao.py` como leitor puro do CSV e concentra a topologia num lugar só.

Seja qual for, o Structural Seed hoje descreve `ingestao.py` como *"valida schema e unicidade antes de qualquer chamada paga"* e `grafo.py` como *"StateGraph · Send · RetryPolicy · compile"*, e nenhum dos dois diz quem corta o lote. A responsabilidade está sem dono.

### 0.4 Resíduo de AD-2 — o raio de derrubada contradiz FR-7 `[MÉDIO]`

FR-7 é explícito: *"derruba **o sinal específico** que aquela citação sustentava — não o conjunto de sinais da reclamação."*
AD-2 é explícito na direção oposta: *"aquele `codigo` é ausente para efeito de pontuação — **inclusive os pares do mesmo código que passaram**."*

As duas são reconciliáveis — AD-2 fica entre "o par" e "a reclamação inteira" —, mas nenhuma das duas redações admite a outra, e o texto de FR-7 (*"o sinal específico"*) é mais estreito do que AD-2 implementa. Um implementador que ler o PRD e não a spine escreve o comportamento errado.

Efeito colateral que precisa ser decidido junto: **CM-2 conta o quê?** Os pares que falharam na verificação de substring, ou também os pares colaterais derrubados por AD-2? São números diferentes e a contramétrica muda de significado conforme a escolha. FR-2 reporta esse número ao operador.

---

## 1. As nove capacidades — lugar e governança

A tabela `Capability → Architecture Map` cobre CAP-1 a CAP-9 sem lacuna: toda capacidade tem módulo e ao menos uma coluna de governança. Nesse nível formal, a resposta é **sim, todas têm lugar**. Os problemas estão no detalhe.

| Capability | Lugar | Governança | Veredito |
|---|---|---|---|
| CAP-1 Ingestão | `ingestao.py` | convenções | governada por convenção, não por AD — ver 1.1 |
| CAP-2 Sentimento | `analise.py` | AD-7 | critério de sucesso universal vs. AD-6 — ver 1.2 |
| CAP-3 Produto | `analise.py` | AD-7 | **restrição central ausente** — ver 2.2 |
| CAP-4 Sinais | `analise.py` | AD-1, AD-7 | catálogo e glossário sem dono — ver 5 |
| CAP-5 Evidência | `evidencia.py` | AD-1, AD-2, AD-12 | sólida; piso de 5 palavras sem dono — ver 1.3 |
| CAP-6 Priorização | `pontuacao.py` | AD-3, AD-4, AD-12 | critério de sucesso sem caminho reproduzível — ver 1.4 |
| CAP-7 Agregação | `agregacao.py` | AD-5, AD-6, AD-12 | ok |
| CAP-8 Relatório | `relatorio.py` + template | AD-10, AD-11, AD-4 | **AD-4 bloqueia FR-14/NFR-6** — ver 1.5 |
| CAP-9 Orquestração | `grafo.py` | AD-7, AD-8, AD-9, paradigma | forte; M-6 sem invariante — ver 1.6 |

### 1.1 CAP-1 — "antes de qualquer chamada paga" é comentário, não invariante `[BAIXO]`

O critério de sucesso de CAP-1 tem duas metades. A segunda (*mesmos identificadores em duas execuções*) está coberta pela convenção de identificador e por NFR-8. A primeira — *"interrompem a execução **antes de qualquer chamada paga**"* — aparece apenas como comentário na linha de `ingestao.py` do Structural Seed.

Não é grave hoje, porque a topologia protege: `carregar` precede os `Send`. Mas é uma propriedade de ordem, e a spine acabou de introduzir fan-out — a ordem virou a coisa que mudou. Uma linha na tabela de convenções ("validação de schema e unicidade completa antes da emissão do primeiro `Send`") custa nada e amarra o que a topologia hoje garante por acidente feliz.

### 1.2 CAP-2 e CAP-3 — critérios universais contra a admissão de falha parcial `[MÉDIO]`

CAP-2 diz *"**Cada** reclamação recebe exatamente um valor"*. CAP-3 diz que a reclamação sem produto *"não é silenciosamente descartada"*.

AD-5 e AD-6 legitimam, corretamente e em linha com NFR-5, um subconjunto de reclamações que termina a execução **sem** `Analise` — logo sem sentimento e sem produto. A identidade de AD-6 (`len(reclamacoes) == len(analises) + sum(len(f["ids"]))`) diz isso com todas as letras.

Não é contradição de fato — é redação. Os critérios de CAP-2 e CAP-3 são quantificados sobre a base inteira quando deveriam ser quantificados sobre o conjunto analisado. A spine está certa e o SPEC está impreciso; a correção é no SPEC, e é de uma linha ("cada reclamação **analisada**"). Registro aqui porque, sem a correção, uma leitura literal de CAP-2 reprova qualquer execução com uma única falha — e NFR-6 tolera até 10%.

Nota: AD-6 garante que o descarte **nunca é silencioso**, que é o que CAP-3 realmente pede. A capacidade está atendida no espírito.

### 1.3 CAP-5 — o piso de cinco palavras não tem módulo `[MÉDIO]`

FR-6 exige citação com **no mínimo cinco palavras**, e a justificativa é explícita: *"String vazia é substring de qualquer texto: sem piso, a verificação de FR-7 aprova o nada."* M-2 mede isso.

A spine não atribui esse piso a lugar nenhum. `evidencia.py` é descrito como *"verificação de citação — determinística, sem rede"*, o que sugere que ele faz a verificação de substring de FR-7; AD-1 fala em nunca produzir código sem citação, mas nada sobre o comprimento dela.

Pior: **o piso e AD-2 têm semânticas incompatíveis se caírem no mesmo módulo.** FR-6 diz que a citação curta faz o sinal *não ser registrado*; AD-2 diz que a citação inválida *derruba o código inteiro*. Se o piso for aplicado dentro da verificação, uma citação curta passa a matar os pares irmãos do mesmo código — comportamento que FR-6 não pede e que come recall de graça. Se for aplicado na composição da resposta em `analise.py`, o par simplesmente não nasce e AD-2 nunca o vê.

**Decidir e escrever:** o piso pertence a `analise.py` (filtro de registro, antes de o delta existir) e AD-2 só governa a falha de substring. Sem isso, dois implementadores escrevem dois sistemas.

### 1.4 CAP-6 — o critério de sucesso não tem caminho reproduzível na spine `[ALTO]`

Este é o achado mais consequente do conjunto, porque toca a única capacidade que a base do projeto realmente exercita.

O critério de CAP-6 é precisão ≥ 95% com recall ≥ 65% contra `docs/gabarito.csv`. `risk-signals.md` e M-1 registram que **exatamente uma** regra atende: *"Categoria de dinheiro retido + `Status` ≠ Respondida"*, com 100% / 68,4%. A regra da categoria consome o **título canônico** do CSV (a tabela de `risk-signals.md` é explícita: *"Categoria (determinística, vê o título)"*).

Agora olhe o que a spine dá a `pontuacao.py`: *"parcelas, modificador de `Status`, motivos"*. E o que `analise.py` produz: `Sinal` com códigos do catálogo (`cobranca_indevida`, `prazo_estourado`, `registro_contraditorio`, `servico_nao_contratado`, `lei_citada`).

**"Dinheiro do cliente retido" não é um código do catálogo.** É uma categoria derivada do título, de um segundo vocabulário — o das parcelas de peso em `risk-signals.md`. A spine tem dois vocabulários circulando e **nenhum AD que mapeie um no outro**:

| Vocabulário | Onde vive | Itens |
|---|---|---|
| Códigos do catálogo (sinal B) | saída do modelo, `Sinal.codigo` | `cobranca_indevida`, `prazo_estourado`, `registro_contraditorio`, `servico_nao_contratado`, `lei_citada` |
| Parcelas do score | `risk-signals.md`, pesos 3/2/2/1 e modificador −1 | dinheiro retido, ameaça explícita, dano continuado, registro contraditório, prazo estourado, `Status` = Respondida |

Os dois se sobrepõem parcialmente (`prazo_estourado` e `registro_contraditorio` aparecem nos dois) e divergem no item que **importa**: a única parcela validada, peso 3, a que sozinha explica o gabarito.

Consequências concretas:

- Se `pontuacao.py` consumir apenas `Sinal.codigo`, o número medido (100% / 68,4%) **não transfere** — ele foi obtido por uma regra que lê o título, e nada na spine dá ao score um caminho até a categoria do título.
- Se `pontuacao.py` consumir a categoria do título, então existe uma classificação determinística de categoria em algum lugar do sistema e a spine não a nomeia — não há módulo, não há AD, e AD-3 diz apenas que `origem == "atributo"` *"vem de coluna do CSV"*, sem dizer que existe uma derivação categoria←título entre a coluna e o motivo.
- Os **pesos e o corte** (3/2/2/1, −1, corte binário em ≥ 3) não aparecem em lugar nenhum da spine. `config.py` é *"lote, concorrência, modelo"*. Por omissão eles ficam codificados em `pontuacao.py`, o que é aceitável — mas então a spine deveria dizer que `risk-signals.md` é a fonte única desses números, sob pena de a calibração medida em 2026-08-06 virar irreproduzível na primeira divergência.

**Correção mínima:** um AD ou uma linha de convenção que declare (i) onde vive a derivação categoria←título, (ii) o mapeamento código-do-catálogo → parcela, e (iii) que pesos e corte vêm de `risk-signals.md`.

Nota positiva no mesmo tema: **nenhum AD torna o critério inatingível.** AD-2 é a candidata natural — derrubar o código inteiro custa recall, e o piso de recall é 65% contra 68,4% medidos, folga de 3,4 pontos. Mas CM-2 registra **zero derrubadas em 50 reclamações**: o raio de AD-2 é vazio nesta base e não move o número medido. Vale registrar que essa folga é uma medição, não uma garantia — AD-2 nunca foi exercida contra dado real, só pelo caso sintético de AD-12.

### 1.5 CAP-8 — AD-4 bloqueia o relatório de cumprir FR-14 e NFR-6 `[ALTO]`

AD-4 é categórica: *"O nó `renderizar` lê apenas `pontuacoes` e `agregados`."*

AD-5 é igualmente categórica na direção oposta: `Falha` tem **Binds: `analise`, `agregacao`, `relatorio`**, e sua justificativa é literalmente sobre o relatório (*"um relatório sobre 5 de 50 reclamações reportar '1 falha' e ter aparência de execução limpa"*).

E os requisitos concordam com AD-5:

- **FR-14** — o relatório informa o total analisado e o **total não analisado por falha**, explicitamente porque *"hoje esse número existe apenas no terminal do operador, que o leitor nunca vê"*;
- **NFR-6** — acima de 10% de não analisadas, o relatório é marcado como **degradado no próprio arquivo**;
- **AD-10** cita FR-9 a FR-17 e menciona *"condicional de degradado"* no template.

Sob a letra de AD-4, `renderizar` não tem como saber que a execução foi degradada. Duas leituras possíveis e a spine não escolhe:

- **(a)** `agregados` carrega as contagens de falha, e AD-4 está correta — mas então `agregacao.py` ganha uma responsabilidade que não está escrita em lugar nenhum (o Structural Seed diz *"ranking, distribuição, ordenação da fila"*), e o `Bind` de AD-5 em `relatorio` é indireto;
- **(b)** `renderizar` lê `falhas` diretamente, e a regra de AD-4 precisa ser reescrita como *"lê `pontuacoes`, `agregados` e `falhas`"*.

A intenção de AD-4 — impedir que o renderizador reconstrua a **regra de pontuação** — é boa e não depende de proibir a leitura de `falhas`. A regra está mais larga do que o `Prevents` que a justifica. **(a)** é a saída mais limpa: `agregacao.py` já é o nó que produz números para o leitor, e o denominador de NFR-6 é um agregado por natureza.

Achado menor no mesmo nó: **a data da execução (FR-14, FR-1) não existe no estado.** `Estado` tem `reclamacoes`, `analises`, `scores`, `agregados`, `caminho_html`; o Structural Seed lista `Reclamacao · Sinal · Analise · Falha · Motivo · Pontuacao · Estado`. Não há `data_execucao`. Ela também é a peça que falta para a reclassificação por tempo de espera do roadmap (ver 4.5).

Resto de CAP-8 está bem coberto: AD-11 é a tradução mais forte possível da restrição de autocontenção, e AD-10 pega o `autoescape` do Jinja2 — que é exatamente o erro que um pipeline de texto livre de consumidor produz.

Lacuna residual: **FR-17** (formatação numérica na convenção pt-BR) não tem dono. AD-10 põe texto no template; formatação de número é filtro do `Environment`, que AD-10 governa. Uma menção resolve.

### 1.6 CAP-9 — forte, mas M-6 não tem invariante `[MÉDIO]`

CAP-9 é a capacidade que carrega o propósito declarado do projeto, e a spine a serve bem: o paradigma de pipes-and-filters sobre deltas, mais AD-7, AD-8 e AD-9, entrega "adicionar etapa sem mexer nas anteriores" por construção.

O que falta é o **teste**. M-6 é, nas palavras do próprio PRD, *"a única métrica que mede o objetivo declarado do projeto"*, e é verificável (*"acrescentar um nó ao grafo e observar que o diff não toca os nós anteriores"*). Nenhum AD a menciona; AD-12 governa a suíte e lista verificar/pontuar/agregar/renderizar, não a extensibilidade do grafo. A propriedade que justifica o projeto inteiro é a única sem asserção.

---

## 2. As restrições, uma a uma

| # | Restrição | Sobrevive? | Onde |
|---|---|---|---|
| 1 | Modelo extrai; código julga | **sim, reforçada** | AD-7 + AD-12 |
| 2 | Produto do texto, nunca da empresa | **NÃO** | ausente — 2.2 |
| 3 | Sem citação literal não há risco | sim, reforçada | AD-1, AD-2 (mas ver 0.1) |
| 4 | Falso positivo custa mais | parcial | consequência de AD-2, não regra |
| 5 | Lote é a unidade; chamada individual proibida | **parcial — a proibição some** | 2.5 |
| 6 | Casamento por `id`, nunca por posição | sim, ampliada | convenções |
| 7 | Arquivo único autocontido | sim, reforçada | AD-11 |
| 8 | LangGraph obrigatório | sim, reforçada | 2.8 |
| 9 | Gemini + Python | sim | Stack |
| 10 | Relatório é só representação visual | **parcial — porta aberta** | 3.2 |
| 11 | Heurística, não parecer jurídico | sim | AD-10 via FR-16 |

### 2.1 "O modelo extrai; código determinístico julga" — sobrevive reforçada

AD-7 é a melhor tradução possível desta restrição, porque converte uma afirmação de prosa numa regra **mecanicamente verificável**: *"Nenhum outro módulo importa `google.genai`, direta ou transitivamente."* Isso é um teste de uma linha, não um julgamento arquitetural. AD-12 fecha pelo outro lado: se julgar dependesse de extrair, a suíte precisaria de credencial.

Uma peça da restrição, porém, escorregou na redação: o SPEC nomeia *"score, contagem, ranking, ordenação **e aritmética de prazo**"*. `architecture-diagrams.md` atribuía a `pontuar` *"as três parcelas **e a aritmética de prazo**"*. O Structural Seed da spine descreve `pontuacao.py` como *"parcelas, modificador de `Status`, motivos"* — a aritmética de prazo sumiu da descrição. Os campos `prazo_prometido_dias` e `data_evento` do `Analise` continuam existindo e continuam sendo entrada de uma parcela (peso 1, reconhecidamente fraca). `[BAIXO]` — é redação, mas é a parcela que, sendo fraca e não exercida, é a mais provável de ser esquecida na implementação.

### 2.2 "Produto é inferido do texto, nunca da empresa" — **desapareceu** `[ALTO]`

Esta restrição não aparece na spine. Nem como AD, nem como linha na tabela de convenções, nem como comentário no Structural Seed. CAP-3 é mapeada para `analise.py` governada apenas por AD-7 — que fala sobre importar o SDK e nada sobre de qual campo o produto é inferido.

É a restrição com a justificativa mais concreta de todo o SPEC, e a justificativa é de **corretude do resultado**, não de estilo:

> *"Na base do projeto empresa e reclamação estão pareadas ao acaso — supermercado com reclamação de voo cancelado, loja de moda com reclamação de ração. Derivar produto do nome da empresa produz ranking falso."*

O PRD repete o alerta em §1. E o sistema **facilita o erro**: `Reclamacao` carrega `empresa`, o lote inteiro é serializado para o prompt em `analise.py`, e incluir `empresa` no payload é a coisa mais natural do mundo para quem está montando o prompt — parece contexto útil. O resultado é um ranking de produtos plausível e errado, sobre uma base onde a correlação empresa↔produto é ruído puro por construção. Ninguém detecta olhando a saída.

Agrava: CAP-7 e as leituras de marca/ranking já são, segundo o próprio PRD, *"estrutura construída e não validada"* nesta base. Um ranking envenenado pela empresa cai justamente na dimensão que nenhuma métrica cobre.

**Correção:** AD explícito. Sugestão de redação — *"o payload enviado ao modelo para extração de produto contém `titulo` e `texto`; `empresa` não é enviada. `agregacao` não deriva produto de `empresa` em nenhuma circunstância."* Custa uma regra e fecha um erro silencioso e irrecuperável.

### 2.3 e 2.4 Citação obrigatória e assimetria de custo

A restrição da citação sobrevive e melhora: AD-1 torna a associação estrutural (impossível ter código sem citação) em vez de convencional, e AD-2 endurece o raio. As duas ressalvas já estão em 0.1 (`sinal_a` órfão) e 1.3 (piso de cinco palavras sem dono).

A assimetria de custo (*"falso positivo custa mais que falso negativo"*) sobrevive apenas como **consequência** de AD-2 e do critério de M-1, nunca como regra declarada. Não é grave — a assimetria é critério de aceitação, e critério de aceitação vive no PRD. Mas vale notar que, se alguém futuramente afrouxar AD-2 para recuperar recall, nada na spine registra por que AD-2 era severa de propósito. Uma frase no `Prevents` de AD-2 resolveria.

### 2.5 "Chamada individual proibida" e "base inteira num único prompt" — o mesmo buraco `[ALTO]`

O SPEC proíbe duas coisas nas duas pontas da mesma escala:

- restrição: *"O lote é a unidade de chamada. **Chamada individual por reclamação é proibida.**"*
- não-objetivo: *"**Enviar a base inteira num único prompt.**"*

A spine tem `config.py` — *"lote, concorrência, modelo — de env com default"* — e NFR-2 exige que o tamanho de lote seja **configurável sem alteração de código**. Em nenhum lugar há piso ou teto.

Com `tamanho_lote = 1`, AD-8 emite um `Send` por reclamação e o sistema faz exatamente a chamada individual proibida — sem violar nenhum AD, sem quebrar nenhuma asserção, sem sinal de erro. Com `tamanho_lote = 50`, manda a base inteira num prompt — o não-objetivo, também limpo. As duas proibições mais explícitas do SPEC viraram uma variável de ambiente sem validação.

Não é hipotético: a Assumption do SPEC diz que *"tamanho de lote é ponto de partida arbitrário, **a calibrar**"*, ou seja, alguém **vai** mexer nesse número, provavelmente durante depuração, provavelmente para 1 (é o valor que se usa para isolar uma resposta malformada). O caminho para a violação é o caminho normal de trabalho.

**Correção:** validação de faixa em `config.py` com as duas pontas nomeadas pela restrição que cada uma protege. É uma linha de `if` e uma linha de AD.

Observação relacionada: **AD-9 fixa concorrência com padrão 1 e chama isso de botão exposto** — bom, e é a proteção certa para NFR-3 (tier gratuito). Ali a spine se lembrou de dar um default seguro a um parâmetro perigoso. O mesmo cuidado não foi aplicado ao lote.

O outro braço da restrição — *"desmonte na escalada"* — está corretamente diferido (é a cascata do v2) e a spine registra que o fan-out de AD-8 é a estrutura sobre a qual isso entra. Ver 4.2 para a ressalva.

### 2.6 e 2.7 Casamento por `id` e autocontenção

Ambas sobrevivem **ampliadas**. A convenção de identificador acrescenta a detecção do `id` que o modelo devolveu sem ter sido pedido (NFR-7), que o SPEC não pedia explicitamente. AD-11 traduz a autocontenção em algo verificável byte a byte e mata o modo de falha real — *"alguém adicionar uma fonte remota e testar com a internet ligada"*.

### 2.8 "LangGraph obrigatório mesmo com fluxo linear" — sobrevive, e por um bom motivo

Esta restrição era a mais frágil do SPEC, porque a justificativa é pedagógica (*"é o objeto de estudo, não o meio"*) e justificativa pedagógica não resiste a um refactor. `risk-signals.md` inclusive registra a conclusão desconfortável de que *"nesta base, o pipeline de agentes é infraestrutura cara para um resultado que um `in` entrega"* — ou seja, existe argumento técnico documentado para remover o LangGraph.

A spine resolve isso **estruturalmente, não por decreto**: AD-8 usa `Send` para fan-out e AD-9 usa `RetryPolicy` no `add_node`. As duas são primitivas do framework sem equivalente trivial em composição de funções. O LangGraph deixou de ser decoração sobre um pipeline linear e passou a carregar peso — paralelismo por lote, redutores de acumulação, política de repetição declarativa. Remover o framework agora custa reimplementar três coisas, o que é exatamente a defesa que a restrição precisava.

Ressalva de forma: o `paradigm` do frontmatter diz *"pipes-and-filters sobre estado compartilhado explícito"*, uma descrição que, isolada, sugere que qualquer composição serve. AD-8 e AD-9 desmentem, mas quem lê só o cabeçalho fica com a impressão errada. `[BAIXO]`

---

## 3. Os não-objetivos

| Não-objetivo | Fechado? |
|---|---|
| Interface web, upload, job assíncrono, polling | sim — CLI em `main.py`, envelope operacional declarado ausente |
| Cache, cascata, guard-rails, loop de crítica, checkpoint | sim — `Deferred` explícito |
| Níveis de criticidade na fila | sim — `Pontuacao.na_fila` é booleano |
| Normalizar/limpar CSV com LLM | sim, e com força — 3.1 |
| Agentes por dimensão ou especialidade | sim — 3.3 |
| Base inteira num único prompt | **NÃO** — ver 2.5 |
| Formatos além do schema fixo | sim — FR-3 em `ingestao.py` |
| Relatório como ferramenta de decisão | **porta entreaberta** — 3.2 |

### 3.1 Fechamento acidentalmente excelente

AD-7 fecha *"normalizar ou limpar o CSV usando LLM"* sem nunca mencioná-lo: se só `analise.py` importa o SDK, `ingestao.py` não tem como chamar o modelo, ponto. É o tipo de regra que fecha um não-objetivo como efeito colateral de uma boa fronteira. Vale registrar como acerto.

Da mesma forma, `Pontuacao = {id, pontos, na_fila, motivos}` mantém o corte binário do v1 (`na_fila` booleano) **e** carrega `pontos`, que é a matéria-prima dos níveis do v2. Fecha o não-objetivo sem fechar a porta do roadmap.

### 3.2 "Relatório como ferramenta de decisão" — AD-11 não fecha JavaScript inline `[MÉDIO]`

AD-11 proíbe `<script src>`, `<link href>` externo, biblioteca de plotagem e fonte remota. Todos externos. **`<script>` inline satisfaz AD-11 inteiro** — todo byte que o navegador renderiza já estava no arquivo.

E JavaScript inline é o caminho de menor resistência para exatamente o que quatro documentos proíbem:

- SPEC, restrição: *"O relatório é apenas representação visual. Sem drill-down, sem série temporal, sem ferramenta de decisão elaborada."*
- SPEC, não-objetivo e `roadmap.md` §"Fora de todas as versões": *"Relatório como ferramenta de decisão elaborada."*
- PRD §8: *"Ele não filtra, não ordena, não exporta."*
- FR-12: a evidência é *"conteúdo visível e **não como detalhe expansível**"*.

Ordenar a tabela de ranking por clique, colapsar as citações longas num `<details>`, filtrar a fila por produto — cada uma é vinte linhas, cada uma passa em AD-11, e a última viola FR-12 diretamente. A tentação é real porque o público inclui um avaliador técnico e interatividade parece qualidade.

**Correção:** uma cláusula em AD-11 ou AD-10 — *"o relatório é estático: nenhum `<script>`, inline ou externo; nenhum `<details>` sobre conteúdo que FR-12 exige visível"*. Isso também simplifica a verificação de AD-11: "o arquivo não contém a substring `<script`" é um teste trivial.

### 3.3 Divisão de agentes — fechado pela redação, por pouco

O não-objetivo proíbe *"agentes divididos por dimensão de análise ou por especialidade de domínio — a divisão é por etapa do fluxo"*. AD-8 introduz fan-out, e fan-out é o mecanismo natural para fazer justamente isso (um `Send` para sentimento, um para produto, um para risco). A regra de AD-8 diz *"`carregar` emite um `Send` **por lote**"*, o que fecha a porta — mas fecha por escolha de palavra, não por invariante. Como o conjunto de nós no Structural Seed é por etapa e a restrição continua no SPEC, considero fechado. `[BAIXO]` — se AD-8 for reescrito, esta é a palavra a não perder.

---

## 4. A afirmação de aditividade do roadmap

A spine afirma, na seção `Deferred`:

> *"AD-1, AD-5 e AD-8 são o que os mantém aditivos: cada um precisa saber de qual reclamação está falando, e o `id` atravessa o estado inteiro."*

**A afirmação está certa no eixo que ela nomeia e é ampla demais no que conclui.** O `id` atravessa o estado de ponta a ponta — `Reclamacao.id`, `Analise.id`, `Falha.ids`, `Pontuacao.id`, `Motivo` ancorado na pontuação. O item não-aditivo que `state-contract.md` isolou está resolvido, e resolvido melhor do que o contrato original pedia. Nenhum item do roadmap fracassa por não saber de qual reclamação está falando.

Mas identidade não é a única coisa que um item deferido precisa. Percorrendo os itens:

| Item do roadmap | Aditivo? | O que ainda exige reescrita |
|---|---|---|
| Níveis de criticidade (v2) | **não** | `na_fila` booleano consumido por `agregacao` e pelo template |
| Cascata entre modelos (v2) | **parcial** | `Sinal.valida` é booleano; falta proveniência |
| Cache de chamadas (v2) | **não** | não existe versão de prompt em lugar nenhum |
| Guard-rails (v3) | sim | — |
| Loop de crítica (v3) | **não** | AD-6 e a semântica de `Falha` |
| Checkpoint persistido (v3) | sim | — |
| Interface web (v3) | quase | efeito de disco em `renderizar` |
| Reclassificação por espera | **não** | depende de níveis + data de execução ausente |

### 4.1 Níveis de criticidade — não é aditivo `[MÉDIO]`

`Pontuacao.pontos` sobrevive e é o insumo dos níveis; do lado de `pontuacao.py` a mudança é aditiva, e isso é mérito de AD-4. O problema é rio abaixo: `na_fila: bool` é o que `agregacao.py` usa para *"ordenação da fila"* e o que o template usa para montar a seção que FR-11 põe em primeiro lugar. Trocar booleano por nível com prazo máximo de atendimento mexe em `agregacao.py`, em `relatorio.py` e no template.

Não é falha da spine — o v1 **deve** ser binário, é decisão do Q-3 com o gabarito em 38% contra o limiar de 40% da CM-1. É a afirmação de aditividade que é larga demais. Baratear é possível: se `Pontuacao` expusesse `nivel` em vez de `na_fila`, com o v1 usando um enum de dois valores, a extensão viraria acrescentar valores ao enum e o template já iteraria por nível. Custo hoje: quase zero. Custo depois: os três módulos.

Registre-se também o alerta do roadmap — *"Decidir isso **antes** de calibrar o corte binário"* — que continua pendente e não é responsabilidade da spine.

### 4.2 Cascata — meio aditiva; `Sinal.valida` é o campo estreito `[MÉDIO]`

O que funciona: o sublote é outro `Send`, o redutor `add` já acumula, o roteador é uma aresta condicional em `grafo.py`, o merge é por `id`. AD-8 entrega a estrutura, e a spine está certa ao dizer isso. AD-7 também aguenta — dois modelos, um só módulo importando o SDK.

O que não funciona: a cascata é definida no roadmap como *"um sinal só sobrevive se **dois modelos concordarem**"*. AD-1 define `Sinal = {codigo, citacao, valida}`, com `valida` booleano. Um booleano não distingue "validado por substring" de "confirmado por dois modelos", e não registra qual modelo produziu o par. Adicionar essa dimensão altera a estrutura que AD-1 fixa — e `Sinal` é lido por `evidencia.py`, `pontuacao.py` e pelo template.

AD-3 tem a mesma rigidez pelo lado do motivo: `Motivo.origem ∈ {sinal, atributo}` é enum fechado de dois valores, e a cascata quer distinguir sinal-triado de sinal-confirmado no motivo exibido ao gestor.

Conclusão precisa: **AD-1 mantém aditiva a identidade e o pareamento código↔citação, que era o risco original. Não mantém aditivo o ciclo de vida do sinal.** A afirmação da spine deveria ser qualificada nesse ponto — ou `valida` deveria nascer como campo de estado em vez de booleano, o que custa igual hoje.

### 4.3 Cache — não é aditivo, e o motivo está escrito no roadmap `[ALTO]`

O roadmap especifica a chave com precisão e explica por quê:

> *"Chave = `hash(texto + versão_do_prompt + modelo)`. Três campos, não um: a reclamação é imutável, o prompt não. Chave apenas com o texto envenena o cache no primeiro ajuste de prompt e produz depuração perdida."*

Dos três campos, a spine dá dois: `texto` está em `Reclamacao`, `modelo` está em `config.py`. **`versão_do_prompt` não existe em lugar nenhum da spine** — não há módulo de prompt, não há AD sobre prompt, `config.py` é *"lote, concorrência, modelo"*, e o Structural Seed não tem `prompts.py` nem `templates/` para prompt.

Ligar o cache exige, portanto, primeiro introduzir versionamento de prompt: mexer em `analise.py` (que hoje é dono implícito do prompt), em `config.py`, e provavelmente criar o módulo que não existe. Isso é modificação, não plugue.

Q-8 acrescenta uma segunda exigência que a spine também não acomoda: *"medir com o cache de análises desligado, ou o número mede o disco"* — ou seja, o cache precisa de chave de desligamento desde o desenho.

**Correção barata agora:** uma constante `VERSAO_PROMPT` em `config.py` ou no topo de `analise.py`, incrementada à mão quando o prompt muda. Custa uma linha no v1 e transforma o cache de reescrita em plugue. Sem ela, a spine não pode afirmar que o cache é aditivo.

### 4.4 Loop de crítica — AD-6 é o invariante que o impede `[ALTO]`

Este é o item onde a afirmação de aditividade falha mais fundo, e falha por causa de um AD que a própria afirmação não menciona.

AD-6: `len(reclamacoes) == len(analises) + sum(len(f["ids"]) for f in falhas)`. Toda reclamação está em exatamente um de dois baldes: analisada, ou falha.

O loop de crítica do roadmap exige um terceiro estado. O roadmap é explícito ao pedir a decisão: *"Definir o que acontece com a reclamação que falha três vezes — descarte, marcação como **indeterminada**, ou **fila humana**."* Nenhuma dessas três é "analisada", e nenhuma é honestamente uma `Falha`:

- `Falha = {ids, causa, no}` é registro de **falha de conteúdo ou transporte**. Uma reclamação reprovada três vezes pelo crítico foi analisada com sucesso — o resultado é que foi julgado insuficiente.
- Contá-la como `Falha` corrompe três contadores de uma vez: FR-2 (*"total não analisadas"*) reportado ao operador, FR-14 (mesmo número no relatório) e CM-4. E dispara **NFR-6**: reclamações reprovadas pelo crítico passariam a marcar o relatório como degradado, o que é semanticamente falso — o crítico funcionando é sinal de saúde, não de degradação.
- E o glossário do PRD amarra esses três termos ao mesmo conjunto: *"**não analisada** … é o mesmo conjunto que FR-2 chama de falha, que NFR-5 manda absorver e que CM-4 conta"*. Não há folga na definição.

Logo: o loop de crítica exige um terceiro balde, e o terceiro balde quebra a identidade de AD-6, que é uma asserção em código. Isso é reescrita — de AD-6, do glossário do PRD e dos contadores de FR-2/FR-14.

**Nota positiva no mesmo item:** AD-9 (*"o código do nó não tem laço de repetição"*) é exatamente a forma certa para o loop de crítica entrar depois — como ciclo no grafo, com `max_iteracoes` como propriedade de aresta, e não como `while` dentro de um nó. A spine acerta a forma e tropeça na contabilidade.

### 4.4.1 Efeito colateral de AD-6 já no v1 `[MÉDIO]`

Independente do roadmap, o mecanismo de AD-6 conflita com a convenção de erro da própria spine.

A convenção diz: *"Falha de conteúdo vira `Falha` no estado e a execução segue."* NFR-5 diz o mesmo. Mas AD-6 é *"verificado em **asserção** após o gather e antes de `pontuar`"* — e uma asserção que falha aborta a execução.

O cenário concreto: NFR-7 manda descartar `id` repetido ou inventado devolvido pelo modelo. Se a deduplicação não acontecer **dentro** de `analisar_lote`, antes do delta entrar no estado, o redutor `add` acumula duas `Analise` para o mesmo `id`, `len(analises)` sobe, e a asserção estoura. Falha de conteúdo derrubando a execução inteira — o oposto da convenção.

E o momento é o pior possível: a asserção roda **depois do gather**, ou seja, depois que 100% das chamadas pagas foram feitas. Dinheiro gasto, nenhum relatório escrito, e o modo de falha classificado como "de conteúdo" comportando-se como "de infraestrutura".

**Correção:** a violação de AD-6 deve produzir uma `Falha` e um relatório marcado como degradado, não um `AssertionError`. E a spine deve dizer explicitamente que a deduplicação de NFR-7 acontece dentro de `analisar_lote`, antes do delta — hoje isso é inferência.

### 4.5 Reclassificação por tempo de espera — bloqueada duas vezes

Depende dos níveis do v2 (4.1) e de uma noção de "agora" no estado. `Reclamacao.data` existe; `data_execucao` não (ver 1.5). Sem ela, não há aritmética de envelhecimento — e ela já é exigida pelo v1 via FR-14 e FR-1. Acrescentá-la agora resolve um requisito atual e desbloqueia um item futuro.

### 4.6 Guard-rails, checkpoint e interface web — aditivos, com uma ressalva

**Guard-rails:** o formato já existe. `evidencia.py`, chamado de `analise.py`, **é** um guard-rail de saída — a exceção declarada na direção de dependência é precisamente a fronteira onde os outros entram. Aditivo.

**Checkpoint:** um `checkpointer` no `compile()` de `grafo.py`. Os `TypedDict` são serializáveis, os redutores `add` são idempotentes por lote, o fan-out de AD-8 é determinístico a partir da ordem de `carregar`. Aditivo, e AD-8 ajuda de verdade aqui — retomar uma execução com lotes independentes é possível; com laço dentro de um nó, não seria.

**Interface web:** a direção de dependência (`main → grafo → filtros`) permite uma camada HTTP importar `grafo` sem tocar em filtro nenhum, e `main.py` continuar sendo só a CLI. Isso é mérito da spine e a afirmação se sustenta. Ressalva única: `renderizar` escreve arquivo em disco e o estado guarda `caminho_html`. Um job web quer bytes, não caminho. É uma função de vinte linhas em `relatorio.py` — modificação pequena e localizada, mas não é zero.

---

## 5. `risk-signals.md` — quem é o dono

Pergunta dupla: o **catálogo de sinais** tem dono na spine? O **modificador de `Status`** tem dono?

### 5.1 Modificador de `Status` — dono claro `[OK]`

É o item mais bem resolvido da reconciliação. O Structural Seed nomeia `pontuacao.py` como *"parcelas, **modificador de `Status`**, motivos"*, dono explícito. AD-3 dá a ele a representação correta — `origem == "atributo"`, `citacao` nula, vindo de coluna do CSV — e AD-3 existe justamente para impedir o erro de inventar citação para valor de coluna, que é o erro natural aqui. FR-9 e AD-4 levam o motivo estrutural até o relatório sem que o renderizador reconstrua nada.

A cadeia `Status` → parcela → motivo → tela está inteira e sem ambiguidade. Único senão, já registrado em 1.4: o **valor** do modificador (−1) e o **corte** (≥ 3) não estão em lugar nenhum da spine, e deveriam ao menos apontar para `risk-signals.md` como fonte única.

### 5.2 Catálogo de sinais — **sem dono** `[ALTO]`

O catálogo tem cinco códigos (`cobranca_indevida`, `prazo_estourado`, `registro_contraditorio`, `servico_nao_contratado`, `lei_citada`) e é sustentado por CAP-4, cujo critério de sucesso é *"os cinco tipos de exposição factual do catálogo são reconhecidos sobre o corpus de referência"*.

Na spine:

- `Sinal.codigo` não é declarado como enum, `Literal` ou conjunto fechado. É string livre.
- Nenhum AD amarra o conjunto de códigos válidos a `risk-signals.md`.
- Nenhum módulo é nomeado como casa do catálogo. `analise.py` consome (para o prompt), `pontuacao.py` consome (para os pesos), o template consome (para exibir), e **nenhum dos três possui**.

Consequência: o modelo pode devolver `codigo: "cobrança_indevida"` com acento, ou `"cobranca indevida"` com espaço, e o par passa por AD-1 (tem citação), passa por AD-2 (a citação é substring), chega em `pontuacao.py` e **não casa com nenhuma parcela** — pontua zero, silenciosamente. O sinal existe, é válido, é exibível, e não pontua. É falso negativo invisível, e sai direto contra CAP-6, cujo piso de recall tem 3,4 pontos de folga.

Somando ao problema dos dois vocabulários (1.4), o catálogo é a estrutura de dados mais central do domínio e a única sem lar arquitetural.

**Correção:** o catálogo vira um `Literal`/enum em `estado.py` — que já é o módulo que ninguém importa de ninguém e que todos importam —, com `risk-signals.md` declarado como fonte, e um mapeamento código→parcela em `pontuacao.py`.

### 5.3 Glossário no prompt — sem dono, e é o maior fator de acurácia `[ALTO]`

`risk-signals.md` é enfático:

> *"Cada tipo precisa de **definição escrita com exemplo dentro do prompt**. Categoria sem glossário explícito degrada a classificação — **é o fator de maior impacto na acurácia**."*

Isto é uma afirmação de arquitetura, não de implementação: diz que existe um artefato (o glossário) cuja qualidade domina o resultado do sistema. A spine não tem `prompts.py`, não tem `templates/` de prompt, não tem AD sobre a construção do prompt, e nada no Structural Seed além de `analise.py # nó analisar_lote — único módulo que importa o SDK do modelo`.

O artefato mais determinante da acurácia do sistema está, por omissão, como f-string dentro do nó. Note o contraste: o relatório HTML — que é apresentação — ganhou AD-10 inteiro para tirá-lo de f-strings e pô-lo em template governado por um `Environment` único. O prompt, que decide o conteúdo, não ganhou nada.

Isso também é o que trava o cache (4.3): sem lugar definido para o prompt, não há onde pendurar a versão dele.

**Correção:** o prompt (glossário + esquema de saída) vira arquivo próprio ou constante em módulo próprio, com versão. Uma linha no Structural Seed e uma no diagrama de dependência.

### 5.4 O gabarito e a medição de M-1 — fora da arquitetura `[MÉDIO]`

CAP-6 é aferida contra `docs/gabarito.csv`, e é a única capacidade com número de aceitação. Na spine, `baseline.py` e `classificador.py` aparecem no Structural Seed rotulados *"medição, preexistente"* — fora do pacote `plataforma/`, sem AD, sem menção em `tests/`, sem vínculo com M-1 na tabela de capacidades.

AD-12 governa a suíte e é excelente no que cobre (*"as três parcelas que a base não exercita … têm caso construído à mão — a suíte é a única coisa que as executa"*, resolvendo Q-4 e CM-2 corretamente). Mas a medição de concordância com o gabarito não é teste unitário e não está em AD-12.

Resultado: o número que prova CAP-6 é produzido por dois scripts que a arquitetura reconhece como preexistentes e não governa. Quando `pontuacao.py` mudar, nada garante que a medição seja refeita, e 100% / 68,4% é uma medição de 2026-08-06 sobre código que a spine está prestes a substituir.

**Correção:** declarar quem reproduz M-1 sobre o `pontuacao.py` novo, e se `baseline.py`/`classificador.py` sobrevivem, são portados para `tests/`, ou são aposentados.

### 5.5 A regra dos dois sinais independentes — parcialmente representada

`risk-signals.md` abre com a afirmação estrutural: *"Risco jurídico é composto por dois sinais **independentes**. Detectar apenas o primeiro produz um sistema que acerta o caso raro e perde o caso caro."*

Com AD-1 unificando tudo em `Sinal`, a independência entre A e B deixa de ser estrutural (dois campos) e passa a depender do mapeamento código→parcela — que, como visto em 1.4 e 5.2, não existe. Se `sinal_a` for absorvido corretamente como código do catálogo (0.1), a independência é preservada pelos pesos distintos. Se `sinal_a` ficar como booleano órfão, ela é preservada por acidente e sem citação. **A correção de 0.1 e a de 5.2 são a mesma correção.**

---

## 6. Achados consolidados

| # | Achado | Sev. | Onde corrigir |
|---|---|---|---|
| A-1 | Restrição *"produto do texto, nunca da empresa"* ausente da spine; `empresa` está no `Reclamacao` e nada impede que entre no prompt ou no ranking | **ALTO** | novo AD |
| A-2 | `tamanho_lote` sem piso nem teto reabre *"chamada individual proibida"* e *"base inteira num único prompt"* | **ALTO** | `config.py` + AD-8 |
| A-3 | AD-1 não diz o que acontece com `sinal_a: bool`; sobra classificação de risco sem citação | **ALTO** | AD-1 |
| A-4 | AD-4 (*"renderizar lê apenas `pontuacoes` e `agregados`"*) impede FR-14 e NFR-6, que AD-5 vincula a `relatorio` | **ALTO** | AD-4 ou `agregacao.py` |
| A-5 | Catálogo de sinais sem dono: `Sinal.codigo` é string livre; dois vocabulários (códigos × parcelas) sem mapeamento | **ALTO** | `estado.py` + `pontuacao.py` |
| A-6 | Glossário no prompt — *"fator de maior impacto na acurácia"* — sem módulo, sem AD, sem versão | **ALTO** | Structural Seed + AD |
| A-7 | Cache do roadmap não é aditivo: `versão_do_prompt` não existe na spine | **ALTO** | `config.py` (uma linha, hoje) |
| A-8 | Loop de crítica não é aditivo: exige terceiro balde, que quebra a identidade de AD-6 e a semântica de `Falha`/FR-2/NFR-6 | **ALTO** | qualificar a seção `Deferred` |
| A-9 | CAP-6: a regra que atinge 100%/68,4% lê o título; a spine não dá a `pontuacao.py` caminho até a categoria, nem registra pesos e corte | **ALTO** | AD novo ou convenção |
| A-10 | AD-6 é asserção que aborta após todas as chamadas pagas, contrariando a convenção *"falha de conteúdo segue"* e NFR-5 | **MÉDIO** | AD-6 |
| A-11 | AD-2 contradiz a letra de FR-7 (*"o sinal específico"*); CM-2 fica sem definição de contagem | **MÉDIO** | AD-2 + FR-7 |
| A-12 | Piso de cinco palavras (FR-6) sem módulo; se cair em `evidencia.py` herda o raio de AD-2 e come recall | **MÉDIO** | Structural Seed |
| A-13 | AD-11 não fecha `<script>` inline; drill-down/ordenação/`<details>` violam não-objetivo e FR-12 passando na regra | **MÉDIO** | AD-11 |
| A-14 | Níveis de criticidade não são aditivos: `na_fila` booleano preso em `agregacao` e no template | **MÉDIO** | `Pontuacao` (barato agora) |
| A-15 | Cascata meio aditiva: `Sinal.valida` booleano e `Motivo.origem` enum fechado não comportam "dois modelos concordaram" | **MÉDIO** | AD-1/AD-3 |
| A-16 | `data_execucao` não existe no estado; exigida por FR-1/FR-14 e pela reclassificação por espera | **MÉDIO** | `Estado` |
| A-17 | Diagrama de dependência da spine não liga `config` a quem fatia o lote, depois que AD-8 moveu o fatiamento para `carregar` | **MÉDIO** | diagrama + Structural Seed |
| A-18 | Terceiro diagrama de `architecture-diagrams.md` (fluxo da evidência) também caduca sob AD-2 | **MÉDIO** | companion |
| A-19 | M-6, única métrica do objetivo declarado do projeto, não tem AD nem asserção | **MÉDIO** | AD-12 ou AD novo |
| A-20 | Medição de M-1 contra o gabarito não é governada; `baseline.py`/`classificador.py` fora do pacote e sem destino | **MÉDIO** | `Deferred` ou AD-12 |
| A-21 | CAP-2/CAP-3 têm critério universal (*"cada reclamação"*) que AD-6 legitimamente não atende | **MÉDIO** | SPEC (redação) |
| A-22 | Aritmética de prazo sumiu da descrição de `pontuacao.py` | BAIXO | Structural Seed |
| A-23 | "Falha antes de qualquer chamada paga" (CAP-1) é comentário, não convenção | BAIXO | convenções |
| A-24 | FR-17 (formatação pt-BR) sem dono | BAIXO | AD-10 |
| A-25 | `paradigm` do frontmatter sugere que qualquer composição serve, enfraquecendo a restrição do LangGraph que AD-8/AD-9 sustentam | BAIXO | frontmatter |

## 7. O que a spine acerta

Registrado porque uma reconciliação só de furos distorce o resultado.

- **AD-7** transforma *"o modelo extrai, o código julga"* de prosa em regra de importação mecanicamente verificável — e fecha, de graça, o não-objetivo de normalizar CSV com LLM.
- **AD-1** resolve o item que `state-contract.md` marcava como *"a única parte do v1 que não é aditiva"*, e resolve melhor do que o contrato original: par indivisível elimina uma classe de erro que duas listas paralelas só evitam por disciplina.
- **AD-8 e AD-9** dão ao LangGraph peso estrutural real (`Send`, redutores, `RetryPolicy`), o que salva a restrição mais frágil do SPEC — a que `risk-signals.md` dá munição documentada para violar.
- **AD-3** antecipa FR-9 antes de ele ser um problema: separar `sinal` de `atributo` é o que impede inventar citação para valor de coluna.
- **AD-11** traduz autocontenção em algo verificável byte a byte e nomeia o modo de falha real (testar com internet ligada).
- **AD-12** resolve Q-4 e CM-2 corretamente: as três parcelas não exercidas viram código coberto, e o autoteste de citação falsa é o que distingue "verificação saudável" de "mecanismo morto".
- **`Deferred`** registra a ausência de envelope operacional como decisão explícita, em vez de omissão.

O padrão dos furos é consistente e diz onde olhar: **a spine é forte onde a fronteira é de código (import, pureza, template, tipos) e fina onde a regra é de conteúdo** — o que vai no prompt, quais são os códigos válidos, de que campo o produto é inferido, quanto vale cada parcela, qual o tamanho mínimo do lote. Sete dos nove achados ALTO caem nessa segunda categoria.
