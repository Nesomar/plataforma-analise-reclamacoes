# Epic 1 Context: O operador roda a base e sabe se pode confiar no resultado

<!-- Generated from planning artifacts. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Entregar o pipeline de análise verificada ponta a ponta na linha de comando: o operador aponta o comando para um CSV de reclamações e, ao encerrar, recebe quatro números honestos — lidas, analisadas, não analisadas e códigos de sinal derrubados na verificação de evidência. Cada reclamação recebe sentimento, produto e sinais de risco, e todo sinal que sobrevive carrega uma citação literal conferida contra o texto original por comparação de string. A falha de um lote não derruba os demais: vira registro contabilizado e a execução segue. Este épico é standalone — ele constrói o contrato de estado, o catálogo, a ingestão, a análise, a verificação e a orquestração, sem depender do relatório HTML do Épico 2.

## Stories

- Story 1.1: Contrato de estado e catálogo de sinais
- Story 1.2: Configuração validada antes de qualquer chamada paga
- Story 1.3: Ingestão que rejeita base inválida antes de gastar
- Story 1.4: Verificação de evidência determinística
- Story 1.5: Análise de um lote pelo modelo
- Story 1.6: Fan-out por lote com falha absorvida
- Story 1.7: As quatro contagens do operador

## Requirements & Constraints

**Execução e feedback.** O caminho do CSV chega como argumento de linha de comando (nada embutido em código); invocar sem argumento encerra com mensagem de uso. Ao encerrar, o terminal imprime total lido, total analisado, total não analisado e total de códigos de sinal derrubados. O total não analisado conta *reclamações afetadas*, não eventos de falha — a contagem de eventos também fica disponível. O total de derrubados conta *códigos distintos* que tiveram ao menos um sinal reprovado.

**Rejeição antes de gastar.** Coluna ausente, schema divergente, identificador duplicado ou CSV sem linhas encerram a execução com a causa nomeada e zero chamadas ao modelo. Tamanho de lote fora da faixa permitida também encerra antes de qualquer chamada paga.

**Análise.** Cada reclamação recebe sentimento (`positivo`/`neutro`/`negativo`), produto (`str | None`) e sinais de risco. Todo sinal exige citação literal com piso de cinco palavras; sem isso não é registrado. A verificação confirma que cada citação existe no texto original antes de o resultado entrar no estado, e derruba o código específico que aquela citação sustentava — não o conjunto de sinais da reclamação.

**Confiabilidade.** Falha em uma reclamação ou lote não interrompe os demais; a afetada é registrada e contabilizada. A resposta do modelo é casada por identificador, nunca por posição: id faltante vira falha carregando aquele id; id repetido ou inventado é descartado e não soma a agregado nenhum. Resposta fora do schema é falha de conteúdo, não exceção que aborta. Duas execuções sobre o mesmo arquivo produzem os mesmos identificadores.

**Fronteira de falha.** Falha de conteúdo é absorvida e contabilizada; falha de infraestrutura encerra sem escrever nada, com a causa nomeada (indisponibilidade *versus* credencial ausente, nunca mensagem genérica) e informando quantos lotes haviam concluído. Zero análises encerra com causa nomeada e não escreve arquivo.

**Configuração e credencial.** Tamanho de lote e modelo vêm de variável de ambiente com default no código, via `python-dotenv`; sem variáveis definidas a execução segue nos defaults. A chave de API é lida exclusivamente de variável de ambiente — nenhuma credencial em código, teste ou repositório — e o arquivo de exemplo lista apenas nomes, sem valores.

**Aceitação manual.** A execução sobre a base de referência reportando 50 lidas / 50 analisadas / 0 não analisadas exige rede e crédito: é a única verificação do épico fora da suíte determinística.

## Technical Decisions

**Paradigma.** Pipes-and-filters sobre estado compartilhado explícito, com exatamente um filtro impuro. Cada etapa é função do estado para um delta; nenhuma muta o estado que recebeu. Módulos e funções em português; nós do grafo nomeados pelo verbo da etapa.

**Isolamento da rede.** Somente o módulo de análise importa o SDK do modelo, direta ou transitivamente, e o cliente é construído dentro da função do nó, nunca em escopo de módulo — importar qualquer módulo do pacote deve funcionar sem credencial. Verificável por inspeção de import. Única exceção à regra de que nenhum filtro importa outro: o módulo de análise importa o de evidência, porque a verificação roda sobre a resposta do modelo antes de o delta entrar no estado. Consequência de ordenação: implemente evidência antes de análise.

**Contrato de estado.** Vive em módulo próprio que não importa nenhum outro módulo do pacote, todo tipado por `TypedDict`. O sinal é par indivisível `{codigo, citacao, valida}` — não existem listas paralelas de código e evidência, nem campo booleano à parte para ameaça explícita. `valida` é `bool` com default `False`, nunca `bool | None`. `Motivo.origem` é `Literal["sinal", "atributo"]`, com citação não nula se e somente se a origem for `sinal`; nenhuma etapa converte uma origem na outra. `Falha` carrega ids afetados, causa e nó. As listas de análises e falhas são anotadas com o redutor de soma, que é a mecânica de merge do fan-out; toda chave do estado tem exatamente um nó que a escreve.

**Catálogo.** Seis códigos em módulo único, fonte tanto do construtor do prompt quanto da pontuação — nenhum código de sinal como literal solto em outro módulo. Sinal A (intenção jurídica, grupo declarado como saturado): `ameaca_explicita`, `lei_citada`. Sinal B (exposição factual): `dinheiro_retido`, `registro_contraditorio`, `dano_continuado`, `prazo_estourado`. Cada código exige definição escrita com exemplo dentro do prompt — é o maior fator isolado de acurácia. `dinheiro_retido` cobre as seis situações em que a empresa está com dinheiro do cliente. O mesmo módulo declara a lista canônica de termos genéricos de produto.

**Fronteira do modelo.** O payload carrega apenas `id` e `texto`. Empresa e título ficam fora *por construção*, não por instrução no prompt — o título entregaria a resposta e faria o modelo reproduzir a linha de base. A saída vem por schema de resposta do SDK, derivado das estruturas do contrato de estado; nunca parsing de texto livre. O produto volta como o modelo leu, sem julgamento de genérico; `produto = None` significa apenas *o texto não permitiu identificar*.

**Verificação de evidência.** Determinística, sem rede. Substring exata contra o texto original e piso de cinco palavras conferidos no mesmo lugar. Citação vazia reprova, apesar de ser substring de qualquer texto. Uma citação reprovada derruba o código inteiro, inclusive os pares do mesmo código que passaram.

**Fan-out.** O nó de carga fatia a base e emite um despacho por lote; nenhum lote lê o resultado de outro. Repetição de transporte é política declarada no registro do nó, não laço dentro do código do nó; o tratador de erro no mesmo registro é obrigatório e é quem produz o registro de falha com os ids do lote — sem ele, o retry esgotado aborta o grafo inteiro. Tamanho de lote tem piso 2 e teto 25, validados na carga da configuração, e a validação recai sobre os lotes efetivamente emitidos: lote residual de tamanho 1 é fundido ao anterior, porque chamada individual por reclamação é proibida. Após o gather, uma asserção verifica a conservação: reclamações lidas igual a análises mais a soma dos ids em falhas.

**Convenções.** CSV lido com `utf-8-sig` e separador `;` (UTF-8 cru cola BOM no nome da primeira coluna); sete colunas esperadas; datas em ISO-8601 no estado, com `DD/MM/AAAA` apenas na fronteira de leitura. Identificador vem da origem e é validado único na ingestão. Observabilidade é a saída do operador ao encerrar — não há log estruturado, métrica exportada nem trace.

**Testes.** Tudo que o modelo não decide é testável sem o modelo: as funções puras são alimentadas por análises fabricadas à mão e nenhum teste faz chamada de rede. A suíte roda sem a variável de chave de API definida. A verificação de citação falsa e as parcelas que a base real nunca exercita precisam de caso construído à mão — a suíte é a única coisa que as executa.

**Stack fixada.** Python ≥3.11 · langgraph 1.2.10 · google-genai ≥2.17.0 · modelo `gemini-3.6-flash` · jinja2 3.1.6 · python-dotenv ≥1.2.2 · pytest 9.1.1. Sem starter template: o repositório já existe e o trabalho é criar o pacote do zero dentro dele.

## Cross-Story Dependencies

- **1.1 é base de tudo.** Contrato de estado e catálogo são importados por ingestão, análise, evidência e (no Épico 2) pontuação e agregação.
- **1.4 antes de 1.5.** A análise importa a verificação de evidência, porque a citação é conferida antes de o delta entrar no estado. Implementar evidência primeiro, contra o resto da ordem alfabética/natural dos módulos.
- **1.2 antes de 1.6.** A validação da faixa de tamanho de lote é o que torna o fatiamento e o fan-out legais; ela precisa encerrar antes de qualquer chamada paga.
- **1.3 antes de 1.6.** Quem fatia e emite os despachos é o próprio nó de carga.
- **1.6 antes de 1.7.** As quatro contagens leem análises e falhas produzidas pelo fan-out; a asserção de conservação vale sozinha neste épico e não depende da pontuação, que só existe no Épico 2.
- **FR-1 é partido entre épicos.** A metade que aceita o caminho do CSV como argumento fica na Story 1.7; escrever, nomear e imprimir o caminho do HTML é responsabilidade da Story 2.6.
- **O Épico 2 consome este.** Pontuação, agregação e relatório dependem de `analises`, `falhas` e do contrato de estado produzidos aqui; nada deste épico depende deles.
- **O Épico 3 mede o que aqui foi construído** (precisão/recall da fila, tempo, custo, extensibilidade) e não é pré-requisito de nenhuma story deste épico.
