---
title: Review — Caça a Casos-Limite (PRD Plataforma de Análise de Reclamações)
target: prd.md
method: bmad-review-edge-case-hunter
date: 2026-08-06
findings: 50
---

# Review — Casos-limite não tratados

**Escopo.** `prd.md` na íntegra. Contexto lido para descarte de falsos achados: `SPEC.md`, `state-contract.md`, `risk-signals.md`. Caminho já tratado em qualquer um dos quatro documentos foi descartado em silêncio e não aparece aqui.

**Método.** Enumeração mecânica de ramificações e condições de fronteira. Somente caminhos sem tratamento definido. Sem juízo de estilo, sem elogio, sem proposta de escopo, sem rótulo de severidade.

**Contagem: 50 achados.**

---

## A — Seção 6 (Comportamento em falha): combinações sem resposta definida

### A1 — Limite de taxa persistente após lotes concluídos: relatório sai ou não sai
- **Local:** prd.md:117 vs prd.md:116
- **Gatilho:** limite de taxa persiste depois de 4 de 5 lotes concluídos
- **Guarda:** definir na tabela: "escalada de taxa após N lotes concluídos → [emite relatório marcado como parcial | encerra sem relatório]"
- **Consequência:** duas linhas da mesma tabela pedem coisas opostas; implementação escolhe sozinha

### A2 — Cota diária do tier gratuito esgotada tratada como limite de taxa
- **Local:** prd.md:117 (linha "Limite de taxa da API atingido"), NFR-3 prd.md:83
- **Gatilho:** 429 por cota diária esgotada, não por taxa por minuto
- **Guarda:** separar as duas linhas: "cota do período esgotada → encerra imediatamente, espera não resolve"
- **Consequência:** "aguarda e repete" espera por algo que só volta no dia seguinte

### A3 — "Aguarda e repete" sem limite de tentativas nem de espera total
- **Local:** prd.md:117
- **Gatilho:** API responde 429 repetidamente com backoff crescente
- **Guarda:** fixar teto explícito: máximo de tentativas por lote e espera acumulada máxima, alinhados ao teto de NFR-1
- **Consequência:** execução estoura os 2 minutos de NFR-1 sem que nada a interrompa

### A4 — Nenhuma linha para API lenta que não falha
- **Local:** prd.md:111-120 (tabela inteira)
- **Gatilho:** chamada aceita e nunca responde, ou responde em 90s
- **Guarda:** acrescentar timeout por chamada e linha "chamada excede timeout → trata como resposta ausente"
- **Consequência:** "API indisponível" nunca dispara porque a API não está indisponível, está lenta

### A5 — Cem por cento das reclamações falham
- **Local:** NFR-5 prd.md:88, tabela prd.md:118
- **Gatilho:** todos os lotes retornam malformados; nenhuma análise sobrevive
- **Guarda:** linha nova: "zero reclamações analisadas com sucesso → encerra sem gerar relatório, como no CSV vazio"
- **Consequência:** relatório com fila vazia e ranking vazio é indistinguível de base sem risco

### A6 — Falha na escrita do próprio HTML
- **Local:** FR-1 prd.md:53, FR-4 prd.md:56
- **Gatilho:** disco cheio, pasta sem permissão, arquivo aberto/bloqueado no navegador do operador
- **Guarda:** escrever em arquivo temporário e renomear ao final; falha na escrita → mensagem nomeando o caminho
- **Consequência:** todo o custo de LLM é pago e o resultado se perde, ou fica um HTML truncado

### A7 — Duas causas de rejeição simultâneas no mesmo CSV
- **Local:** FR-3 prd.md:55 ("mensagem que nomeia a causa", singular)
- **Gatilho:** arquivo com coluna ausente **e** identificador duplicado
- **Guarda:** definir se a validação acumula e reporta todas as causas ou aborta na primeira
- **Consequência:** operador corrige uma causa, roda de novo, descobre a seguinte; N ciclos para N defeitos

### A8 — Limite de taxa e resposta malformada no mesmo lote
- **Local:** prd.md:117 vs prd.md:118
- **Gatilho:** resposta chega truncada por corte de cota no meio do streaming
- **Guarda:** definir precedência: erro de transporte → repetir; erro de conteúdo → marcar como não analisadas
- **Consequência:** o mesmo lote pode ser repetido indefinidamente ou descartado sem tentativa

### A9 — Interrupção do processo no meio da execução
- **Local:** prd.md:111-120
- **Gatilho:** Ctrl+C, kill, queda de energia entre o lote 3 e o lote 4
- **Guarda:** definir o artefato deixado para trás — nenhum arquivo, ou arquivo parcial nomeado como tal
- **Consequência:** próxima execução encontra um HTML anterior que ninguém sabe se é completo (ver F5)

### A10 — Credencial válida no início e revogada durante a execução
- **Local:** prd.md:116 vs NFR-5 prd.md:88
- **Gatilho:** 401 no lote 3 de 5, após lotes anteriores bem-sucedidos
- **Guarda:** classificar 401 tardio como falha terminal, não como "falha em uma reclamação"
- **Consequência:** cai na regra de NFR-5 e prossegue registrando todo o resto como "não analisado"

---

## B — FR-3: entradas de fronteira que passam pelo crivo

### B1 — Arquivo inexistente, caminho que é diretório, arquivo sem permissão de leitura
- **Local:** FR-1 prd.md:53, FR-3 prd.md:55
- **Gatilho:** caminho digitado errado, ou caminho de pasta
- **Guarda:** validar existência e legibilidade do caminho antes de qualquer parsing
- **Consequência:** stack trace bruto no lugar da mensagem que nomeia a causa exigida por FR-3

### B2 — Nenhum argumento, ou mais de um argumento na linha de comando
- **Local:** FR-1 prd.md:53
- **Gatilho:** operador roda o comando sem caminho, ou com dois caminhos
- **Guarda:** exigir exatamente um argumento posicional e imprimir uso quando ausente
- **Consequência:** comportamento indefinido no primeiro contato do único papel que usa terminal

### B3 — Arquivo que não é UTF-8
- **Local:** FR-3 prd.md:55, `state-contract.md` (leitura com `utf-8-sig`)
- **Gatilho:** CSV exportado em cp1252/latin-1 por Excel em outra máquina
- **Guarda:** capturar erro de decodificação e reportar "codificação não suportada; esperado UTF-8"
- **Consequência:** exceção de decodificação não coberta por nenhuma das três causas de rejeição de FR-3

### B4 — Data malformada, impossível, vazia ou ambígua
- **Local:** FR-3 prd.md:55, `state-contract.md` (`data: str` ISO-8601 convertido de `DD/MM/AAAA`)
- **Gatilho:** `31/02/2026`, `2026-08-06` já em ISO, campo vazio, ou `05/06/2026` em base de origem MM/DD
- **Guarda:** validar conversão de todas as datas na ingestão; falha de conversão é causa de rejeição nomeada
- **Consequência:** parcela de prazo estourado calcula sobre data inválida, ou a conversão explode fora de qualquer guarda

### B5 — `Status` fora dos cinco valores do contrato
- **Local:** FR-3 prd.md:55, `state-contract.md` (`Literal` de 5 valores)
- **Gatilho:** base nova traz "Aguardando", "Encerrada" ou string vazia
- **Guarda:** validar domínio de `Status` na ingestão como parte do schema
- **Consequência:** `Literal` é anotação de tipo, não validação em execução; modificador de score não reconhece o valor e falha em silêncio

### B6 — `ID_Reclamacao` em branco, ou duplicado apenas após normalização
- **Local:** FR-3 prd.md:55, prd.md:115, `state-contract.md` (`scores: dict[str, int]`)
- **Gatilho:** `RA123 ` e `RA123`, ou `ra123` e `RA123`, ou dois campos vazios
- **Guarda:** normalizar (trim + caixa) antes do teste de unicidade e rejeitar identificador vazio
- **Consequência:** unicidade passa, `scores` sobrescreve silenciosamente uma reclamação com a outra

### B7 — `Descricao` vazia ou só espaços
- **Local:** FR-3 prd.md:55, FR-5 prd.md:60
- **Gatilho:** linha com texto em branco na coluna analisada
- **Guarda:** rejeitar na ingestão ou marcar como não analisável sem gastar chamada
- **Consequência:** consome cota de LLM para produzir análise sem base, e verificação de citação de C1 aceita qualquer coisa

### B8 — Uma única linha maior que o limite de contexto
- **Local:** NFR-2 prd.md:79
- **Gatilho:** reclamação com 40 mil caracteres em base real
- **Guarda:** teto de tamanho por reclamação com truncamento declarado ou rejeição nomeada
- **Consequência:** NFR-2 calibra o lote, não a linha; lote de tamanho 1 ainda estoura e nunca converge

### B9 — Linha com número de campos diferente do cabeçalho
- **Local:** FR-3 prd.md:55, `state-contract.md` ("nenhum campo contém o separador" — validado só para o arquivo atual)
- **Gatilho:** base futura com `;` dentro de `Descricao`, sem aspas
- **Guarda:** validar contagem de campos por linha contra o cabeçalho
- **Consequência:** deslocamento de coluna silencioso — texto vira `Cidade_Estado` e nada em FR-3 detecta

### B10 — Base muito maior que 50 linhas
- **Local:** UJ-1 prd.md:41 ("base do mês"), NFR-1 prd.md:78, M-3 prd.md:129
- **Gatilho:** operador roda sobre 5.000 reclamações
- **Guarda:** declarar teto de linhas aceitas, ou definir o comportamento acima do teto de tempo
- **Consequência:** NFR-1 e M-3 valem só para 50; acima disso não há tempo, custo nem falha definidos

---

## C — FR-6 / FR-7: derrubada de citação

### C1 — Citação vazia ou de um caractere passa no teste de substring
- **Local:** FR-7 prd.md:62, M-2 prd.md:128
- **Gatilho:** modelo devolve `""`, `" "` ou `"a"` como evidência
- **Guarda:** exigir comprimento mínimo e ao menos N palavras antes de aceitar a citação como sustentação
- **Consequência:** verificação aprova 100% das citações (M-2 satisfeito), e o item da fila exibe nada ao leitor

### C2 — Normalização da comparação não definida
- **Local:** FR-7 prd.md:62
- **Gatilho:** citação difere do original por caixa, acento, aspas curvas, quebra de linha ou espaço duplo
- **Guarda:** fixar a regra de normalização aplicada aos dois lados antes do teste de substring
- **Consequência:** citação literal é contabilizada como fabricada; CM-2 sobe por defeito de comparação e culpa o prompt

### C3 — Citação extraída do `Titulo` e verificada contra a `Descricao`
- **Local:** FR-7 prd.md:62, `state-contract.md` (`titulo` e `texto` são campos distintos)
- **Gatilho:** modelo cita a frase do título, que é literal e existe no registro
- **Guarda:** definir explicitamente o texto de referência da verificação, e se `titulo` entra nele
- **Consequência:** sinal correto derrubado como fabricado, ou aceito contra campo que ninguém decidiu incluir

### C4 — `evidencia` não é ligada a `sinal_b`; "derrubar o sinal" não é expressável
- **Local:** FR-7 prd.md:62, `state-contract.md` (`sinal_b: list[str]` e `evidencia: list[str]` são listas paralelas sem vínculo)
- **Gatilho:** reclamação com dois códigos de sinal e três citações, uma inválida
- **Guarda:** amarrar evidência ao código do sinal (par ou dict por código) antes de qualquer derrubada seletiva
- **Consequência:** não há como saber qual sinal cai; ou cai tudo, ou não cai nada, e FR-7 vira decorativo

### C5 — Sinal com várias citações, parte válida e parte inválida
- **Local:** FR-6 prd.md:61 ("ao menos uma citação") vs FR-7 prd.md:62 ("derruba o sinal quando não existe")
- **Gatilho:** duas citações para o mesmo sinal, uma literal e uma fabricada
- **Guarda:** definir a regra: sinal sobrevive com a citação válida, ou cai inteiro ao primeiro defeito
- **Consequência:** FR-6 diz que uma basta; FR-7 diz que a inexistente derruba — leituras opostas do mesmo caso

### C6 — Reclamação que perde todos os sinais na verificação
- **Local:** FR-7 prd.md:62, FR-2 prd.md:54, NFR-5 prd.md:88
- **Gatilho:** único sinal da reclamação é derrubado por citação inexistente
- **Guarda:** definir se ela conta como "analisada com sucesso", se sai da fila, e se aparece em algum lugar do relatório
- **Consequência:** item desaparece da fila sem que a contagem de FR-2 registre a saída; ninguém vê o buraco

### C7 — Itens da fila pontuados por parcelas determinísticas não têm citação para exibir
- **Local:** FR-11 prd.md:69, `risk-signals.md` (parcelas `prazo estourado` peso 1 e `Status` −1 não são sinais com evidência)
- **Gatilho:** item atinge o corte por soma de parcelas determinísticas, sem sinal citado sobrevivente
- **Guarda:** ou exigir ao menos uma citação viva como condição de entrada na fila, ou definir o texto exibido quando não há
- **Consequência:** FR-11 é obrigatório e não tem o que renderizar; M-2 continua em 100% porque não há citação para violar

### C8 — FR-2 reporta derrubadas em absoluto; CM-2 é uma taxa sem denominador
- **Local:** FR-2 prd.md:54, CM-2 prd.md:139
- **Gatilho:** operador tenta calcular a taxa de derrubada da execução
- **Guarda:** reportar também o total de sinais emitidos antes da verificação
- **Consequência:** "3 derrubados" é indistinguível entre 3 de 4 e 3 de 300; a contramétrica não é calculável

---

## D — Resposta do modelo, NFR-5 e confiabilidade do relatório

### D1 — Modelo devolve identificador que não estava no lote
- **Local:** NFR-6 prd.md:89, prd.md:118
- **Gatilho:** resposta traz `RA999999` alucinado junto com os 10 pedidos
- **Guarda:** descartar identificadores fora do conjunto enviado e contabilizar como resposta malformada
- **Consequência:** NFR-6 compara identificadores para achar o que faltou; o que sobrou entra em `analises` e nos agregados

### D2 — Modelo repete o mesmo identificador na resposta
- **Local:** NFR-6 prd.md:89, `state-contract.md` (`analises: Annotated[list[Analise], add]`)
- **Gatilho:** dois itens com o mesmo `id` no mesmo lote, ou lote repetido por retry
- **Guarda:** validar unicidade de `id` também na saída do modelo, antes do acúmulo
- **Consequência:** o redutor `add` acumula ambos; a reclamação conta duas vezes no ranking, no sentimento e no total

### D3 — Item com identificador válido e campo fora do domínio
- **Local:** FR-5 prd.md:60, prd.md:118, `state-contract.md` (Literais de `sentimento` e catálogo de `sinal_b`)
- **Gatilho:** `sentimento: "misto"`, ou código de sinal fora dos cinco do catálogo
- **Guarda:** definir se campo inválido invalida o item inteiro ou apenas aquele campo
- **Consequência:** "resposta malformada" não distingue item ilegível de item legível com um campo inválido

### D4 — Falha na granularidade de lote, não de reclamação
- **Local:** NFR-5 prd.md:88 ("falha em uma reclamação")
- **Gatilho:** JSON do lote inteiro inválido; 10 reclamações caem de uma vez
- **Guarda:** declarar que a unidade de isolamento é o lote e o que acontece quando lotes consecutivos falham
- **Consequência:** NFR-5 fala de uma reclamação; a unidade de chamada é o lote — o isolamento prometido não existe nessa escala

### D5 — Nenhum limiar de falha invalida o relatório
- **Local:** NFR-5 prd.md:88, CM-4 prd.md:142
- **Gatilho:** 30 de 50 reclamações não analisadas; execução termina "com sucesso"
- **Guarda:** fixar limiar (ex.: acima de X% não analisadas → não gera relatório, ou gera com bloco de aviso obrigatório)
- **Consequência:** o relatório é gerado e enviado com a mesma aparência de uma execução limpa; CM-4 é conselho, não porta

### D6 — O leitor nunca vê a contagem de falhas
- **Local:** FR-13 prd.md:71, FR-2 prd.md:54, NFR-5 prd.md:88 ("contabilizada no relatório final ao operador")
- **Gatilho:** Ricardo abre o HTML de uma execução com 40% de falha
- **Guarda:** FR-13 passa a exigir no próprio HTML: lidas, analisadas e não analisadas
- **Consequência:** o único papel que decide sobre o relatório é o único que não recebe o sinal de degradação

### D7 — NFR-4 contra o retry da Seção 6 e o desmonte na escalada
- **Local:** NFR-4 prd.md:84 vs prd.md:117 e `SPEC.md` ("sublote remontado apenas com os candidatos")
- **Gatilho:** lote repetido após 429, ou reclamação reenviada em sublote de escalada
- **Guarda:** redigir NFR-4 excluindo explicitamente retry de transporte e escalada deliberada
- **Consequência:** implementação literal de NFR-4 proíbe o retry que a Seção 6 exige

---

## E — FR-8 e Q-2: produto não identificável

### E1 — Nada define quando o produto **deve** ser `None`
- **Local:** FR-8 prd.md:63, `state-contract.md` (`produto: str | None`)
- **Gatilho:** texto menciona "o serviço" genericamente; modelo devolve "serviço"
- **Guarda:** definir o critério de não identificável (lista fechada de produtos, ou regra explícita de abstenção)
- **Consequência:** o modelo quase nunca devolve `None`; FR-8 nunca é exercido e CM-3 fica em zero por construção

### E2 — Opção de Q-2 "omitida do ranking mas contada no total" contradiz CAP-7
- **Local:** Q-2 prd.md:159 vs `SPEC.md` CAP-7 ("os números agregados batem com a contagem direta")
- **Gatilho:** 8 reclamações sem produto, ranking somando 42 e cabeçalho dizendo 50
- **Guarda:** eliminar a opção incompatível, ou definir que o ranking exibe o resíduo declarado
- **Consequência:** uma das três saídas de Q-2 quebra um critério de sucesso já fechado no SPEC

### E3 — CM-3 sem limiar e sem ponto de medição
- **Local:** CM-3 prd.md:141 (contrasta com CM-1 prd.md:137, que tem 40%)
- **Gatilho:** taxa de produto não identificado em 35%
- **Guarda:** fixar limiar numérico e exigir que FR-2 reporte a taxa ao operador
- **Consequência:** contramétrica sem número e sem quem a calcule não dispara nunca

### E4 — Ranking inteiro vazio ou dominado pelo rótulo próprio
- **Local:** FR-8 prd.md:63, tabela prd.md:120 (cobre fila vazia, não ranking vazio)
- **Gatilho:** base de domínio novo em que nenhum produto é reconhecido
- **Guarda:** linha equivalente à da fila vazia: ranking sem produto identificado é declarado como tal
- **Consequência:** o leitor recebe um ranking de um item só ("não identificado") sem saber que é degradação

### E5 — `produto` é texto livre sem normalização
- **Local:** FR-8 prd.md:63, FR-12 prd.md:70, `state-contract.md` (`produto: str | None`)
- **Gatilho:** "cartão de crédito", "Cartão de Crédito" e "cartao credito" na mesma execução
- **Guarda:** normalizar ou mapear contra vocabulário controlado antes de agregar
- **Consequência:** o mesmo produto ocupa três linhas do ranking e nenhuma chega ao topo

### E6 — Reclamação que menciona dois produtos
- **Local:** FR-8 prd.md:63, `state-contract.md` (`produto` é campo único)
- **Gatilho:** texto reclama de cobrança do cartão **e** da assinatura de streaming
- **Guarda:** definir a regra de escolha (produto do fato reclamado) ou permitir lista
- **Consequência:** escolha arbitrária do modelo entra no ranking sem que nada a registre como ambígua

### E7 — Produto e sentimento não têm exigência de evidência nem verificação
- **Local:** FR-6 e FR-7 prd.md:61-62 (só cobrem sinal de risco), FR-5 prd.md:60
- **Gatilho:** modelo atribui produto que não aparece no texto
- **Guarda:** ou estender a verificação de citação a produto, ou declarar o ranking como não auditado
- **Consequência:** a defesa contra alucinação cobre a fila e não cobre duas das três leituras entregues ao gestor

---

## F — FR-4 e caminho de saída

### F1 — "Evidente ao operador" não define ação
- **Local:** FR-4 prd.md:56
- **Gatilho:** o arquivo de destino já existe
- **Guarda:** escolher uma: aborta nomeando o arquivo, grava com sufixo novo, ou exige flag de sobrescrita
- **Consequência:** três implementações legítimas e incompatíveis; nenhuma testável contra o requisito

### F2 — Confirmação interativa sem terminal interativo
- **Local:** FR-4 prd.md:56
- **Gatilho:** execução com stdin redirecionado, em CI, ou via agendador
- **Guarda:** nunca depender de prompt; usar flag explícita de sobrescrita
- **Consequência:** processo trava esperando entrada que nunca chega, depois de já ter pago as chamadas

### F3 — Duas execuções dentro da mesma granularidade de sufixo
- **Local:** FR-4 prd.md:56, FR-1 prd.md:53
- **Gatilho:** operador roda duas vezes no mesmo minuto (sufixo por data/minuto)
- **Guarda:** granularidade até segundo mais contador, ou falha explícita na colisão
- **Consequência:** a segunda execução sobrescreve a primeira — exatamente o que FR-4 proíbe

### F4 — Destino existente que não é arquivo gravável
- **Local:** FR-4 prd.md:56
- **Gatilho:** caminho é diretório, arquivo somente leitura, ou aberto/travado pelo navegador
- **Guarda:** testar gravabilidade do destino antes de iniciar o pipeline
- **Consequência:** falha na última etapa, depois de todo o custo de LLM consumido

### F5 — HTML truncado de execução interrompida conta como "relatório anterior"
- **Local:** FR-4 prd.md:56, A6, A9
- **Gatilho:** execução anterior morreu durante a escrita
- **Guarda:** escrita atômica (temporário + rename), de modo que só arquivo completo exista no destino
- **Consequência:** FR-4 protege um arquivo corrompido, e o operador pode enviá-lo achando que está completo

### F6 — "Caminho previsível" não é definido
- **Local:** FR-1 prd.md:53
- **Gatilho:** duas bases com o mesmo nome de arquivo em pastas diferentes
- **Guarda:** especificar a regra de derivação do caminho de saída
- **Consequência:** colisão de destino que FR-4 tenta impedir sem que ninguém saiba de onde o nome vem

---

## G — Fronteiras de governança de dados não guardadas

### G1 — Saída e base caem na pasta do projeto sem regra de `.gitignore`
- **Local:** UJ-1 prd.md:41 ("salva na pasta do projeto"), FR-1 prd.md:53, DG-2 prd.md:102, DG-4 prd.md:104 (cobre apenas o arquivo de ambiente)
- **Gatilho:** operador roda sobre base real, salva na pasta do projeto, e commita
- **Guarda:** `.gitignore` cobrindo o diretório de saída e o diretório de bases, desde já
- **Consequência:** DG-2 e DG-3 são política sem controle; o repositório é público

### G2 — O sistema não distingue base sintética de base real
- **Local:** DG-1 prd.md:101, DG-3 prd.md:103, FR-13 prd.md:71
- **Gatilho:** mesma execução, mesmo comando, sobre base real
- **Guarda:** marcação de origem na entrada refletida como aviso de restrição no próprio HTML
- **Consequência:** o relatório restrito de DG-3 é visualmente idêntico ao seguro; nada no arquivo diz o que ele é

---

## Anexo — achados em formato do método

```json
[
{"location":"prd.md:116-117","trigger_condition":"Limite de taxa persiste apos lotes ja concluidos","guard_snippet":"linha na tabela: escalada de taxa com N lotes ok -> emite parcial marcado OU encerra sem relatorio","potential_consequence":"Duas linhas da tabela pedem comportamentos opostos"},
{"location":"prd.md:117","trigger_condition":"Cota diaria esgotada tratada como limite de taxa","guard_snippet":"linha separada: cota do periodo esgotada -> encerra, espera nao resolve","potential_consequence":"Retry espera por janela que so abre no dia seguinte"},
{"location":"prd.md:117","trigger_condition":"Aguarda e repete sem teto de tentativas ou espera","guard_snippet":"max_tentativas e espera_acumulada_max alinhados a NFR-1","potential_consequence":"Execucao estoura os 2 minutos sem interrupcao definida"},
{"location":"prd.md:111-120","trigger_condition":"API lenta ou pendurada, nunca indisponivel","guard_snippet":"timeout por chamada; excedido -> trata como resposta ausente","potential_consequence":"Nenhuma linha da tabela cobre chamada que nao retorna"},
{"location":"prd.md:88,118","trigger_condition":"Cem por cento das reclamacoes falham na analise","guard_snippet":"zero analisadas com sucesso -> encerra sem gerar relatorio","potential_consequence":"Relatorio vazio indistinguivel de base sem risco"},
{"location":"prd.md:53,56","trigger_condition":"Falha ao escrever o HTML final","guard_snippet":"escrever em temporario e renomear; erro nomeia o caminho","potential_consequence":"Custo de LLM pago e resultado perdido ou truncado"},
{"location":"prd.md:55","trigger_condition":"Duas causas de rejeicao simultaneas no mesmo CSV","guard_snippet":"acumular todas as causas de rejeicao antes de abortar","potential_consequence":"Operador descobre um defeito por execucao"},
{"location":"prd.md:117-118","trigger_condition":"Limite de taxa e resposta malformada no mesmo lote","guard_snippet":"precedencia: erro de transporte repete, erro de conteudo marca falha","potential_consequence":"Lote repetido indefinidamente ou descartado sem tentativa"},
{"location":"prd.md:111-120","trigger_condition":"Processo interrompido no meio da execucao","guard_snippet":"definir artefato deixado: nenhum, ou nomeado como parcial","potential_consequence":"Arquivo parcial confundido com relatorio completo"},
{"location":"prd.md:88,116","trigger_condition":"Credencial revogada apos lotes bem-sucedidos","guard_snippet":"401 tardio e falha terminal, nao falha de uma reclamacao","potential_consequence":"Prossegue marcando todo o restante como nao analisado"},
{"location":"prd.md:53,55","trigger_condition":"Caminho inexistente, diretorio, ou sem permissao","guard_snippet":"validar existencia e legibilidade antes do parsing","potential_consequence":"Stack trace no lugar da mensagem exigida por FR-3"},
{"location":"prd.md:53","trigger_condition":"Zero argumentos ou mais de um na linha de comando","guard_snippet":"exigir exatamente um argumento posicional e imprimir uso","potential_consequence":"Comportamento indefinido no primeiro uso do operador"},
{"location":"prd.md:55","trigger_condition":"Arquivo que nao e UTF-8 (cp1252, latin-1)","guard_snippet":"capturar erro de decodificacao e reportar codificacao nao suportada","potential_consequence":"Excecao fora das tres causas de rejeicao previstas"},
{"location":"prd.md:55","trigger_condition":"Data malformada, impossivel, vazia ou ambigua","guard_snippet":"validar conversao de todas as datas na ingestao","potential_consequence":"Parcela de prazo calcula sobre data invalida ou explode"},
{"location":"prd.md:55","trigger_condition":"Valor de Status fora dos cinco literais do contrato","guard_snippet":"validar dominio de Status como parte do schema","potential_consequence":"Modificador de score nao reconhece o valor e falha em silencio"},
{"location":"prd.md:55,115","trigger_condition":"ID em branco ou duplicado apos normalizacao de caixa/espaco","guard_snippet":"normalizar antes do teste de unicidade e rejeitar ID vazio","potential_consequence":"scores[id] sobrescreve uma reclamacao com a outra"},
{"location":"prd.md:55,60","trigger_condition":"Descricao vazia ou apenas espacos","guard_snippet":"rejeitar na ingestao ou marcar nao analisavel sem chamada","potential_consequence":"Gasta cota e produz analise sem base textual"},
{"location":"prd.md:79","trigger_condition":"Uma unica linha maior que o limite de contexto","guard_snippet":"teto de caracteres por reclamacao com truncamento declarado","potential_consequence":"Lote de tamanho 1 ainda estoura e nunca converge"},
{"location":"prd.md:55","trigger_condition":"Linha com contagem de campos diferente do cabecalho","guard_snippet":"validar numero de campos por linha contra o cabecalho","potential_consequence":"Deslocamento silencioso de coluna nao detectado"},
{"location":"prd.md:41,78,129","trigger_condition":"Base muito maior que as 50 linhas de referencia","guard_snippet":"declarar teto de linhas aceitas e comportamento acima dele","potential_consequence":"Tempo, custo e falha indefinidos fora do tamanho medido"},
{"location":"prd.md:62,128","trigger_condition":"Citacao vazia ou de um caractere passa no substring","guard_snippet":"exigir comprimento minimo e N palavras na citacao","potential_consequence":"M-2 em 100% com item de fila que nao exibe evidencia"},
{"location":"prd.md:62","trigger_condition":"Normalizacao da comparacao de citacao nao definida","guard_snippet":"fixar normalizacao (caixa, acento, espaco, aspas) nos dois lados","potential_consequence":"Citacao literal contabilizada como fabricada; CM-2 falseia"},
{"location":"prd.md:62","trigger_condition":"Citacao extraida do Titulo, verificada contra Descricao","guard_snippet":"definir o texto de referencia da verificacao explicitamente","potential_consequence":"Sinal correto derrubado, ou campo aceito sem decisao"},
{"location":"prd.md:62","trigger_condition":"evidencia nao e ligada ao codigo do sinal em sinal_b","guard_snippet":"amarrar evidencia por codigo de sinal antes de derrubar","potential_consequence":"Impossivel saber qual sinal cai; FR-7 vira decorativo"},
{"location":"prd.md:61-62","trigger_condition":"Sinal com varias citacoes, parte valida e parte fabricada","guard_snippet":"definir se sobrevive com a valida ou cai ao primeiro defeito","potential_consequence":"FR-6 e FR-7 dao leituras opostas do mesmo caso"},
{"location":"prd.md:54,62,88","trigger_condition":"Reclamacao perde todos os sinais na verificacao","guard_snippet":"definir se conta como analisada, se sai da fila, e onde aparece","potential_consequence":"Item some da fila sem registro na contagem de FR-2"},
{"location":"prd.md:69","trigger_condition":"Item entra na fila por parcelas deterministicas sem citacao","guard_snippet":"exigir citacao viva como condicao de entrada na fila","potential_consequence":"FR-11 obrigatorio sem nada para renderizar"},
{"location":"prd.md:54,139","trigger_condition":"Derrubadas reportadas em absoluto; CM-2 e taxa","guard_snippet":"reportar tambem total de sinais emitidos antes da verificacao","potential_consequence":"Contramétrica CM-2 nao e calculavel pelo operador"},
{"location":"prd.md:89,118","trigger_condition":"Modelo devolve identificador que nao estava no lote","guard_snippet":"descartar IDs fora do conjunto enviado e contar como malformada","potential_consequence":"Analise alucinada entra no estado e nos agregados"},
{"location":"prd.md:89","trigger_condition":"Modelo repete o mesmo identificador na resposta","guard_snippet":"validar unicidade de id na saida antes do acumulo","potential_consequence":"Reducer add conta a reclamacao duas vezes nos agregados"},
{"location":"prd.md:60,118","trigger_condition":"Item com id valido e campo fora do dominio","guard_snippet":"definir se campo invalido invalida o item ou so o campo","potential_consequence":"Malformada nao distingue item ilegivel de campo invalido"},
{"location":"prd.md:88","trigger_condition":"Lote inteiro falha; isolamento e por reclamacao","guard_snippet":"declarar lote como unidade de isolamento e limite de lotes falhos","potential_consequence":"Isolamento prometido por NFR-5 nao existe na escala do lote"},
{"location":"prd.md:88,142","trigger_condition":"Nenhum limiar de falha invalida o relatorio","guard_snippet":"acima de X% nao analisadas -> nao gera, ou gera com aviso obrigatorio","potential_consequence":"Relatorio degradado enviado com aparencia de execucao limpa"},
{"location":"prd.md:54,71,88","trigger_condition":"Leitor nunca ve a contagem de falhas no HTML","guard_snippet":"FR-13 exige lidas, analisadas e nao analisadas no relatorio","potential_consequence":"Quem decide sobre o relatorio nao recebe o sinal de degradacao"},
{"location":"prd.md:84,117","trigger_condition":"NFR-4 proibe repetir chamada; Secao 6 exige retry","guard_snippet":"excluir retry de transporte e escalada do texto de NFR-4","potential_consequence":"Implementacao literal de NFR-4 impede o retry exigido"},
{"location":"prd.md:63","trigger_condition":"Nada define quando produto deve ser None","guard_snippet":"criterio explicito de abstencao ou vocabulario fechado","potential_consequence":"FR-8 nunca e exercido; CM-3 fica em zero por construcao"},
{"location":"prd.md:159","trigger_condition":"Opcao de Q-2 omite do ranking mas conta no total","guard_snippet":"eliminar a opcao incompativel ou exibir residuo declarado","potential_consequence":"Quebra CAP-7: agregados deixam de bater com a contagem direta"},
{"location":"prd.md:141","trigger_condition":"CM-3 sem limiar numerico e sem ponto de medicao","guard_snippet":"fixar limiar e exigir a taxa no relatorio ao operador","potential_consequence":"Contramétrica nunca dispara"},
{"location":"prd.md:63,120","trigger_condition":"Ranking vazio ou dominado pelo rotulo nao identificado","guard_snippet":"declarar ranking sem produto identificado como tal, igual a fila vazia","potential_consequence":"Leitor le degradacao como resultado"},
{"location":"prd.md:63,70","trigger_condition":"produto e texto livre sem normalizacao","guard_snippet":"normalizar ou mapear contra vocabulario controlado antes de agregar","potential_consequence":"Mesmo produto ocupa varias linhas do ranking"},
{"location":"prd.md:63","trigger_condition":"Reclamacao menciona dois produtos, campo e unico","guard_snippet":"regra de escolha explicita, ou permitir lista","potential_consequence":"Escolha arbitraria entra no ranking sem registro de ambiguidade"},
{"location":"prd.md:60-62","trigger_condition":"Produto e sentimento sem evidencia nem verificacao","guard_snippet":"estender verificacao a produto, ou declarar ranking nao auditado","potential_consequence":"Defesa contra alucinacao cobre so uma das tres leituras"},
{"location":"prd.md:56","trigger_condition":"Evidente ao operador nao define acao no destino existente","guard_snippet":"escolher: aborta, sufixo novo, ou flag de sobrescrita","potential_consequence":"Tres implementacoes legitimas e incompativeis, nenhuma testavel"},
{"location":"prd.md:56","trigger_condition":"Confirmacao interativa sem terminal interativo","guard_snippet":"flag explicita de sobrescrita, nunca prompt","potential_consequence":"Processo trava esperando entrada apos pagar as chamadas"},
{"location":"prd.md:53,56","trigger_condition":"Duas execucoes na mesma granularidade de sufixo","guard_snippet":"sufixo ate segundo mais contador, ou falha explicita na colisao","potential_consequence":"Segunda execucao sobrescreve a primeira, contra FR-4"},
{"location":"prd.md:56","trigger_condition":"Destino existente e diretorio, somente leitura ou travado","guard_snippet":"testar gravabilidade do destino antes de iniciar o pipeline","potential_consequence":"Falha na ultima etapa com todo o custo ja consumido"},
{"location":"prd.md:56","trigger_condition":"HTML truncado anterior conta como relatorio valido","guard_snippet":"escrita atomica: temporario mais rename","potential_consequence":"FR-4 protege arquivo corrompido que pode ser enviado"},
{"location":"prd.md:53","trigger_condition":"Caminho previsivel de saida nao e definido","guard_snippet":"especificar a regra de derivacao do caminho de saida","potential_consequence":"Colisao de destino sem que a origem do nome seja conhecida"},
{"location":"prd.md:41,53,102,104","trigger_condition":"Base real e relatorio salvos na pasta do projeto","guard_snippet":"gitignore cobrindo diretorio de saida e de bases desde ja","potential_consequence":"DG-2 e DG-3 sem controle tecnico em repositorio publico"},
{"location":"prd.md:101,103,71","trigger_condition":"Sistema nao distingue base sintetica de base real","guard_snippet":"marcacao de origem refletida como aviso de restricao no HTML","potential_consequence":"Relatorio restrito visualmente identico ao seguro"}
]
```
