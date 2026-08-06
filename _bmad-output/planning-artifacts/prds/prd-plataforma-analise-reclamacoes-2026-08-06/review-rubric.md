# PRD Quality Review — Plataforma de Análise de Reclamações

Revisado em 2026-08-06 contra `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`.
Companions do SPEC lidos como contexto (`SPEC.md`, `risk-signals.md`, `state-contract.md`, `roadmap.md`) — a ausência de `addendum.md` é decisão registrada e a não-duplicação **não** é tratada como lacuna neste review.

## Veredito geral

Este é um PRD honesto e bem calibrado à sua forma: duas personas que puxam requisitos de verdade, contramétricas que já dispararam alerta antes de o produto existir, e uma seção de falha que trata o caminho triste como entregável. O que sustenta o documento é a disposição de registrar resultado desfavorável — M-1 declara que "o LLM não superou a regra nesta base" e CM-2 lê o zero como suspeita, não como vitória. O que está em risco é a ponte para jusante: sem glossário, com dois substantivos de domínio em deriva (sinal/evidência/citação, falha/não analisada) e com duas capacidades do SPEC cobertas mas não etiquetadas, quem for escrever histórias a partir daqui vai reconstruir vocabulário em vez de extrair. E o objetivo declarado do projeto — dominar arquitetura multi-agente, com "um avaliador técnico" no público — não tem nenhuma métrica em §7.

## Decision-readiness — forte

O PRD decide, e decide à vista. Q-1, Q-3, Q-6 e Q-7 aparecem tachadas com a data e **com a medição que as resolveu** — Q-6 não diz "decidimos não usar `Status`", diz "`Status` sozinho tem F1 0,42, pior que a categoria do problema", e nomeia o que sobrou dele ("entra como modificador negativo dentro da categoria certa"). Q-3 nomeia o que foi abandonado junto: "Binário fica no v1; níveis com prazo seguem no roadmap sem urgência". Isso é trade-off com o preço declarado, não escolha que equilibra tudo.

As questões que ficaram abertas são abertas de fato. Q-4 não tem resposta na frase seguinte — tem o custo da indecisão em negrito: *"É a decisão que separa um sistema honesto de um sistema decorativo."* Q-2 lista três saídas concretas (categoria visível, omitida mas contada, sinalizada ao operador) sem sinalizar preferência.

Não há callouts `[NOTE FOR PM]` em lugar nenhum. Para um projeto solo em que o PM é o operador, §9 faz esse trabalho e a ausência não é achado. O que falta é força de decisão: Q-4 é reconhecida como a questão mais cara do documento e não tem gatilho, prazo, nem comportamento default se ninguém decidir.

### Findings
- **medium** Resultado que contradiz o meio, sem o ponteiro que o resolve (§7.1, M-1) — o PRD registra que a regra determinística e o Gemini "empatam em F1 0,86, com zero divergências item a item" e para aí. Quem lê só o PRD encontra a medição de que o mecanismo central do produto é dispensável e nenhuma resolução; a decisão existe, mas mora na restrição do SPEC *"LangGraph é obrigatório, mesmo com fluxo linear. É o objeto de estudo, não o meio"*. *Fix:* uma cláusula em M-1 remetendo à restrição do SPEC, deixando explícito que o empate não reabre a escolha de arquitetura — e o que reabriria.
- **medium** Q-4 sem função de forçamento (§9) — a questão declarada como a mais consequente do documento não tem prazo, gatilho de decisão nem default. Como está, ela sobrevive ao v1 por inércia e as quatro parcelas não exercidas entram no código sem que ninguém tenha decidido nada. *Fix:* anexar a Q-4 o momento em que ela vence (ex.: antes do primeiro run sobre base não sintética) e o default se chegar lá indecidida.

## Substância sobre teatro — forte

Nada aqui é mobília. As duas personas puxam requisitos opostos e o PRD diz isso na cara: *"Dois papéis distintos, com necessidades opostas. Confundi-los é o erro mais provável do projeto."* O operador gera FR-1, FR-2, FR-3; o leitor gera FR-9, FR-10, FR-11, FR-14 — e a proibição de rede em FR-9 é consequência direta de *"Nunca instala nada, nunca vê terminal, nunca tem a chave de API"*. Duas personas, ambas carregando peso.

Não há seção de diferenciação, não há visão, não há mercado — corretamente, para a forma. Os NFRs têm número e são específicos deste produto: NFR-1 amarra 2 minutos a 50 reclamações, NFR-3 amarra custo ao free tier, NFR-6 proíbe casamento posicional, NFR-7 separa o que pode variar entre execuções (classificação) do que não pode (identidade). Nenhum "o sistema deve ser escalável".

O §1 vai além do que a maioria dos PRDs admite: volunteia a limitação do corpus que enfraquece toda medição do próprio documento — *"as descrições se repetem (30 textos distintos em 50 linhas), o que faz qualquer acurácia medida aqui superestimar o desempenho sobre linguagem real"*. Sem achados.

## Coerência estratégica — adequada

A tese do produto existe e é defendida pela ordenação: o valor é a fila justificada com evidência à vista, não o painel. FR-10 põe a fila antes de qualquer agregado, FR-11 exige a citação *"como conteúdo visível e não como detalhe expansível"*, e FR-12 desinfla o próprio ranking de produtos dentro do relatório (*"volume não equivale a gravidade"*). Três requisitos que são a tese expressa como hierarquia de tela. As contramétricas atacam exatamente o modo de falha da tese: CM-1 mede se a fila parou de ordenar (*"virou uma lista com adjetivo"*), com limiar numérico e leitura já medida em 38%.

Onde a coerência trinca é entre §1 e §7. §1 declara o propósito do projeto — *"O objetivo declarado é dominar arquitetura de pipeline multi-agente com LangGraph sobre Gemini"* — e nomeia um terceiro público: *"Um avaliador técnico é parte do público."* §2 modela dois papéis e o avaliador some. §7 traz cinco métricas e quatro contramétricas, todas sobre o produto. O projeto pode bater M-1 a M-5 inteiras e falhar no objetivo que ele mesmo declarou como primário, sem que nenhum número em §7 mude de cor.

### Findings
- **high** Objetivo declarado do projeto sem critério de sucesso (§1 "Natureza do projeto" vs §7) — o propósito primário do documento (domínio da arquitetura multi-agente) e o terceiro público (avaliador técnico) não têm métrica, contramétrica nem requisito. Num artefato de portfólio, é o objetivo que mais importa e o único sem verificação. *Fix:* uma métrica em §7 sobre o que o avaliador técnico deve conseguir concluir do repositório (ex.: reconstruir o fluxo do grafo a partir de `architecture-diagrams.md` sem ler código), ou uma linha em §8 declarando explicitamente que o sucesso de aprendizado não é medido neste PRD.
- **medium** Duas contramétricas sem linha de base, na mesma execução que mediu as outras duas (§7.2) — CM-1 e CM-2 trazem *"Medida em 2026-08-06"* com número; CM-3 (produto não identificado) e CM-4 (não analisadas por falha) descrevem só a direção do perigo. A execução que produziu os números de M-1 sobre as 50 reclamações necessariamente produziu esses dois valores também. Sem a leitura inicial, "subindo" não tem de onde subir — e CM-3 é justamente o que decide Q-2. *Fix:* registrar as duas leituras de 2026-08-06 e, em CM-3, o limiar a partir do qual o ranking é declarado sem significado.

## Clareza de done — adequada

A maioria dos FRs tem consequência testável e vários carregam a razão junto, o que é raro e útil: FR-2 lista os quatro números exatos a reportar e explica por quê (*"Sem isso o operador não distingue uma execução limpa de uma execução silenciosamente degradada"*). FR-3 nomeia as três causas de rejeição e ancora o formato em `state-contract.md`. FR-6 e FR-7 são binários e verificáveis por comparação de string. A tabela de §6 é o ponto mais forte do documento em done-ness: oito modos de falha, cada um com comportamento nomeado e amarrado a um FR/NFR.

Sobram três predicados sem limite e um conflito interno. FR-1 pede *"caminho previsível"* e FR-4 pede que sobrescrita não aconteça *"sem que isso seja evidente ao operador"* — os dois são satisfeitos por implementações incompatíveis (caminho fixo é previsível e sobrescreve; caminho com timestamp não sobrescreve e não é previsível), e nenhum dos dois define o predicado. M-5 é a única métrica sem procedimento. NFR-8 fala em sobreviver ao e-mail sem citar o limite de tamanho — e como FR-9 exige arquivo único autocontido, o tamanho é exatamente a variável que decide se NFR-8 passa.

### Findings
- **high** FR-1 e FR-4 em tensão, ambos com predicado aberto (§3.1) — *"caminho previsível"* e *"sem que isso seja evidente ao operador"* não são condições verificáveis, e as leituras naturais de um contradizem o outro. Um engenheiro escolhe entre sufixar timestamp, perguntar antes, ou apenas avisar — três produtos diferentes, os três "conformes". *Fix:* fixar a regra de nome do arquivo em FR-1 e converter FR-4 na consequência observável escolhida (ex.: "existindo arquivo de mesmo nome, o sistema aborta e informa o caminho em conflito").
- **medium** Retry de rate limit sem teto, contra um NFR com relógio (§6, linha "Limite de taxa da API atingido") — *"Aguarda e repete a chamada; se persistir, encerra"* não define espera nem número de tentativas, enquanto NFR-1 fixa 2 minutos ponta a ponta. A linha, como escrita, pode violar NFR-1 sem violar a si mesma. *Fix:* nomear tentativas máximas e espera máxima, e declarar se o orçamento de 2 minutos de NFR-1 inclui ou exclui a espera por rate limit.
- **medium** M-5 sem procedimento nem condição de aprovação (§7.1) — *"Uma pessoa que nunca viu a base consegue dizer..."* não diz quem é a pessoa, que pergunta é feita, quantas pessoas, nem o que conta como acerto. É a única das cinco métricas que não pode ser lida de um número. *Fix:* fixar o protocolo mínimo (uma pessoa, duas perguntas fechadas, acerto em ambas) ou rebaixar M-5 a critério qualitativo declarado como tal.
- **medium** NFR-8 sem o limite que o decide (§4.4) — *"sobrevive a ser encaminhado por e-mail como anexo único"* depende do tamanho do HTML, que FR-9 empurra para cima ao exigir zero requisição de rede. Nenhum teto de bytes aparece no documento. Idem *"navegador atual"*, sem lista. *Fix:* teto de tamanho do arquivo em NFR-8 e a família de navegadores tratada como alvo.

## Honestidade de escopo — forte

§8 faz trabalho real: nomeia as quatro omissões que um leitor assumiria em silêncio (sem filtro/ordenação para o leitor, sem autenticação, sem histórico entre execuções, sem agendamento) e uma delas é admitida como fraqueza em vez de embrulhada — *"o controle de acesso é o e-mail que carrega o anexo"*. A seção também aponta para `SPEC.md` e `roadmap.md` em vez de repetir, coerente com a decisão registrada.

A governança de dados em §5 é honestidade de escopo em forma de requisito: DG-3 antecipa que o próprio produto vaza dado pessoal quando roda sobre base real, porque FR-11 obriga citação literal na tela. Poucos PRDs derivam a consequência incômoda do seu próprio requisito estrela.

Densidade de itens abertos: três questões efetivamente abertas (Q-2, Q-4, Q-5), quatro resolvidas mantidas com data, um `[ASSUMPTION]` inline. Para portfólio, saudável — não é bloqueio.

O único ponto em que o PRD assume sem marcar é o recorte por empresa.

### Findings
- **medium** Recorte por empresa assumido sem tag (§2.2, UJ-2) — o SPEC lista como premissa **aberta**: *"O relatório consolida a base inteira, sem filtro por empresa. A base contém 14 empresas distintas e nada define se a análise é por empresa ou agregada."* O PRD constrói o leitor sobre um dos ramos: Ricardo é "gestor", lê uma fila e *"encaminha aquele caso para o time de cobrança"* — o que só faz sentido se a fila for de uma empresa só, enquanto a base tem 14. Nem §9 nem um `[ASSUMPTION]` registra a escolha. *Fix:* tag `[ASSUMPTION]` em §2.2 declarando o recorte adotado, ou uma Q-8 espelhando a premissa aberta do SPEC.

## Usabilidade downstream — rala

É a dimensão mais fraca, e importa aqui: o PRD é topo de cadeia com SPEC ao lado e implementação já iniciada (`baseline.py`, `classificador.py`).

Não há glossário, e a deriva já aconteceu dentro do próprio documento. "Sinal de risco" (FR-5, FR-6) vira "sinal" (FR-7, CM-2); "citação" (FR-6, FR-7, FR-11) vira "evidência" no título de M-2 (*"Integridade da evidência"*) e é `evidencia` no `state-contract.md`; e o contador de falhas aparece com três nomes — FR-2 pede *"total com falha"*, NFR-5 diz *"registrada como não analisada"*, CM-4 mede *"Reclamações não analisadas por falha"*. Quem escrever a história de FR-2 tem de adivinhar se são um campo ou dois.

A convenção "Realiza CAP-x" é aplicada em FR-3, FR-5, FR-6, FR-7 e FR-9, e some justamente nos requisitos de fila e ranking. Uma varredura SPEC→PRD acusa CAP-6 e CAP-7 sem cobertura quando elas estão cobertas por FR-10/FR-11 e FR-12 — o pior tipo de falso negativo, porque é a própria convenção que gera a leitura errada.

O que funciona: IDs contíguos e únicos em todas as famílias (FR-1..14, NFR-1..9, DG-1..5, M-1..5, CM-1..4), as duas UJs com protagonista nomeado carregando contexto inline, e todas as referências a arquivo resolvendo (`docs/gabarito.csv`, `docs/gabarito-v1.csv`, `docs/reclamacoes_reclameaqui.csv`, os três companions citados existem). §6 referencia FR/NFR por ID em vez de "ver acima".

### Findings
- **high** Sem glossário, com deriva já instalada (documento inteiro) — três pares em uso intercambiável (sinal de risco/sinal; citação/evidência; com falha/não analisada) atravessam FRs, NFRs, métricas e a tabela de falha. Extração automática por termo de domínio produz conjuntos diferentes conforme o sinônimo escolhido. *Fix:* seção de glossário com os termos de fronteira (reclamação, sinal de risco, citação, fila de prioridade, produto não identificado, reclamação não analisada) e um passe de uniformização — em especial fixar um único nome para o contador de FR-2/NFR-5/CM-4.
- **medium** CAP-6 e CAP-7 cobertas mas não etiquetadas (§3.3) — FR-10 e FR-11 realizam CAP-6 (Priorização) e FR-12 realiza CAP-7 (Agregação), sem a tag "Realiza" que os outros FRs usam. Rastreabilidade SPEC→PRD aponta duas capacidades órfãs que não são órfãs. *Fix:* aplicar as tags em FR-10, FR-11 e FR-12.
- **low** UJs desconectadas dos requisitos (§2) — nenhum FR referencia UJ-1 ou UJ-2 e as UJs não citam IDs. Elas são bem escritas e coerentes com os FRs, mas a ligação é implícita. *Fix:* citar os FRs em cada UJ, ou os IDs de UJ nos requisitos que elas motivam.

## Fit de forma — forte

A forma está certa e as escolhas foram feitas, não herdadas do template. Ferramenta de operador único com um segundo leitor real: duas UJs — nem uma por FR (super-formalização), nem zero (o que quebraria, porque o requisito de arquivo único autocontido deriva justamente da jornada do leitor que "nunca instala nada"). Nenhuma persona sobrando, nenhuma seção de mercado, nenhum roadmap duplicado.

As duas seções fora do menu padrão se pagam. Governança de dados existe porque o concern é real e específico — repositório público, relato de consumidor com protocolo e referência a conta bancária, API de terceiro — e DG-1 traz verificação datada contra o arquivo, não promessa. Comportamento em falha existe porque *"Um sistema de portfólio é avaliado tanto pelo que faz quando funciona quanto pelo que faz quando não funciona"*, e a tabela cumpre a premissa.

A não-duplicação com o SPEC está executada de forma consistente: o PRD nunca reenuncia capacidade, restrição ou contrato de estado, e o cabeçalho declara a divisão de trabalho em uma frase. Sem achados.

## Notas mecânicas

- **Deriva de número entre PRD e SPEC.** O PRD (Q-3, Q-7) e `risk-signals.md` dizem gabarito v2, **19 de 50, 38%**. `SPEC.md` §Resolved ainda diz *"o julgamento humano marcou 36% da base"* (linha 107) e *"`docs/gabarito.csv`, 18 de 50"* (linha 110). O `.memlog.md` registra a correção ("Q-7 e Q-3 corrigidas: gabarito v2 tem 19 de 50 (38 por cento)"), mas ela não chegou ao SPEC. Quem ler o contrato canônico primeiro sai com o número velho. Corrigir no SPEC.
- **Índice de suposições ausente.** Há um `[ASSUMPTION]` inline (NFR-1, teto de 2 minutos) e nenhuma seção que o indexe. Com uma só, o custo é baixo — mas o roundtrip não existe, e se a nota da §5 (recorte por empresa) virar tag, passam a ser duas.
- **Ordem dos IDs de questão.** §9 lista Q-1, Q-6, Q-7, Q-3, Q-2, Q-4, Q-5 — resolvidas primeiro, abertas depois. Todas presentes e sem duplicata, mas a leitura sequencial parece ter buracos. Ordenar por número dentro de cada grupo, ou separar em "Resolvidas" e "Abertas" com subtítulo.
- **Status do front-matter.** `status: draft` enquanto o `.memlog.md` registra "Intent: Update + Finalize". Atualizar ao fechar o gate.
- **IDs e referências.** FR-1..FR-14, NFR-1..NFR-9, DG-1..DG-5, M-1..M-5, CM-1..CM-4, UJ-1..UJ-2: contíguos, únicos, sem duplicata. Todas as referências cruzadas internas (FR-2 em FR-7, NFR-5 em §6, NFR-9 em DG-4, NFR-1 em M-3, NFR-3 em M-4) resolvem. Todos os arquivos citados existem.
