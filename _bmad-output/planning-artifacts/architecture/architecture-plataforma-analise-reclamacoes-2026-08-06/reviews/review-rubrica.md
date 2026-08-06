---
title: Revisão de rubrica — ARCHITECTURE-SPINE
type: review
method: rubrica da boa spine
created: 2026-08-06
target: ../ARCHITECTURE-SPINE.md
also_read:
  - ../../../../specs/spec-plataforma-analise-reclamacoes/SPEC.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/state-contract.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/risk-signals.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/architecture-diagrams.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/roadmap.md
  - ../../../prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md
  - ../.memlog.md
  - ./reconcile-spec.md
  - ./reconcile-prd.md
  - baseline.py, classificador.py, pyproject.toml, .gitignore (código do repositório)
---

# Revisão de rubrica — Architecture Spine

**Veredito geral: adequada.**

A spine é densa e honesta. Dezoito ADs, quase todos com `Prevents` que nomeia um modo de
falha concreto, e a maioria das `Rule` é verificável por `grep` ou por um teste de uma
linha — que é o padrão certo. O padrão dos furos é o mesmo que a reconciliação anterior já
tinha identificado e continua valendo depois das correções: **a spine é forte onde a
fronteira é de código (import, pureza, tipo, template) e fina onde a regra é de conteúdo**
(o que vai no payload, quanto vale cada parcela, que forma tem `agregados`, quem carrega o
número que a métrica consome).

O que mudou desde a reconciliação: AD-13 a AD-18 fecharam sete dos nove achados ALTO
anteriores, e `state-contract.md` foi reescrito e agora bate com a spine. O que sobra está
concentrado em três lugares: a **fronteira do payload do modelo**, o **vocabulário da
pontuação** e a **fronteira `agregacao` → `relatorio`**.

Um achado novo é crítico e não aparece em nenhuma revisão anterior: **AD-16 fecha a
fronteira errada** (§1.1).

| Dimensão | Veredito |
|---|---|
| 1. Fixa os pontos reais de divergência do nível abaixo | **adequada** |
| 2. Cada Rule é executável e previne o que declara | **forte** |
| 3. Nada sob Deferred permite duas unidades divergirem | **forte** |
| 4. Tecnologia nomeada é verificada e atual | **adequada** |
| 5. Cobre as capacidades do SPEC que a dirigiram (CAP-1..9) | **adequada** |
| 6. Toda dimensão desta altitude decidida, adiada ou aberta | **adequada** — envelope operacional **rala** |

---

## 1. Fixa os pontos reais de divergência do nível abaixo — **adequada**

As unidades abaixo são as onze de sempre: `estado`, `catalogo`, `ingestao`, `analise`,
`evidencia`, `pontuacao`, `agregacao`, `relatorio`, o template, `grafo`/`config`, e a suíte.
A pergunta útil é fronteira a fronteira: nas costuras entre duas unidades, existe regra?

**Costuras fixadas, e bem:** forma do estado (AD-1, AD-3, AD-5), topologia do fan-out
(AD-8), política de repetição (AD-9), fronteira de pureza (AD-7), fronteira do template
(AD-10, AD-11), porta de aborto (AD-13), nome do artefato (AD-15), validação de
configuração (AD-17), casa do catálogo (AD-18). Nove costuras com dono explícito é bastante.

**Costuras que continuam abertas** — cada uma abaixo produz duas implementações que passam
em todos os ADs e não se encaixam.

### 1.1 `[CRÍTICO]` AD-16 proíbe `empresa` e admite `titulo` — a fronteira errada

> AD-16, `Rule`: *"o payload enviado ao modelo carrega `id`, `titulo` e `texto`. `empresa`
> fica fora, por construção — não por instrução no prompt."*

AD-16 é, na forma, o melhor AD do documento: uma fronteira de dados fechada por construção,
verificável com uma asserção sobre as chaves do dicionário. E fecha um vazamento real.

Só que fecha o segundo vazamento mais grave e abre o primeiro.

`risk-signals.md` mede duas abordagens e a diferença entre elas é exatamente o `titulo`:

> | Regra | Precisão | Recall | F1 |
> | Categoria (determinística, **vê o título**) | 89% | 84% | 0.86 |
> | Gemini 3.6 Flash (**vê apenas o texto livre**) | 89% | 84% | 0.86 |

E `classificador.py` registra a razão de desenho, em comentário de módulo:

> *"Diferença deliberada em relação a baseline.py: o modelo vê **apenas o texto livre** da
> reclamação, nunca o título. O título desta base é canônico (18 valores fixos) e entrega a
> resposta; base real não tem isso. Ganhar sem o título é ganhar de verdade."*

O título desta base é uma de dezoito strings canônicas, e a regra determinística que atinge
**100% de precisão** — a única que atende M-1 — é `set` de títulos + `Status`. Ou seja: o
título **é** o gabarito. Colocá-lo no payload do modelo:

- **anula a comparabilidade de M-1.** O 89%/84% do LLM foi obtido sem o título. O pipeline
  entregue mede outra coisa, e mede para cima. O número que a spine herda como aceite deixa
  de valer para o sistema que a spine descreve.
- **destrói a única afirmação de portfólio que o projeto tem sobre o LLM** — *"o LLM se
  validou: reconstruiu a categorização inteira lendo apenas o texto livre"*. Com o título no
  payload, não reconstruiu nada, leu a resposta.
- **é o mesmo erro que AD-16 existe para prevenir, um campo ao lado.** O `Prevents` de AD-16
  fala em inferir produto da empresa. Inferir categoria do título é o mesmo mecanismo, com
  consequência maior: `empresa` envenena o ranking (leitura não validada, sem métrica);
  `titulo` envenena a fila (a única leitura exercida, e a única com número de aceite).

**Como eu verificaria:** asserção sobre as chaves do payload — hoje ela passaria com
`titulo` dentro, porque AD-16 o autoriza. O teste que pega o problema é outro: rodar a
suíte de M-1 e comparar com o 89%/84% de `risk-signals.md`; se subir, o título está dentro.

**Correção, e ela fecha dois furos de uma vez:** o payload leva `id` e `texto`. O `titulo`
não atravessa a fronteira do modelo — atravessa a fronteira **determinística**, alimentando
a derivação de categoria que hoje não tem módulo nenhum (ver 1.2). Uma linha em AD-16 e uma
linha nova de convenção resolvem o achado crítico desta revisão e o achado ALTO de CAP-6
que a reconciliação do SPEC deixou aberto (A-9).

### 1.2 `[ALTO]` O vocabulário da pontuação continua sem mapeamento

AD-18 deu casa aos **códigos do catálogo** (`cobranca_indevida`, …) e isso resolveu metade do
problema. A outra metade não foi tocada: as **parcelas de peso** de `risk-signals.md`
(dinheiro retido 3, ameaça explícita 3, dano continuado 2, registro contraditório 2, prazo
1, modificador `Status` −1, corte binário em ≥3) são outro vocabulário, e a parcela que
sozinha explica o gabarito — *"dinheiro do cliente retido"* — **não é um código do catálogo**.

Na spine, `pontuacao.py` é *"parcelas, modificador de `Status`, motivos"*. Não há AD que diga
(i) onde vive a derivação categoria←título, (ii) qual código do catálogo alimenta qual
parcela, (iii) que os pesos e o corte vêm de `risk-signals.md`. AD-18 chega a proibir código
de sinal literal em `pontuacao.py`, mas não diz nada sobre os pesos — que, por omissão,
nascem literais ali sem fonte declarada.

Consequência mecânica: dois desenvolvedores escrevem duas pontuações, e nenhuma das duas
reproduz necessariamente o 100%/68,4% medido em 2026-08-06.

Previamente levantado (reconcile-spec 1.4 / A-9), **não endereçado**, e agora agravado pela
1.1: com o título dentro do payload, a categoria pode nascer do modelo em vez do CSV, e aí
`Motivo.origem` vira `"sinal"` onde AD-3 manda ser `"atributo"`.

### 1.3 `[ALTO]` `agregados: dict` é a única fronteira do estado sem forma

`state-contract.md` tipa sete estruturas com precisão e deixa uma linha solta:

> `agregados: dict`

Por essa fronteira passa **tudo o que o relatório mostra fora da fila**: ranking de produtos
(FR-13), distribuição de sentimento (FR-15), totais de FR-14, o rótulo `não identificado`
(FR-8), os genéricos de CM-3, o flag de degradado (NFR-6) e as ressalvas de AD-14. É a
costura `agregacao` → `template` inteira, e é a única sem contrato.

A spine gastou um AD inteiro (AD-4) fixando a forma de `Pontuacao` para que o renderizador
não reconstruísse a regra — e deixou aberta, ao lado, a estrutura por onde entra tudo o
resto. Duas stories, duas grafias de chave, e o template quebra em silêncio (Jinja2 resolve
chave ausente como vazio; `autoescape` não ajuda aqui).

**Como eu verificaria:** hoje não dá — não existe forma contra a qual verificar. Com um
`TypedDict Agregados`, o teste é o mesmo de AD-12: `renderizar` alimentado por agregado
fabricado à mão.

### 1.4 `[ALTO]` NFR-6 sem dono, e a correção de AD-4 empurrou a regra para dentro do template

AD-4 foi corrigido para liberar a leitura de `falhas`:

> *"e `falhas` para cumprir FR-14 e NFR-6, sem o que ele não tem como saber que a execução
> foi degradada."*

A correção era necessária e a direção é certa. O efeito colateral não foi visto: com
`falhas` na mão do template e sem `agregados` tipado, o caminho de menor resistência é
`{% if falhas|length / total > 0.1 %}` — a regra numérica de NFR-6 vivendo em Jinja2.

Isso viola o princípio de AD-4 (*"quem pontua carrega o motivo; quem renderiza não o
reconstrói"*) sem violar a letra de AD-4, que fala só de `Reclamacao`. E põe a única regra
de honestidade com limiar numérico do PRD fora do alcance de AD-12. O limiar de 10% também
não está em `config.py` (*"lote, concorrência, modelo"*) nem como constante em lugar nenhum.

Previamente levantado (reconcile-prd 2.9), e a correção subsequente de AD-4 **piorou** o
achado em vez de fechá-lo.

### 1.5 `[ALTO]` Quem fatia o lote, e como a resposta chega estruturada

Duas perguntas na mesma costura, ambas sem resposta.

**(a) Quem fatia.** AD-8: *"`carregar` emite um `Send` por lote"*. O diagrama de direção de
dependência da própria spine desenha `config -.-> analise` e `config -.-> grafo`, e nenhuma
aresta `config -.-> ingestao`. O Structural Seed descreve `ingestao.py` como *"valida schema
e unicidade"*, sem fatiamento. E `architecture-diagrams.md` — companion do contrato canônico
— ainda atribui na tabela de nós: *"`analisar_lotes` | LLM | **Fatia em lotes**, saída
estruturada, casa resposta por `id`"*. Três documentos, três donos. Previamente levantado
(reconcile-spec 0.3 / A-17), **não endereçado**; o memlog registra a correção do companion
como feita, mas só o diagrama foi corrigido — a tabela de nós, não.

**(b) Saída estruturada.** A expressão *"saída estruturada"* aparece uma única vez em todo o
material vinculante: naquela mesma linha da tabela que a spine contradiz. Nenhum AD, nenhuma
convenção e nenhuma linha de Stack menciona o mecanismo pelo qual a resposta do modelo vira
`Analise` — e `classificador.py` já resolveu isso de um jeito específico:

```python
response_mime_type="application/json",
response_schema=Lote,   # pydantic BaseModel
```

Isso é a costura mais carregada do sistema: dela dependem NFR-7 (casamento por `id`), a
detecção de resposta incompleta, a forma inteira de `Analise` e, por consequência, AD-6.
Uma story usa `response_schema`; outra pede JSON no prompt e parseia texto. As duas passam
em AD-7, AD-8, AD-9 e AD-16, e só uma detecta id inventado de forma confiável.

### 1.6 `[MÉDIO]` `data_execucao` ainda não existe, e agora AD-15 depende dela

AD-15 fixa o prefixo do nome do arquivo; FR-1 manda o nome conter a data da execução; FR-14
manda o relatório informá-la. `Estado` não tem `data_execucao`, e o Structural Seed de
`estado.py` lista *"Reclamacao · Sinal · Analise · Falha · Motivo · Pontuacao · Estado"*.

Se `main.py` deriva o nome com um `date.today()` e o template estampa outro, os dois divergem
na virada de meia-noite e numa reexecução — e a colisão de FR-4 passa a depender de qual dos
dois foi consultado. Ligado a isso: **o momento da checagem de colisão de FR-4 continua sem
dono** (reconcile-prd 2.3, não endereçado). Checar em `main.py` custa milissegundos; checar
em `renderizar` custa a execução inteira contra o tier gratuito de NFR-3.

### 1.7 `[MÉDIO]` O produto genérico de CM-3 não tem lugar

FR-8 e AD-14 tratam o produto **nulo** (1 de 50). CM-3 foi reescrita no PRD justamente porque
contar só o nulo *"media exatamente o caso que o modelo evita"*: o número real é 38%, com 18
de 50 caindo em `fatura`, `compra`, `produto`, `serviço`. Na spine não há dono para a lista
de genéricos nem para a decisão do que fazer com eles — `agregacao.py` é *"ranking,
distribuição, ordenação da fila"*. Uma story entrega um ranking cujo topo é `fatura`, que é
tecnicamente correto e é exatamente o defeito que CM-3 existe para expor. Previamente
levantado (reconcile-prd 2.6), não endereçado. AD-14 cobre a **ressalva** sobre o ranking
raso, o que é meio caminho — e é meio caminho que torna o outro meio mais fácil de esquecer.

### 1.8 `[MÉDIO]` AD-11 não fecha `<script>` inline nem `<details>`

> AD-11: *"nenhuma biblioteca de plotagem, nenhum `<script src>`, nenhum `<link href>`
> externo"* — todos externos.

`<script>` inline satisfaz AD-11 inteiro: todo byte já estava no arquivo. E `<details>`
satisfaz AD-10 e AD-11. FR-12 exige a evidência como *"conteúdo visível e não como detalhe
expansível"*, e o SPEC proíbe *"drill-down"* e *"ferramenta de decisão elaborada"*. Ordenar
o ranking por clique é vinte linhas, passa em tudo, e é o que se faz quando o público inclui
um avaliador técnico e interatividade parece qualidade. Previamente levantado (reconcile-spec
3.2 / A-13), não endereçado. A regra que fecha é também a mais barata de verificar do
documento inteiro: *o arquivo de saída não contém a substring `<script`*.

---

## 2. Cada Rule é executável e previne o que declara — **forte**

Percorri os dezoito. A tabela abaixo só traz aqueles onde a verificação é interessante ou
onde a regra não entrega o que promete.

| AD | Como eu verificaria | Previne o que declara? |
|---|---|---|
| AD-7 | `importlib` + inspeção de `sys.modules` após importar cada módulo isolado; ou `grep -r "google.genai" plataforma/ \| grep -v analise.py` | **Sim.** É o modelo do que uma Rule deve ser: converte prosa (*"o modelo extrai, o código julga"*) em predicado mecânico, e fecha de graça o não-objetivo de normalizar CSV com LLM |
| AD-16 | asserção sobre as chaves do dict do payload | Sim para `empresa`, **não para o que importa** — ver 1.1 |
| AD-17 | `pytest.raises` com `tamanho_lote` 1 e 26 | **Sim.** Duas proibições do SPEC viram duas comparações |
| AD-10 | `grep -c "Environment(" plataforma/` = 1; asserção de que `env.autoescape` é verdadeiro para `.html` | **Sim** |
| AD-15 | `assert caminho.name.startswith("relatorio-")`. Verifiquei o pressuposto: o `.gitignore` do repositório tem `relatorio*.html`, e o padrão sem barra casa em subdiretório — logo `docs/relatorio-*.html` é ignorado | **Sim**, e o `Prevents` é literalmente verdadeiro contra o repositório real |
| AD-13 | teste: `analises == []` ⇒ encerra e nenhum arquivo escrito; teste: CSV só com cabeçalho ⇒ encerra em `carregar` | **Sim.** Fecha as linhas "API fora do ar" e "CSV vazio" da §6 do PRD, que eram as duas contradições da reconciliação |
| AD-12 | rodar a suíte com `GEMINI_API_KEY` ausente e sem rede | **Sim.** É a regra que mantém as outras testáveis |
| AD-1 | inspeção do `TypedDict` (`citacao: str` não-opcional torna o par estrutural) + teste com citação de 4 palavras | Sim para o pareamento; ver 2.1 para o piso |
| AD-2 | teste: dois pares do mesmo código, um inválido ⇒ o código não pontua | Sim para o raio; ver 2.2 para o contador |
| AD-4 | inspeção do template: nenhuma `{% if %}` referencia a variável de reclamações | Sim para o alvo nomeado; a regra é **mais estreita que o `Prevents`** — ver 1.4 |
| AD-6 | executar e observar; a asserção é o próprio teste | **Parcialmente** — ver 2.3 |
| AD-14 | teste sobre o HTML de saída: a ressalva aparece; adjacência ao gráfico é inspeção | Sim, com o "ao lado, não em rodapé" dependendo de julgamento — aceitável nesta altitude |
| AD-18 | `grep` por literal de código de sinal em `analise.py`, `pontuacao.py` e no template | **Sim** para os códigos; não alcança os pesos — ver 1.2 |

### 2.1 `[MÉDIO]` O piso de cinco palavras herdou o raio de AD-2, contra a letra de FR-6

AD-1 deu dono ao piso — era o achado A-12 — e escolheu o lado que a reconciliação tinha
avisado que era o caro:

> AD-1: *"A citação tem piso de cinco palavras (FR-6), verificado **no mesmo lugar que a
> verificação de substring**"*
> AD-2: *"se qualquer `Sinal` de um dado `codigo` falha na verificação de substring **ou no
> piso de cinco palavras**, aquele `codigo` é ausente"*

FR-6 diz que o sinal com citação curta *"não é registrado"* — um par. AD-2 mata o código
inteiro, inclusive os pares irmãos que passaram. Isso come recall de graça, e o recall tem
**3,4 pontos de folga** contra o piso de 65% de M-1. A escolha é defensável pelo custo
assimétrico do falso positivo, mas não está declarada como escolha: quem ler FR-6 e AD-1 não
percebe que uma citação curta agora derruba as boas do mesmo código. Uma frase no `Prevents`
de AD-2 basta.

### 2.2 `[ALTO]` AD-2 fixou a unidade do contador e não a sobrevivência do dado

AD-2 resolve corretamente uma ambiguidade de três leituras:

> *"A contagem que FR-2 e CM-2 reportam é de **códigos derrubados**"*

Mas FR-2 exige que esse número chegue ao terminal do operador, e CM-2 é a contramétrica que
o PRD destaca como a que *"disparou exatamente o alerta que foi desenhada para dar"*. Duas
peças faltam para o número existir:

1. **Onde ele mora.** Não há campo em `Analise`, `Falha` ou `Estado`; `agregados` é um dict
   sem forma (1.3). Sobrevive só se o par reprovado **permanecer** na lista com
   `valida=False` — que é o que `Sinal.valida: bool | None` permite, mas que nenhum AD manda
   fazer. E colide com FR-6 (*"não é registrado"*): sob a leitura literal de FR-6 o par curto
   nunca nasce, e a contagem que AD-2 acabou de definir perde o insumo.
2. **Quem o imprime.** `main.py` é *"CLI: caminho do CSV e flag de sobrescrita"*. Os quatro
   números de FR-2 não têm carregador nem impressor.

O resultado é o pior possível para uma contramétrica: um zero indistinguível de mecanismo
morto — que é literalmente o alerta que o PRD registra em CM-2.

### 2.3 `[MÉDIO]` AD-6 é uma asserção, e asserção não é a ferramenta

> AD-6: *"verificado em **asserção** após o gather e antes de `pontuar`"*

Dois problemas, um de comportamento e um de mecânica:

- **Comportamento.** Uma asserção que falha aborta. A convenção de erro da própria spine diz
  *"falha de conteúdo vira `Falha` no estado e a execução segue"*, e NFR-5 diz o mesmo. Uma
  violação de conservação — por exemplo, `id` duplicado devolvido pelo modelo entrando no
  delta antes da deduplicação de NFR-7 — é falha de conteúdo, e aqui derruba a execução
  **depois de 100% das chamadas pagas terem sido feitas**. Dinheiro gasto, nenhum relatório.
  Previamente levantado (reconcile-spec 4.4.1 / A-10), não endereçado.
- **Mecânica.** `python -O` remove `assert`. O único guardião da conservação do sistema
  desaparece com uma flag de linha de comando, sem aviso. Uma regra executável não pode ser
  desligável por otimização: isto precisa ser um `if ... raise`, ou uma `Falha` mais o flag
  de degradado.

Também não é dito onde acontece a deduplicação de NFR-7 — dentro de `analisar_lote`, antes
do delta, é a única posição em que AD-6 é verdadeira. Hoje é inferência.

---

## 3. Nada sob Deferred permite duas unidades divergirem — **forte**

Esta é a melhor seção do documento e merece registro explícito: a `Deferred` **argumenta
contra si mesma**, item por item, em vez de afirmar aditividade genérica. A correção do
memlog (*"a afirmação valia só no eixo da identidade"*) produziu um texto que separa
checkpoint e guard-rails (aditivos de fato) de cache (falta versão do prompt), cascata
(`valida` é booleano), loop de crítica (terceiro balde quebra AD-6) e níveis de criticidade
(`na_fila` é booleano). Cada uma dessas quatro conclusões está correta e verificável contra
`roadmap.md`.

Percorri os cinco itens perguntando se algum deixa uma decisão **do v1** em aberto — nenhum
deixa. Concorrência tem default (AD-9), níveis têm booleano fixado (AD-4), roteamento não
existe, persistência está fora.

Duas observações que não chegam a ser achados de divergência:

- **`[BAIXO]` O cache declarado deferido já existe no repositório.** `classificador.py` tem
  `CACHE = Path(...)/".cache_analises.json"` com `usar_cache=True` por padrão, e o
  `.gitignore` ignora o arquivo. A spine lista `classificador.py` no Structural Seed como
  *"medição, preexistente"* e no mesmo documento defere cache. Não há divergência de build
  porque nada de `plataforma/` lê esse cache — mas Q-8 do PRD manda *"medir com o cache de
  análises desligado, ou o número mede o disco"*, e a spine não diz que o desligamento é
  responsabilidade de quem reproduzir M-1 (ver 5.2).
- **Níveis de criticidade:** a spine registra corretamente que não são aditivos. Trocar
  `na_fila: bool` por `nivel` com enum de dois valores custaria hoje quase nada e depois
  custa três módulos. Registrar o custo em vez de pagá-lo é decisão legítima; anoto só para
  que ela seja consciente.

---

## 4. Tecnologia nomeada é verificada e atual — **adequada**

Reverifiquei os cinco itens da tabela `Stack` contra a API do PyPI hoje, 2026-08-06:

| Item da Stack | Última versão no PyPI | `requires_python` | Veredito |
|---|---|---|---|
| langgraph 1.2.10 | 1.2.10 | ≥3.10 | atual, compatível |
| jinja2 3.1.6 | 3.1.6 | ≥3.7 | atual, compatível |
| pytest 9.1.1 | 9.1.1 | ≥3.10 | atual, compatível |
| google-genai ≥2.17.0 | 2.17.0 | ≥3.10 | atual, compatível |
| python-dotenv ≥1.2.2 | 1.2.2 | ≥3.10 | atual, compatível |

Cinco de cinco são exatamente a versão corrente, e todas aceitam o Python ≥3.11 declarado.
Nenhuma tecnologia inventada, nenhuma versão fantasma. Esta parte está feita com cuidado.

O que rebaixa a dimensão de *forte* para *adequada* é o que **não** está na tabela.

### 4.1 `[MÉDIO]` O modelo não é nomeado, e é o item cuja identidade move a métrica

`config.py` é *"lote, concorrência, **modelo** — de env com default"*, e o default não é
dito em lugar nenhum. Enquanto isso, `classificador.py` pina, com a razão escrita:

```python
MODELO = "gemini-3.6-flash"  # pinado de propósito: alias móvel invalida comparação de F1
```

M-1, M-4 e CM-2 foram medidos contra esse pino. A spine deixa o modelo como variável de
ambiente sem default declarado e sem menção na `Stack` — ou seja, o único componente
nomeado cuja troca **muda o número de aceite do produto** é o que está fora da tabela de
versões, enquanto `python-dotenv` está dentro. A restrição do SPEC (*"Provedor de LLM:
Google AI Studio (Gemini)"*) sobrevive; a reprodutibilidade da medição, não.

### 4.2 `[BAIXO]` Stack incompleta em duas pontas e sem convenção de pinagem

- **Saída estruturada / pydantic.** `classificador.py` importa `pydantic` e usa
  `response_schema`. Se `analise.py` seguir o mesmo caminho, pydantic é dependência de
  runtime e não está na Stack; se não seguir, a decisão contrária também não está escrita
  (ver 1.5b).
- **A Stack diverge do `pyproject.toml`.** Hoje o projeto declara apenas `google-genai` e
  `python-dotenv`. langgraph, jinja2 e pytest não estão lá, e não há grupo de dev. É
  implementação, não spine — mas o Structural Seed também não lista `pyproject.toml` (ver
  6.1), então nada na arquitetura aponta para onde a Stack se materializa.
- **Pinagem mista sem regra:** langgraph, jinja2 e pytest com versão exata; google-genai e
  python-dotenv com `≥`. Nenhuma convenção diz por quê. Para langgraph a pinagem exata é
  provavelmente deliberada (API em movimento); não estando escrita, a próxima story
  "atualiza dependências" e desfaz.

---

## 5. Cobre as capacidades do SPEC que a dirigiram — **adequada**

Todas as nove estão na tabela `Capability → Architecture Map` com módulo e governança —
nenhuma capacidade órfã. O que segue é onde a cobertura é formal e não efetiva.

| CAP | Cobertura | Veredito |
|---|---|---|
| CAP-1 Ingestão | convenções + AD-13 (CSV vazio) + AD-17 (aborto antes de chamada paga) | **Boa.** A propriedade *"antes de qualquer chamada paga"* deixou de ser só comentário: AD-13 e AD-17 abortam antes do primeiro `Send`. Achado A-23 pode ser considerado fechado na prática |
| CAP-2 Sentimento | AD-7 + AD-14 (ressalva) | Boa. AD-14 é a resposta certa a uma leitura que a base não exercita |
| CAP-3 Produto | AD-7 + AD-16 | **Comprometida** — 1.1 (título) e 1.7 (genéricos de CM-3) |
| CAP-4 Sinais | AD-1, AD-7, AD-18 | Boa. AD-18 fechou o catálogo sem dono |
| CAP-5 Evidência | AD-1, AD-2, AD-12 | Boa no mecanismo; contador sem casa (2.2) e raio do piso não declarado (2.1) |
| CAP-6 Priorização | AD-3, AD-4, AD-12, AD-18 | **Comprometida** — 1.2: o caminho até o número de aceite não existe na spine |
| CAP-7 Agregação | AD-5, AD-6, AD-12 | Formal. Tudo o que CAP-7 produz atravessa `agregados: dict` (1.3) |
| CAP-8 Relatório | AD-4, AD-10, AD-11, AD-13, AD-14, AD-15 | **A mais bem coberta do documento.** Seis ADs, todos verificáveis. Furos: `<script>` inline (1.8), NFR-6 sem dono (1.4), FR-17 sem dono (5.1) |
| CAP-9 Orquestração | AD-7, AD-8, AD-9, AD-17, paradigma | Forte no mecanismo; M-6 sem invariante (5.2) |

### 5.1 `[BAIXO]` FR-17 continua sem dono, e a convenção de datas só fecha a entrada

> Convenção: *"ISO-8601 no estado; `DD/MM/AAAA` **só na fronteira de leitura do CSV**"*

"Só na leitura" fecha a fronteira de escrita. FR-17 exige rótulos e **números formatados na
convenção local**, e FR-14 exige a data da execução no relatório. Seguindo a convenção ao pé
da letra, o gestor recebe `2026-03-14` e `1234.5`. AD-10 já governa o `Environment` do
Jinja2, que é exatamente onde filtros de formatação vivem — falta uma frase. Previamente
levantado (reconcile-prd 1.3), não endereçado.

### 5.2 `[BAIXO]` M-6 e M-1 — as duas métricas sem contraparte arquitetural

- **M-6** é, nas palavras do PRD, *"a única métrica que mede o objetivo declarado do
  projeto"*, e é verificável (*"acrescentar um nó ao grafo e observar que o diff não toca os
  nós anteriores"*). AD-12 governa a suíte e lista verificar/pontuar/agregar/renderizar —
  não a extensibilidade. A propriedade que justifica o projeto inteiro é a única sem
  asserção.
- **M-1** é aferida por `baseline.py` e `classificador.py`, que o Structural Seed lista como
  *"medição, preexistente"* — fora de `plataforma/`, fora de `tests/`, sem AD, sem destino
  declarado. Quando `pontuacao.py` existir, nada diz quem reproduz 100%/68,4% sobre ele, nem
  se os dois scripts são portados, mantidos ou aposentados. Previamente levantado
  (reconcile-spec 5.4 / A-20), não endereçado.

---

## 6. Toda dimensão desta altitude decidida, adiada ou aberta — **adequada**; envelope operacional **rala**

Varri as dimensões que uma spine de feature costuma ter e nenhuma está em silêncio total:
paradigma, estado, dependência, erro, concorrência, custo, teste, apresentação, segurança de
credencial, i18n (parcial, 5.1) e desempenho (aberto e nomeado via Q-8) têm todas alguma
contraparte. É bom.

O envelope operacional é o caso que a spine declara não possuir. A declaração:

> `Deferred`: *"**Envelope operacional.** Não há deploy, ambiente, provisionamento ou
> observabilidade: a execução é manual, local, iniciada pelo operador, e a saída é um
> arquivo. Esta altitude não possui essa dimensão, e registrá-la como ausente é a decisão."*

**A justificativa se sustenta em metade e é fuga na outra metade**, e a divisão é limpa.

**Onde se sustenta:** deploy, provisionamento, infraestrutura, orquestração de ambiente,
disponibilidade, escalonamento. Não há serviço, não há uptime, não há nada rodando entre
execuções. Registrar isso como ausência explícita está certo e é melhor que silêncio.

**Onde é fuga:** a frase junta quatro coisas e usa a ausência das três primeiras para
descartar a quarta. **Observabilidade existe nesta altitude e é requisito**, e o envelope de
execução existe:

### 6.1 `[MÉDIO]` A spine escreve três regras contra um envelope que declara não ter

- **FR-2 é observabilidade.** Quatro números ao operador ao encerrar (*"sem isso o operador
  não distingue uma execução limpa de uma execução silenciosamente degradada"*), e §2.1 do
  PRD define o operador como papel de produto. Não têm carregador nem impressor (2.2).
- **A §6 do PRD define comportamento de saída**: *"encerra com a causa nomeada, sem gerar
  relatório, **informando quantos lotes haviam concluído**"*. Nada na spine diz quem informa,
  nem se há convenção de código de saída. Para um executável de linha de comando, isso é o
  contrato operacional.
- **A spine legisla sobre o envelope em três lugares enquanto o declara inexistente:**
  AD-15 depende do `.gitignore` do repositório; a convenção de Credencial depende de `.env`;
  a convenção de Configuração depende de `python-dotenv` e de variáveis de ambiente. Uma
  dimensão contra a qual se escrevem três regras é uma dimensão que existe.
- **O Structural Seed não lista os quatro arquivos que a materializam** — `pyproject.toml`,
  `.gitignore`, `.env.example`, `README.md` — e os quatro existem no repositório hoje. Os
  três últimos carregam DG-2/DG-4/DG-5, e o primeiro carrega a Stack inteira. Previamente
  levantado (reconcile-prd 5.2 / item 7), não endereçado.

Nada disso pede uma seção de deploy. Pede que a frase pare de usar "não há deploy" como
justificativa para não decidir quem imprime FR-2, o que o processo devolve ao encerrar, e
onde a Stack se materializa. **Correção:** trocar a frase por *"Não há deploy, ambiente nem
provisionamento — a execução é manual e local. O envelope que existe é o de operação de CLI:
FR-2 é impresso por `main.py`, falha de infraestrutura encerra com código de saída
diferente de zero, e `pyproject.toml`, `.gitignore`, `.env.example` e `README.md` fazem parte
do artefato."* Uma frase converte fuga em decisão.

### 6.2 `[BAIXO]` DG-3 é a única regra de governança de dados sem contraparte

DG-3 diz que o relatório gerado sobre base real *"herda os dados pessoais contidos nessas
citações e deve ser tratado como documento restrito"*. O único lugar onde essa regra pode
agir é o próprio HTML, que circula por e-mail sem controle de acesso. A spine já tem o
padrão pronto e usado duas vezes — FR-16 e AD-14 põem ressalva obrigatória no relatório.
DG-3 não recebeu o mesmo tratamento. AD-15 cobre o vazamento *para o repositório*, que é a
metade fácil; a metade que chega ao leitor não tem regra.

### 6.3 `[BAIXO]` Companion vinculante ainda contradiz a spine em dois pontos

O memlog registra *"architecture-diagrams.md corrigido"*, mas a correção foi parcial. Além
da tabela de nós (1.5a), o terceiro diagrama continua desenhando `citação inválida → sinal
derrubado para falso`, um par por vez — o raio de AD-2 é o código inteiro. Como o SPEC
declara os companions *"o contrato completo do que construir"*, quem seguir o contrato
canônico implementa o raio errado. Previamente levantado (reconcile-spec 0.2 / A-18).

Nota positiva no mesmo eixo: `state-contract.md` **foi** reescrito e hoje bate com a spine
(`Sinal`, `Falha`, `Motivo`, `Pontuacao` presentes; `sinal_a`, `sinal_b`, `evidencia`,
`scores` removidos). O conflito de fonte ALTO do anexo da reconciliação do PRD está fechado.

---

## 7. Achados consolidados

| # | Achado | Dim. | Sev. | Onde corrigir |
|---|---|---|---|---|
| R-1 | AD-16 admite `titulo` no payload do modelo — o título desta base é o gabarito; anula a comparabilidade de M-1 e a afirmação central de `risk-signals.md` | 1,2,5 | **CRÍTICO** | AD-16 + convenção nova (fecha também R-2) |
| R-2 | Vocabulário da pontuação sem mapeamento: parcelas, pesos, corte e derivação categoria←título não têm dono nem fonte declarada | 1,5 | **ALTO** | AD novo ou convenção |
| R-3 | `agregados: dict` é a única fronteira do estado sem forma, e por ela passa todo o relatório fora da fila | 1 | **ALTO** | `state-contract.md` + AD-4 |
| R-4 | NFR-6 sem dono; a correção de AD-4 empurrou a regra de 10% para dentro do template, fora de AD-12 | 1,2 | **ALTO** | AD-4 ou AD-5 + `config.py` |
| R-5 | Contador de FR-2/CM-2 sem campo, sem carregador e sem impressor; sob a letra de FR-6 o par curto é destruído antes de ser contável | 2,5 | **ALTO** | AD-2 + `Estado` |
| R-6 | Quem fatia o lote (AD-8 × diagrama × companion) e como a resposta chega estruturada (`response_schema`) — duas costuras sem regra | 1,2 | **ALTO** | AD-8 + Structural Seed + AD novo |
| R-7 | Modelo não nomeado na Stack; `config.py` deixa alias móvel onde `classificador.py` pinou de propósito | 4 | MÉDIO | Stack + `config.py` |
| R-8 | Envelope operacional: a ausência de deploy é usada para descartar a observabilidade de FR-2, o comportamento de saída, e os quatro arquivos que três regras da spine já pressupõem | 6 | MÉDIO | `Deferred` + Structural Seed |
| R-9 | AD-6 como `assert`: aborta após 100% das chamadas pagas contra a convenção de erro, e `python -O` remove a única guarda de conservação | 2 | MÉDIO | AD-6 |
| R-10 | `data_execucao` ausente do estado, com AD-15/FR-1/FR-14 dependendo dela; momento da checagem de FR-4 sem dono | 1 | MÉDIO | `Estado` + convenção |
| R-11 | Produto genérico de CM-3 (38% real) sem dono em `agregacao.py` | 1,5 | MÉDIO | Structural Seed ou AD-14 |
| R-12 | AD-11 não fecha `<script>` inline nem `<details>`; FR-12 "visível, não expansível" sem regra | 1 | MÉDIO | AD-11 |
| R-13 | Piso de cinco palavras herdou o raio de AD-2 contra a letra de FR-6, sem que a escolha esteja declarada | 2 | MÉDIO | AD-2 (`Prevents`) |
| R-14 | Stack incompleta (pydantic/saída estruturada), divergente do `pyproject.toml`, e sem convenção de pinagem | 4 | BAIXO | Stack |
| R-15 | M-6 sem invariante e M-1 sem quem a reproduza; `baseline.py`/`classificador.py` sem destino | 5 | BAIXO | AD-12 |
| R-16 | FR-17 sem dono; a convenção de datas fecha a entrada e deixa a saída em ISO | 5 | BAIXO | AD-10 ou convenções |
| R-17 | DG-3 (documento restrito) é a única regra de governança sem contraparte no artefato | 6 | BAIXO | AD-14 ou AD-10 |
| R-18 | `catalogo.py` fora do diagrama de dependência, cuja frase de fecho (*"uma exceção declarada"*) ficou falsa com AD-18 | 2 | BAIXO | diagrama |
| R-19 | `architecture-diagrams.md`: tabela de nós e fluxo da evidência ainda contradizem AD-8 e AD-2, apesar de o memlog registrar a correção | 6 | BAIXO | companion |

**Contagem:** 1 crítico, 5 altos, 7 médios, 6 baixos.

---

## 8. O que a spine acerta, e por que o veredito não é mais baixo

Uma revisão só de furos distorce. O que está feito com cuidado incomum:

- **AD-7, AD-16, AD-17 e AD-10 são o gênero certo de regra**: predicados sobre o código, não
  intenções sobre o comportamento. `grep`, contagem de `Environment`, chaves de um dicionário,
  duas comparações numéricas. Uma spine cujas regras se verificam assim é rara.
- **A `Deferred` argumenta contra si mesma.** Corrigir *"tudo é aditivo"* para quatro
  parágrafos que dizem exatamente o que não é aditivo e por quê é o oposto do movimento
  usual, e é o motivo de a dimensão 3 sair forte.
- **AD-13 e AD-14 são regras de honestidade convertidas em estrutura.** Uma fecha o relatório
  sobre nada; a outra impede que duas leituras não validadas tenham a mesma autoridade visual
  da única validada. A segunda é a tradução mais difícil do PRD inteiro e foi feita.
- **AD-15 é verdadeiro contra o repositório real** — verifiquei o glob no `.gitignore`. Regras
  cujo `Prevents` cita um artefato concreto e acertam o artefato são raras.
- **As cinco versões da Stack são todas a versão corrente do PyPI hoje.**
- **AD-1 fechou o item que o `state-contract.md` marcava como o único não-aditivo do v1**, e
  o companion foi de fato reescrito — o conflito de fonte mais perigoso da rodada anterior
  está fechado.

O veredito é *adequada* e não mais alto por um motivo específico: **o achado crítico e três
dos cinco altos caem na mesma região** — o que atravessa a fronteira do modelo, o que
atravessa a fronteira `agregacao` → `relatorio`, e o vocabulário que liga sinal a ponto. São
três costuras, não trinta. A spine está a poucas frases de *forte*, e a primeira delas é a
que tira `titulo` do payload.
