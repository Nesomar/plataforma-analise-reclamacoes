---
input: brainstorming/brainstorm-pipeline-agentes-reclamacoes-2026-08-06 (brainstorm-intent.md, spec-tecnico-v1.md, tasks-v1.md, .memlog.md)
alvo: prd.md
data: 2026-08-06
---

# Reconciliação — sessão de brainstorming → PRD

A sessão de brainstorming de 2026-08-06 é a origem do projeto: dela saíram o problema, os dois sinais de risco, a citação obrigatória, as três parcelas do score e o recorte MoSCoW. Este documento registra o que foi decidido, descoberto ou desejado lá e **não sobreviveu até o PRD**.

Detalhe técnico de implementação foi ignorado por decisão registrada: ele vive no `SPEC.md` e nos companions (`state-contract.md`, `risk-signals.md`, `architecture-diagrams.md`, `roadmap.md`). O que segue é lacuna de produto.

**Resumo da travessia.** A espinha estrutural do brainstorming chegou inteira: os dois sinais, a citação obrigatória, a pós-validação determinística, o "LLM extrai, `if` julga", o lote com desmonte na escalada, o contrato de state como único item não-aditivo, o HTML autocontido, a nota de volume ≠ gravidade, a evidência como conteúdo e não metadado. O que se perdeu é quase todo **qualitativo** — postura, ressalva, tom, e o próprio artefato visual — mais uma contradição de métrica que inverte um requisito fundador.

---

## 1. Contradições não registradas

### 1.1 A assimetria falso positivo × falso negativo virou uma métrica simétrica

**No brainstorming.** Requisito declarado na abertura da sessão, antes de qualquer técnica:

> *(decision by user) Erro que doi mais: falso positivo (dizer que tem risco juridico quando nao tem)*

O `brainstorm-intent.md` repete e explica: *"falso positivo dói mais que falso negativo (entope a fila de prioridade e o gestor perde a confiança no relatório)"*. Toda a mecânica de citação obrigatória nasceu como defesa contra esse erro específico — a SÍNTESE 1 da sessão é exatamente isso.

**No PRD.** M-1 é **F1 ≥ 0,85**. F1 é a média harmônica de precisão e recall: pesa os dois erros **igualmente**. Nada no PRD registra que essa simetria foi escolhida no lugar da assimetria fundadora.

**Por que isso é carregado, e não filosofia.** O `risk-signals.md` já traz o caso concreto:

| Regra | Precisão | Recall | F1 |
|---|---|---|---|
| Categoria de dinheiro retido | 88% | 83% | **0,86** — passa em M-1 |
| Categoria + `Status` ≠ Respondida | **100%** | 72% | 0,84 — **reprova em M-1** |

A segunda regra tem **zero falsos positivos** — é literalmente o comportamento que a sessão declarou preferir — e a métrica do PRD a rejeita. Uma execução com 84% de precisão e 89% de recall (o espelho do resultado atual) seria aceita com o mesmo F1, embora a sessão tenha dito que esse é o lado errado da troca.

O SPEC preserva a postura como constraint (*"Falso positivo custa mais que falso negativo"*), mas o PRD é quem define o critério de aceitação — e o critério contradiz a constraint sem dizer que a contradiz.

**Ação sugerida.** Ou registrar a mudança de rumo com o motivo (ex.: "F1 escolhido por comparabilidade; a assimetria é coberta por CM-1"), ou acrescentar um piso de precisão ao lado do F1 (ex.: precisão ≥ 0,88), ou reconhecer que CM-1 sozinha não cobre falso positivo — ela mede **ocupação** da fila, não **corretude** dos itens; uma fila pequena e errada passa nas duas.

---

### 1.2 "Problema central não resolvido" virou "sem urgência"

**No brainstorming.** A fila inflacionada foi o problema em aberto mais destacado da sessão. `.memlog`:

> *(question by coach) PROBLEMA NOVO: 3 de 5 viraram prioridade (60%). Fila onde a maioria e prioridade nao e fila. Colide com o medo original de falso positivo*
> *(insight) SINTESE 4 - O problema dos 60% de prioridade nao foi resolvido na sessao*

E o `spec-tecnico-v1.md` deixou uma instrução de sequência explícita: a troca por níveis com prazo *"deve ser revisitada **antes** de calibrar o corte atual"* — repetida em `tasks-v1.md`: *"Revisitar antes do v2"*.

**No PRD.** Q-3 está fechada: *"A marcação humana ficou em 38%, abaixo do limiar de 40% da CM-1. Binário fica no v1; níveis com prazo seguem no roadmap **sem urgência**."*

**A observação.** O limiar de 40% é criação do próprio PRD (CM-1) — o brainstorming reclamou de 60% sem fixar número. O PRD fechou um problema herdado usando um critério que ele mesmo inventou, e o fechamento não menciona que existia uma instrução de sequência anterior. A decisão pode estar certa (38% medido é bem diferente de 60% estimado), mas a mudança de postura — de "problema central em aberto" para "sem urgência" — não está registrada como mudança. `roadmap.md` ainda carrega a instrução original ("decidir antes de calibrar o corte"), o que deixa os dois documentos em desacordo de tom.

**Nota lateral, do mesmo fio.** O `.memlog` define risco jurídico como *"classificacao para priorizar quais reclamacoes atender mais rapido (**fila/SLA**)"*. A noção de **tempo** desapareceu inteira do PRD: a fila ordena, mas nada no produto diz "este item tem X horas". Os níveis com prazo do v2 são justamente o que devolveria isso.

---

### 1.3 O `id` mudou de dono, e a consequência de produto não foi registrada

**No brainstorming.** `id` estável **derivado do texto** (`hash(texto)` truncado), com um teste dedicado (tarefa 5: "mesma entrada, duas execuções, mesmos `id`s").

**No PRD.** FR-3 e a tabela de falhas: identificador **vem do arquivo**, e *"a unicidade é garantia do arquivo, não do sistema"*.

A troca é justificada — a base real traz `ID_Reclamacao` único, e um hash de texto colidiria de propósito nas 20 linhas de texto repetido. Ela está documentada em `state-contract.md`. **O que não está registrado é a consequência de produto:** com `id` de origem, o sistema deixa de ter qualquer noção de que dois relatos são textualmente idênticos. O PRD nem trata isso como problema (deduplicação não aparece) nem como decisão (não há linha dizendo "textos repetidos são analisados e contados como reclamações distintas, de propósito"). NFR-7 continua prometendo estabilidade de identificador entre execuções — o que agora é trivialmente verdadeiro e não testa mais nada.

---

## 2. Ideias qualitativas que a estrutura numerada apagou

### 2.1 O relatório perdeu os gráficos

Este é o apagamento mais nítido da travessia.

**No brainstorming**, o visual é o produto:

- MoSCoW MUST: *"HTML **com os gráficos**"*
- `spec-tecnico-v1.md` §6: *"Gráficos: SVG inline gerado em Python ou matplotlib embutido como base64. Nada externo."*
- `tasks-v1.md` #15: *"HTML único autocontido. Gráficos SVG inline ou matplotlib em base64. Zero CDN."*
- `.memlog`: *"Relatorio = APENAS representacao **visual** dos resultados"*

**No PRD**, a seção 3.3 tem seis requisitos — arquivo único (FR-9), fila primeiro (FR-10), citação visível (FR-11), nota de volume (FR-12), data e total (FR-13), pt-BR (FR-14). **Nenhum deles pede um único gráfico.** A palavra não aparece no documento. O que sobreviveu de *"apenas representação visual"* foi só a metade negativa da frase, migrada para a seção 8: *"não filtra, não ordena, não exporta"*.

O PRD manteve a restrição e perdeu a coisa restringida. Um relatório que cumprisse os catorze FRs à risca poderia ser uma tabela de texto puro.

**Ação sugerida.** Um FR na 3.3: distribuição de sentimento e ranking de produtos apresentados como gráfico embutido no arquivo, sem requisição de rede (o "sem CDN" já está coberto por FR-9).

### 2.2 A ressalva jurídica sumiu do documento inteiro

**No brainstorming**, é a última seção do `brainstorm-intent.md`, isolada e com título próprio:

> **Ressalva** — *Os padrões de risco jurídico aqui são heurísticas de engenharia, não parecer jurídico. Adequado para projeto de estudo; produção exigiria validação por profissional habilitado.*

**No PRD**, ausente. Não está em §1 (Contexto), não é NFR, não é requisito do relatório, não é questão aberta. Sobrevive apenas como constraint no `SPEC.md` — um documento que o gestor nunca verá.

A assimetria é o que incomoda: o PRD **exige por requisito** (FR-12) que o relatório avise ao leitor que volume ≠ gravidade — uma ressalva menor — e não pede nada equivalente para a ressalva grave. O leitor definido em §2.2 é um gestor que abre uma seção chamada fila de risco jurídico e age a partir dela, e nada no produto lhe diz que aquilo é heurística de engenharia.

**Ação sugerida.** Um FR irmão do FR-12 na §3.3, ou uma linha em §1 registrando que a ressalva é deliberadamente deixada fora da saída visível.

### 2.3 A leitura de percepção de marca virou um número

**No brainstorming**, o sentimento não era um gráfico de pizza: `spec-tecnico-v1.md` §6.2 pede *"distribuição, **e a leitura de percepção de marca**"* — a distribuição mais o que ela significa.

**No PRD**, o sentimento aparece só como campo em FR-5 (extração) e como M-5 (métrica: *"uma pessoa que nunca viu a base consegue dizer... como o cliente se sente com a marca"*). Existe a **medição** de que o leitor entendeu, e não existe o **requisito** do que o produz. M-5 mede uma qualidade que nenhum FR encomenda.

### 2.4 O cabeçalho perdeu período e empresa

`spec-tecnico-v1.md` §6.1 pedia no cabeçalho: *"total de reclamações, **período**, **empresa(s)**"*. FR-13 ficou com data da execução e total.

Não é cosmético nesta base: são **14 empresas fictícias** consolidadas num relatório só, e o `SPEC.md` registra como assumption que *"nada define se a análise é por empresa ou agregada"*. O leitor Ricardo, de §2.2, abre um relatório que mistura queixas de catorze empresas e nada na tela lhe diz isso. O período coberto tem o mesmo problema: FR-13 informa **quando o relatório foi gerado**, não **que janela de tempo ele cobre** — e a base se espalha por 2026 inteiro.

### 2.5 O "estudo" virou "portfólio", e nenhuma métrica olha para ele

**No brainstorming**, a primeira linha do `brainstorm-intent.md`: *"Natureza do projeto: **estudo**. O aprendizado de arquitetura multi-agente é o **entregável**, não um meio."* Reforçado no `.memlog`: *"LangGraph no v1 nao e overhead apesar de o fluxo ser simples — o objetivo declarado e ESTUDO, entao o LangGraph e o proprio entregavel"*.

**No PRD** §1: *"Peça de portfólio... o problema foi escolhido por ser real o bastante para que o aprendizado seja real."* A mudança de enquadramento está registrada no `.memlog` do PRD (*"Stakes: PORTFOLIO"*) e é legítima.

O que não acompanhou: **das cinco métricas de sucesso (M-1 a M-5), nenhuma olha para o entregável declarado.** Todas medem a qualidade da saída do produto. Se o objetivo primário é a arquitetura, o PRD não tem critério para dizer se ele foi atingido — o que fica estranho num documento que define "avaliador técnico" como parte do público.

---

## 3. Preocupações levantadas e não endereçadas

### 3.1 A premissa não testada continua não testada — e agora há evidência contra ela

`.memlog` da sessão, logo na primeira técnica:

> *(insight by coach) Premissa nao testada: "varios agentes especializados = analise melhor". Assumida, nunca verificada*

A medição posterior a derrubou nesta base: regra determinística e Gemini Flash empatam em F1 0,86, com **zero divergências item a item**, e `risk-signals.md` conclui sem rodeios: *"o LLM não se paga aqui... o pipeline de agentes é infraestrutura cara para um resultado que um `in` entrega."*

O PRD **registra o fato** (a nota sob M-1: *"o LLM não superou a regra nesta base"*) e **não tira consequência dele**. Não há métrica, contramétrica ou questão aberta perguntando se o pipeline agrega valor sobre a baseline determinística. Um avaliador técnico que ler o `risk-signals.md` chega nessa conclusão sozinho; melhor o PRD chegar primeiro — o enquadramento honesto ("a arquitetura é o entregável, o ganho de acurácia não é a tese") desarma a crítica, e ele existe na origem (§2.5 acima).

### 3.2 O corpus de 5 reclamações deixou de ser o gabarito — e Q-4 é a fatura disso

`tasks-v1.md` #2 é categórico: o corpus de 5 reclamações escrito na sessão *"é o gabarito do projeto inteiro"*. Dele saíram, por observação direta, os dois sinais, as três parcelas do score e o teste que a sessão chamou de *"o único teste que sabe se o sistema concorda com um humano"*.

O corpus **sobreviveu** — como seção final do `risk-signals.md` ("Gabarito de aceitação", reclamações 2, 3 e 4 na fila). Mas **nenhuma métrica do PRD o usa**: M-1 mede exclusivamente contra `docs/gabarito.csv` (50 linhas sintéticas).

A consequência aparece na própria Q-4 do PRD, marcada como *"a decisão que separa um sistema honesto de um sistema decorativo"*: ameaça explícita, dano continuado e registro contraditório não são validáveis *"com os dados disponíveis"*. Mas o corpus da sessão exercita duas das três de propósito — a reclamação 2 (FastDelivery: sistema diz entregue, cliente tem rastreio) **é** o caso canônico de registro contraditório, e foi ela que revelou essa parcela; 3 e 4 são os casos de dano continuado. Os dados existem; eles só não estão dentro da métrica.

**Ação sugerida.** Q-4 tem uma saída barata que o PRD não considera: manter o corpus de 5 como conjunto de referência complementar em M-1, o que converte "parcela não exercida" em "parcela exercida por caso construído, não por incidência na base real" — uma afirmação bem mais honesta que qualquer um dos dois lados que Q-4 apresenta.

### 3.3 Riscos deferidos cujo texto de alerta sobreviveu só no roadmap

Três alertas do brainstorming continuam sem endereço no PRD porque os itens que os geram estão fora do v1. Estão em `roadmap.md`, o que é o lugar certo — registrados aqui só para fechar a varredura:

- loop de crítica sem `max_iteracoes` = loop infinito (*"o critico foi escolhido mas nunca foi definido O QUE o critico avalia"* segue sem resposta);
- upload síncrono não sobrevive ao timeout HTTP, exige job assíncrono;
- chave de cache com três campos, sob pena de envenenamento ao primeiro ajuste de prompt.

---

## 4. Essencial no brainstorming, fora de escopo no PRD — legítimo

Registrado sem crítica: em todos os casos a mudança tem rastro em `SPEC.md` (Non-goals) e `roadmap.md`.

| Item | Origem na sessão | Onde está agora |
|---|---|---|
| Cascata Flash → Pro | grade morfológica, linhas D e G | roadmap v2 |
| Cache de chamadas | *"requisito novo"* levantado pelo usuário | roadmap v2 |
| Níveis de criticidade | proposto pelo coach, aprovado no MoSCoW | roadmap v2 (ver §1.2 sobre o tom) |
| Interface com upload de CSV | *"requisito novo"* levantado pelo usuário | roadmap v3 |
| Guard-rails entrada/saída | grade morfológica, linha E; parte da arquitetura que o usuário pediu no início | roadmap v3 |
| Loop de crítica | grade morfológica, linha B | roadmap v3 |
| Checkpoint persistido | grade morfológica, linha H | roadmap v3 |
| Agente normalizador de CSV | ideia do usuário na abertura | derrubada **dentro** da própria sessão (WON'T) |
| Relatório para "qualquer pessoa da empresa" | primeira decisão da sessão | substituída ainda na sessão por "gestores" |

O único aqui que merece nota: **guard-rails** e **normalizador de CSV** eram, na abertura, a *arquitetura desejada pelo usuário* (*"agente normalizador + agente de guard-rails + agente processador"*). A sessão inteira reescreveu essa intenção, e o PRD herda o resultado, não o pedido original. Está correto — mas é a distância mais longa percorrida entre o que foi pedido no minuto zero e o que está especificado hoje.

---

## 5. Prioridade sugerida

| # | Lacuna | Tipo | Custo de corrigir |
|---|---|---|---|
| 1 | F1 simétrico contradiz "falso positivo dói mais" | contradição | baixo — um piso de precisão em M-1 |
| 2 | Nenhum FR pede gráfico no relatório | qualitativo | baixo — um FR em 3.3 |
| 3 | Ressalva jurídica ausente do PRD e da saída | qualitativo / risco | baixo — um FR ou uma linha em §1 |
| 4 | Corpus de 5 fora das métricas, enquanto Q-4 pede justamente ele | preocupação | médio — reabre Q-4 com terceira opção |
| 5 | Percepção de marca medida (M-5) sem requisito que a produza | qualitativo | baixo |
| 6 | Cabeçalho sem período e sem empresa(s), com 14 empresas na base | qualitativo | baixo |
| 7 | "Sem urgência" na fila binária sem registro da virada de postura | contradição | baixo — uma frase em Q-3 |
| 8 | Nenhuma métrica olha para o entregável declarado (a arquitetura) | qualitativo | médio |
| 9 | Premissa "mais agentes = melhor" derrubada e sem consequência no PRD | preocupação | baixo |
| 10 | `id` de origem removeu a noção de texto duplicado, sem registro | contradição | baixo |
