---
title: Revisão do PRD — perspectiva de avaliador de portfólio
alvo: prd.md
revisor: avaliador técnico sênior (leitura de repositório público)
data: 2026-08-06
---

# Revisão — PRD Plataforma de Análise de Reclamações

Leitura feita como quem abre um repositório público antes de uma entrevista. Li o PRD, o `SPEC.md`, `risk-signals.md`, `state-contract.md`, `roadmap.md`, `baseline.py`, `classificador.py`, o `.cache_analises.json` que ficou no disco, os dois gabaritos e o histórico do git. Rodei os números que o documento afirma.

## Veredito sobre a tensão central

A pergunta que o autor colocou é se registrar o empate (F1 0,86 para os dois, zero divergências item a item) é honestidade admirável ou a prova de que o projeto é infraestrutura sem justificativa.

**As duas coisas, e a segunda pesa mais — mas não pelo motivo que o autor imagina.**

Registrar o empate é raro e conta muito a favor. A maioria dos projetos de portfólio com LLM nunca constrói a linha de base determinística que poderia matá-los; este construiu, mediu, e publicou o resultado desfavorável. Isso é o ativo número um do repositório.

O problema é que a honestidade parou no primeiro resultado ruim. O produto promete três leituras (§1: fila de prioridade, ranking de produtos, percepção da marca). A mesma execução que produziu o empate produziu também os números das outras duas, e eles estão no `.cache_analises.json` versionado no disco de trabalho:

| Leitura prometida | O que a execução de 2026-08-06 produziu | O PRD reporta? |
|---|---|---|
| Fila de prioridade | Empate com um `set` de 6 strings | **Sim** (M-1) |
| Percepção da marca | `negativo` em **50 de 50** — distribuição de uma barra só | Não |
| Ranking de produtos | 19 rótulos, liderados por `fatura` (7), `produto` (4), `serviço` (3) — substantivos genéricos, não produtos | Não |

Honestidade aplicada apenas ao achado que você já decidiu publicar não é honestidade, é curadoria. O PRD reporta a medição que ainda deixa o projeto de pé e omite as duas que não deixam — e omite justamente as que ele já tinha em mãos.

Veredito: **nesta base, o projeto é infraestrutura sem justificativa, e o documento sabe disso sobre um terço do produto.** Isso é reparável e barato de reparar, porque o argumento que salva o projeto já existe no repositório e está fora do PRD: `classificador.py` lê **apenas o texto livre**, nunca o título canônico que a regra determinística consome de graça. Numa base sem títulos padronizados a regra simplesmente não existe. Esse é o único argumento honesto pela existência do pipeline, está escrito no docstring do código e em `risk-signals.md`, e não aparece uma vez sequer no PRD. Promovê-lo para a §1 e declarar o empate como resultado esperado — em vez de escondê-lo como sub-item de métrica — converte a leitura mais fraca do projeto na mais forte.

O que **não** salva o projeto: manter 14 FRs, 9 NFRs, 5 cláusulas de governança e uma orquestração multi-agente obrigatória cujo único argumento declarado é "é o objeto de estudo", como se o empate não tivesse acontecido.

---

## Crítico

### C-1 — O empate é registrado e não muda nenhuma decisão do documento

**Local:** §7.1, M-1, sub-item; contra §3, §4, §8 e §9.

> "**Medido em 2026-08-06:** regra determinística e Gemini 3.6 Flash empatam em F1 0,86, com zero divergências item a item. O alvo está atingido — e o LLM não superou a regra nesta base."

Este é o achado do projeto. Ele está enterrado como o segundo parágrafo de uma das cinco métricas, e nada a jusante muda por causa dele: o escopo é o mesmo, os requisitos são os mesmos, o roadmap segue com cascata entre modelos e loop de crítica. Um documento que mede um resultado nulo e mantém o plano intacto está descrevendo uma decisão que já estava tomada antes da medição. É exatamente o padrão que um avaliador procura quando quer saber se a pessoa mede para decidir ou mede para ilustrar.

**Correção:** subir o achado para a §1, com uma frase que assuma a consequência. Sugestão de forma: *"Sobre esta base, o pipeline de LLM não supera uma regra de seis strings — e não deveria: a regra consome um título canônico que uma base real não tem. O entregável é a arquitetura; o resultado nulo é o preço de a base ser sintética, e está medido em vez de suposto."* Depois disso, ou a §8 ganha um item declarando que o valor do LLM não é demonstrável neste corpus, ou o §9 ganha uma questão sobre obter um corpus que o demonstre.

### C-2 — M-1 só passa por causa de uma revisão do gabarito feita depois de ver a saída do modelo

**Local:** §7.1, M-1; §9, Q-7.

> "A fila produzida atinge **F1 ≥ 0,85** contra `docs/gabarito.csv` (19 de 50 marcadas manualmente)."
> "**Q-7 — RESOLVIDA.** `docs/gabarito.csv` v2, 19 de 50 marcadas por leitura manual cega."

Rodei `baseline.avalia` contra os dois gabaritos preservados no repositório:

| Gabarito | Marcadas | TP / FP / FN | F1 |
|---|---|---|---|
| `gabarito-v1.csv` (antes da revisão) | 18 (36%) | 15 / 3 / 3 | **0,83 — reprovado** |
| `gabarito.csv` (v2, vigente) | 19 (38%) | 16 / 2 / 3 | **0,86 — aprovado** |

A revisão que acrescentou `RA645276696` é o que move o projeto de reprovado para aprovado no seu próprio critério de aceitação. E `risk-signals.md` registra, com todas as letras, que essa marcação foi acrescentada **porque o classificador com LLM a marcou**: *"o classificador com LLM a marcou citando literalmente 'sigo sendo cobrado'"*. A mesma revisão entrou em `baseline.py` (`# incluída na revisão do gabarito v2`).

O registro em `risk-signals.md` é honesto e auditável — esse não é o problema. O problema é que o PRD chama o gabarito de "leitura manual cega" sem qualificar que uma das 19 marcações não é cega, e reporta "O alvo está atingido" sem informar que o alvo não era atingido antes do ajuste. Um avaliador que abre os dois CSVs (estão lado a lado no `docs/`, com nomes que convidam à comparação) chega a esse número em dois minutos.

**Correção:** em M-1, reportar os dois números explicitamente. *"F1 0,86 contra o gabarito v2; 0,83 contra o v1. A diferença é uma marcação, acrescentada após argumento do classificador e aplicada igualmente às duas abordagens. Com a margem em um item, o alvo de 0,85 não distingue as duas hipóteses — a medição diz que o sinal existe, não que ele foi validado."* Isso custa três linhas e transforma o achado mais frágil do documento no mais convincente.

### C-3 — A "percepção da marca" é uma constante, e o PRD a vende como uma das três leituras

**Local:** §1; §7.1, M-5; realiza CAP-2 via FR-5.

> "Este produto lê a base e devolve três leituras: [...] e a percepção do cliente sobre a marca."
> "**M-5** — [...] consegue dizer [...] como o cliente se sente com a marca."

Na execução de 2026-08-06 (`.cache_analises.json`, 50 entradas): `sentimento` = `negativo` em **50 de 50**. Zero neutros, zero positivos.

Isso era previsível a priori — uma base de reclamações não tem por que conter outra coisa — e é exatamente por isso que conta contra o documento: ninguém perguntou, antes de gastar um eixo de análise, se um eixo de sentimento sobre um corpus de reclamações pode assumir mais de um valor. O gráfico prometido ao gestor é uma barra. M-5 pede que o leitor diga "como o cliente se sente com a marca" olhando um relatório cuja resposta é sempre a mesma.

**Correção:** ou matar CAP-2/o eixo de sentimento e dizer no PRD por que (uma linha: *"medido: 50/50 negativo; um eixo de valor único não informa"*), ou substituí-lo por algo com variância real — intensidade, ou a taxa de `Status` sem resolução, que já está estruturada na base e é de graça. Não deixar como está: um avaliador que abre o relatório HTML vai ver a barra única e perguntar se o autor chegou a olhar a própria saída.

### C-4 — O ranking de produtos é degenerado, e CM-3 foi desenhada para não perceber

**Local:** §7.2, CM-3; FR-8; §9, Q-2.

> "**CM-3 — Taxa de produto não identificado.** Subindo, o ranking de produtos perde significado mesmo que os totais fechem."
> "**FR-8** — Reclamação cujo produto não é identificável recebe rótulo próprio e permanece na base analisada."

Distribuição real dos 50 rótulos produzidos: `fatura` 7, `internet` 5, `compra` 4, `conta bancária` 4, `produto` 4, `serviço` 3, `convênio` 3, `aparelho` 3, `blusa` 3, e uma cauda de itens únicos. **`produto` é `None` em exatamente 1 de 50.**

CM-3 vai reportar 2% e parecer saudável. Mas os quatro primeiros lugares do ranking — o entregável que o gestor lê — são `fatura`, `internet`, `compra`, `produto`. Três desses quatro não são produtos; são substantivos genéricos que o modelo devolve quando não consegue identificar nada e não quer devolver `null`. O modo de falha real não é a não-resposta honesta que FR-8 e CM-3 cobrem; é a **não-resposta confiante**, que passa por todos os controles. O prompt pede *"o produto ou serviço mencionado no texto, em uma ou duas palavras"* sem vocabulário controlado, então isso é comportamento por desenho, não acidente.

**Correção:** CM-3 precisa medir a concentração em rótulos genéricos, não a taxa de `null`. O caminho mais barato é fechar o vocabulário: enumerar as categorias de produto no schema (`Literal[...]`) e deixar `null` ser a única saída de escape. Isso também resolve Q-2 sem discussão — categoria fechada tem lugar definido no ranking por construção.

---

## Alto

### A-1 — A medição de referência não é reproduzível a partir do artefato

**Local:** §7.1, M-1 ("Medido em 2026-08-06"); `classificador.py:117-126`.

O cache é invalidado apenas por comparação do conjunto de IDs:

```python
if set(analises) == {r["ID_Reclamacao"] for r in reclamacoes}:
```

Nem versão de prompt, nem modelo, nem temperatura entram na chave. Trocar `INSTRUCAO` ou `MODELO` reaproveita silenciosamente as análises antigas. O `roadmap.md` do próprio autor documenta esse erro exato: *"Chave apenas com o texto envenena o cache no primeiro ajuste de prompt e produz depuração perdida."* O código faz pior que a versão que o roadmap desaconselha — a chave nem inclui o texto.

Consequência para o PRD: o F1 0,86 do LLM não é rastreável a nenhuma versão de prompt. O `.cache_analises.json` no disco pode ter sido produzido por qualquer iteração do glossário — e o glossário foi visivelmente iterado (a regra sobre produto defeituoso tem o tom de quem consertou um falso negativo específico).

**Correção:** chave de cache = `hash(texto + INSTRUCAO + MODELO)`, como o próprio roadmap manda; e M-1 passa a citar a versão do prompt junto com o número. Três linhas de código, e a medição vira evidência em vez de anedota.

### A-2 — DG-4 afirma um fato que o `git log` desmente

**Local:** §5, DG-4.

> "A chave de API não é versionada (ver NFR-9), e o arquivo de ambiente está no `.gitignore` **desde o primeiro commit**."

`git ls-tree -r --name-only 163da9a` devolve exatamente um arquivo: `README.md`. O `.gitignore` está **untracked** — não está em commit nenhum, muito menos no primeiro. A afirmação é verificável em um comando, num documento cuja §5 inteira existe para provar cuidado com dados.

O conteúdo do `.gitignore` está correto e bem pensado (inclui `!.env.example` e o `.cache_analises.json`). O erro é só a afirmação sobre o histórico — o que o torna pior, não melhor: é uma afirmação gratuita, que não precisava ser feita, sobre uma coisa que já estava certa.

**Correção:** trocar por "o `.gitignore` cobre `.env`, `.env.*` e chaves, com `!.env.example` para preservar o template" e — mais importante — commitar o `.gitignore` antes de qualquer outra coisa entrar no repositório.

### A-3 — DG-5 descreve um README que não existe

**Local:** §5, DG-5.

> "O README declara explicitamente que o corpus é sintético, para que um avaliador não presuma o contrário."

Não há README no projeto. O único arquivo do primeiro commit era `README.md`, e ele está deletado na árvore de trabalho (`D README.md`). Escrito no presente do indicativo, DG-5 lê como constatação, não como requisito.

Isso vale duas críticas, não uma. A primeira é a factual. A segunda é maior: **o repositório de um portfólio sem README é o repositório que ninguém lê.** Todo o mérito real deste trabalho — a linha de base determinística, o resultado nulo publicado, a verificação de citação — está enterrado em `_bmad-output/`, sob uma hierarquia de artefatos de processo que um avaliador não vai navegar. O primeiro parágrafo do README é o único texto com leitura garantida, e ele não existe.

**Correção:** escrever o README antes de polir mais qualquer artefato de planejamento. Três blocos: o que o projeto faz, o resultado da medição (incluindo o empate e o "só o texto livre"), como rodar. O corpus sintético é uma linha dentro disso, não o motivo do arquivo.

### A-4 — O documento não distingue o que foi medido do que foi apenas escrito

**Local:** §6 inteira; §3 e §4 contra o código existente.

A §6 está toda no presente do indicativo — "Rejeita antes de qualquer chamada paga", "Aguarda e repete a chamada", "Encerra imediatamente com a causa nomeada". Nenhum desses comportamentos existe. `classificador.py` não tem `try/except` em volta de `analisa_lote`: uma indisponibilidade da API derruba a execução inteira, o que contradiz NFR-5 diretamente. Não há retry, não há validação de schema, não há rejeição de ID duplicado no caminho de produção (só um `assert` dentro do `autoteste` de `baseline.py`).

Contando: de 14 FRs e 9 NFRs, o código exercita quatro — FR-5 (parcial), FR-6, FR-7 e NFR-6. Isso é perfeitamente normal para um PRD, que é prospectivo por natureza. **O que não é normal é o mesmo documento carimbar "Medido em 2026-08-06" em alguns pontos e usar o mesmo tempo verbal para o que não existe em nenhum ponto.** O leitor não tem como saber qual é qual sem abrir o código, e quem abrir o código vai encontrar as duas categorias misturadas.

**Correção:** uma coluna de estado em §3, §4 e §6 — `medido` / `implementado` / `especificado`. É a mudança de maior retorno em todo o documento: preserva cada requisito, custa uma coluna, e converte a acusação de inflação numa demonstração de rastreabilidade.

### A-5 — O SPEC, declarado contrato canônico, contradiz o PRD em três números

**Local:** cabeçalho do PRD (`spec:`) e §9, Q-3/Q-7, contra `SPEC.md` §Resolved.

O PRD diz 19 marcações e 38%. O `SPEC.md` diz, na seção Resolved, *"o julgamento humano marcou 36% da base"* e *"`docs/gabarito.csv`, 18 de 50"*. O `risk-signals.md` está atualizado (v2, 19, 38%); o SPEC ficou na v1.

O PRD abre declarando que não repete o SPEC porque o SPEC é o contrato. Um avaliador que segue esse ponteiro cai num contrato desatualizado — e a discrepância é justamente no número que sustenta duas resoluções de questão aberta (Q-3 e Q-7) e a contramétrica CM-1.

**Correção:** atualizar `SPEC.md` §Resolved. Se a arquitetura documental é "o SPEC é canônico", uma divergência numérica entre os dois é uma falha de contrato, não uma erratazinha.

### A-6 — O limiar de CM-1 não tem derivação, e a medição encostou nele por causa da mesma revisão de C-2

**Local:** §7.2, CM-1.

> "Acima de 40%, a fila deixou de ordenar qualquer coisa e virou uma lista com adjetivo"
> "**Medida em 2026-08-06:** o julgamento humano ocupou 38% da base [...] Abaixo do limiar, mas com folga de dois pontos — a contramétrica está útil e apertada, não folgada."

Nada no repositório justifica 40%. Não é derivado de capacidade de atendimento, de tempo de leitura do gestor, nem de qualquer coisa medida — é um número redondo. E os "dois pontos de folga" só são dois porque a revisão v1→v2 moveu a ocupação de 36% para 38%; contra o gabarito v1 a folga era o dobro.

Chamar isso de "apertada, não folgada" é interpretar um limiar arbitrário como se ele tivesse sido posto à prova. Uma contramétrica cuja única evidência de calibragem é que a medição passou raspando não está calibrada — está sorteada.

**Correção:** ou derivar o limiar de algo real (quantos casos por dia uma pessoa consegue atender é um número que existe e que o PRD poderia assumir como `[ASSUMPTION]`, como fez corretamente em NFR-1), ou marcá-lo como arbitrário. Cortar a frase da "folga apertada": ela argumenta a favor de um número que o documento não defende.

---

## Médio

### M-1 — NFR-2 é contradito pelo código que existe

**Local:** §4.1, NFR-2; `classificador.py:24`.

> "**NFR-2** — O tamanho de lote é configurável sem alteração de código"

`TAMANHO_LOTE = 10` é uma constante de módulo. Mudar o lote é, literalmente, alterar código. É o único NFR que o código atual viola ativamente em vez de simplesmente não implementar.

**Correção:** `TAMANHO_LOTE = int(os.getenv("TAMANHO_LOTE", 10))` — uma linha — ou remover NFR-2 até que exista CLI. A segunda opção é mais defensável: com uma base de 50 linhas, um lote configurável é calibragem que ninguém vai fazer.

### M-2 — Metade das métricas nunca foi medida, na mesma lista onde outras dizem "Medido em"

**Local:** §7.1, M-2 a M-5; §7.2, CM-3 e CM-4.

M-2 (integridade da evidência no relatório final) não pode ter sido medida: não existe relatório final. M-3 (tempo) e M-4 (custo) não têm nenhum número no repositório — e o cache de A-1 torna qualquer medição de tempo ou custo sem sentido, porque uma execução com cache faz zero chamadas. M-5 é uma pergunta sem método.

Lado a lado com M-1 e CM-1/CM-2, que carregam data e valor, isso cria a impressão de que a seção inteira foi medida.

**Correção:** valor "não medido" explícito em cada uma. Para M-3 e M-4, uma medição real custa uma execução com `usar_cache=False` e um `time.perf_counter()` — vale mais que a estimativa, e o PRD ganharia o direito de afirmar NFR-1 e NFR-3.

### M-3 — NFR-4 é satisfeito por um cache que o SPEC lista como não-objetivo

**Local:** §4.2, NFR-4; contra `SPEC.md` §Non-goals e `roadmap.md` §v2.

> "**NFR-4** — O sistema não repete chamadas de LLM dentro de uma mesma execução para a mesma reclamação."

Dentro de uma mesma execução, nada no desenho jamais repetiria uma chamada — o loop percorre lotes disjuntos. O requisito não exclui nenhum comportamento plausível. Enquanto isso, o cache que de fato existe atravessa execuções e está explicitamente diferido nos não-objetivos do SPEC e no v2 do roadmap.

Ou seja: o documento numera uma garantia que ninguém ameaçava e não menciona a que já foi construída fora do escopo declarado.

**Correção:** remover NFR-4. Registrar o cache onde ele está — ferramenta de desenvolvimento para não queimar cota durante a calibragem — e dizer que ele não faz parte do pipeline. Um parágrafo em §8 resolve, e é mais informativo que o NFR.

### M-4 — A §5 é cerimônia corporativa sobre um CSV sintético de 50 linhas

**Local:** §5 inteira.

Cinco cláusulas numeradas de governança de dados para um arquivo que o próprio DG-1 confirma não conter dado pessoal nenhum. DG-4 duplica NFR-9. DG-2 e DG-3 legislam sobre uma "base real" que Q-5 admite não existir, não ter origem definida, nem formato. DG-5 é instrução de redação de README, não requisito de sistema.

O parágrafo de abertura da §5 é bom e defende a existência da seção — o produto de fato manda texto de consumidor para uma API de terceiro, num repositório público. Mas o conteúdo que se segue tem cinco vezes o tamanho que o problema comporta.

**Correção:** colapsar em duas cláusulas. *"Só corpus sintético é versionado (verificado em 2026-08-06). Base real ou relatório gerado a partir dela nunca entram no repositório, e citações literais herdam os dados pessoais do texto original."* Os outros três itens ou são duplicatas (DG-4) ou não são requisitos (DG-5).

### M-5 — O PRD declara que não repete o SPEC e repete

**Local:** nota de abertura, contra FR-3, FR-6, FR-7, FR-9, FR-12 e M-1.

> "As capacidades, restrições técnicas, contrato de estado e diagramas vivem em `SPEC.md` [...] Este PRD não os repete."

FR-6 reformula o *success* de CAP-4. FR-7 reformula CAP-5. FR-9 reformula CAP-8. FR-12 reformula o *success* de CAP-7. M-1 reproduz a frase dos 3% de contradição do gabarito quase palavra por palavra a partir de CAP-6.

Não é grave em si — redundância entre PRD e SPEC é comum. É grave porque o documento abre reivindicando a disciplina que não cumpre, e essa é a primeira coisa que o leitor testa.

**Correção:** ou cortar os cinco requisitos redundantes e deixar só as referências `Realiza CAP-N`, ou reescrever a nota de abertura para o que o documento realmente faz: *"onde este PRD toca uma capacidade do SPEC, ele acrescenta o comportamento observável que a capacidade não especifica."* A segunda é mais honesta e não exige mexer em nada.

### M-6 — M-5 não é uma métrica

**Local:** §7.1, M-5.

> "Uma pessoa que nunca viu a base consegue dizer, olhando só o relatório, qual produto está pior e como o cliente se sente com a marca."

Sem método, sem n, sem critério de reprovação, sem quem julga. Não é mensurável nem falsificável — é a descrição do sucesso, que já está no *Success signal* do SPEC.

Aparece numa lista onde as outras entradas têm número e data, o que empresta a ela um rigor que ela não tem.

**Correção:** promover para critério de aceitação em §8 ou deixar como está mas fora da lista numerada de métricas. Se ficar como métrica, precisa de protocolo: *"duas pessoas que não viram a base, cinco minutos com o HTML, acertam produto pior e sentimento predominante"*. Com n=2 já é mais do que zero. (E note C-3: hoje a segunda metade da pergunta tem resposta única.)

### M-7 — Q-4 nomeia a decisão mais importante do projeto e não a toma

**Local:** §9, Q-4.

> "Mantê-las no código apostando na base real, ou removê-las até existir base que as exercite? **É a decisão que separa um sistema honesto de um sistema decorativo.**"

A frase está certa e é a melhor do documento. O problema é que ela fica em aberto — e o `risk-signals.md` já decidiu na prática (*"As parcelas não exercidas permanecem no código com peso baixo"*), e o `classificador.py` já implementou `ameaca_explicita`, que rendeu 0 de 50.

Escrever "é a decisão que separa X de Y" e não decidir é a construção retórica que um avaliador lê como consciência do problema sem apetite pela consequência. Pior: a decisão já foi tomada em outro artefato, sem o PRD registrar.

**Correção:** decidir no PRD e assumir. A decisão defensável é manter, com uma linha de justificativa: *"mantidas com peso baixo e marcadas como não exercidas; o custo de manter é uma chave no schema, o custo de remover é reescrever o prompt quando aparecer a primeira base que as exerça."* Depois mover Q-4 para Resolvidas.

---

## Baixo

### B-1 — Requisitos óbvios demais para receber número

**Local:** FR-4, FR-13, FR-14, NFR-7.

FR-14 exige que o relatório esteja em português do Brasil, num projeto integralmente em português do Brasil sobre reclamações de consumidor brasileiro. NFR-7 exige que duas execuções sobre o mesmo arquivo produzam os mesmos identificadores — os identificadores vêm do arquivo; a alternativa não é implementável por acidente. FR-13 (data e total no relatório) e FR-4 (não sobrescrever silenciosamente) são higiene.

Nenhum é errado. O efeito é de diluição: com 23 requisitos numerados dos quais quatro são inevitáveis, o leitor deixa de tratar a numeração como sinal.

**Correção:** rebaixar para uma linha de "higiene de saída" sem numeração. FR-11 e FR-12, que são decisões de produto reais e discutíveis, ganham peso na mesma proporção.

### B-2 — "Plataforma" no título, contra o que a §8 diz que o produto é

**Local:** título; §8.

A §8 nega interface, filtro, ordenação, exportação, autenticação, histórico e agendamento. O que sobra é um script que lê um CSV e escreve um HTML. "Plataforma" é a primeira palavra que um avaliador lê e a última que o produto entrega.

**Correção:** o nome honesto descreve melhor e impressiona mais — algo como "Pipeline de triagem de reclamações". Um nome modesto sobre um trabalho com linha de base medida lê como confiança; um nome inflado sobre o mesmo trabalho convida à conferência.

### B-3 — Duas personas com "necessidades opostas" para uma pessoa que manda um HTML por e-mail

**Local:** §2.

> "Dois papéis distintos, com necessidades opostas. Confundi-los é o erro mais provável do projeto."

As necessidades não são opostas; são sequenciais — um roda, o outro lê. E "o erro mais provável do projeto" é uma afirmação forte para um risco que se materializa em, no máximo, imprimir um log no HTML.

Dito isso, a restrição embutida é legítima e produtiva: o leitor nunca vê terminal, o que é o que justifica FR-9 (arquivo único, sem rede). O problema é a dramatização, não a distinção.

**Correção:** manter os dois papéis e as duas UJs — são curtas e carregam requisito real. Cortar a frase do "erro mais provável".

### B-4 — Todas as datas do documento são o mesmo dia

**Local:** §1, §5, §7, §9 — oito ou mais ocorrências de "2026-08-06".

"Validada em", "Verificado em", "Medido em", "RESOLVIDA em" — todas na data de criação do documento. Carimbo de data que nunca varia não registra nada; é forma de trilha de auditoria sem a função.

**Correção:** manter em M-1 e nas contramétricas, onde a data vai variar quando a medição for refeita, e cortar do resto.

### B-5 — Detalhes de repositório que um avaliador confere em trinta segundos

**Local:** fora do PRD, mas afetam a leitura dele.

`classificador.py` importa `pydantic` e `pyproject.toml` não a declara (funciona por dependência transitiva de `google-genai` — até o dia em que não funcionar). Existe um `.pytest_cache/` e nenhum arquivo de teste pytest; os autotestes são `assert` em `__main__`, o que é uma escolha defensável, mas o diretório órfão sugere um framework que foi tentado e abandonado.

**Correção:** declarar `pydantic` nas dependências; apagar `.pytest_cache/` (já está no `.gitignore`, então é só limpeza local).

### B-6 — Contramétricas com critério assimétrico

**Local:** §7.2, CM-3 e CM-4.

CM-1 tem limiar (40%) e CM-2 tem interpretação nos dois extremos. CM-3 diz só "subindo, perde significado" e CM-4 diz "acima de zero merece investigação" — que é limiar, mas para o caso trivial.

Uma contramétrica sem número não dispara; ela comenta.

**Correção:** dar limiar a CM-3 quando ela for redesenhada conforme C-4 (a versão útil mede concentração em rótulo genérico, e aí um limiar tipo "nenhum rótulo genérico entre os três primeiros do ranking" é natural).

---

## O que preservar

Esta seção não é cortesia. É a lista do que não pode ser perdido no polimento, porque é o que faz este repositório valer a leitura.

**1. `baseline.py` existe.** É o gesto mais maduro do projeto inteiro e o mais raro em portfólios com LLM: construir deliberadamente a alternativa barata que pode matar a sua ideia, e rodá-la antes de defender a ideia. O docstring diz *"É a barra que o pipeline com Gemini precisa superar para justificar existir"*, e a última linha do `main()` imprime a barra. Isso, sozinho, separa o autor da maioria dos candidatos. **Precisa estar no primeiro parágrafo do README, não no `_bmad-output/`.**

**2. O classificador vê apenas o texto livre, por decisão declarada.** O docstring de `classificador.py`: *"o modelo vê apenas o texto livre da reclamação, nunca o título. O título desta base é canônico (18 valores fixos) e entrega a resposta; base real não tem isso. Ganhar sem o título é ganhar de verdade."* É desenho de experimento correto, é a diferença entre medir e se enganar, e é o único argumento honesto pela existência do pipeline. Está fora do PRD. **Promover para a §1.**

**3. A CM-2 e o autoteste que a sustenta.** *"Em zero constante, indica que a verificação pode não estar sendo exercida"* — e depois, medido: *"o número bom aqui é indistinguível de mecanismo morto sem o teste sintético"*. O autoteste de `classificador.py` injeta uma citação falsa e verifica que ela cai, enquanto a verdadeira sobrevive. Desconfiar do próprio resultado bom e escrever o teste que distingue as duas explicações é maturidade de engenharia de verdade, não vocabulário de engenharia.

**4. A admissão de que a acurácia está superestimada.** §1: *"as descrições se repetem (30 textos distintos em 50 linhas), o que faz qualquer acurácia medida aqui superestimar o desempenho sobre linguagem real."* Está na abertura, antes de qualquer número bom, onde é caro admitir. A maioria dos documentos põe isso numa nota de rodapé, se põe.

**5. O `[ASSUMPTION]` em NFR-1.** Marcar explicitamente o número que foi derivado em vez de medido, com a derivação à vista. É exatamente o que falta em CM-1 (A-6) — o autor já sabe fazer, só não aplicou de forma consistente.

**6. FR-11 e FR-12.** *"como conteúdo visível e não como detalhe expansível"* e *"volume não equivale a gravidade — o produto mais reclamado tende a ser o mais vendido"*. São decisões de produto reais, falsificáveis, e revelam que o autor pensou no que o gestor faz de errado com o relatório. Valem mais que os outros doze FRs somados.

**7. A restrição "o modelo extrai, código determinístico julga".** Está no SPEC e atravessa o código: `valida_evidencia` e `pontua` são puros e testáveis, o LLM só preenche campos. É a arquitetura certa para este problema e é defensável numa entrevista sem hesitar.

**8. NFR-6, casamento por identificador e não por posição.** Implementado (`faltando = [...]`), documentado no `state-contract.md` com o motivo (*"o modo mais silencioso de corromper a base inteira"*). Um NFR que existe, tem razão de ser articulada e é exercitado pelo código.

**9. O registro auditável da revisão v1→v2 em `risk-signals.md`.** *"A revisão foi aceita com o argumento à vista, não para melhorar métrica. A mesma correção foi aplicada à regra determinística, para que a comparação não fosse enviesada a favor do LLM."* Preservar o `gabarito-v1.csv` no repositório para que qualquer um possa conferir é a decisão certa. C-2 não pede que isso seja escondido — pede que o número que ele implica (0,83 contra 0,85) apareça também no PRD.

**10. As contramétricas existirem.** Números que, subindo, indicam que o produto está falhando apesar das métricas parecerem boas. Poucos PRDs de portfólio têm isso. As críticas em A-6, C-4 e B-6 são sobre calibragem de três delas — não sobre a ideia, que está certa.

---

## Contagem

| Severidade | Achados |
|---|---|
| Crítico | 4 |
| Alto | 6 |
| Médio | 7 |
| Baixo | 6 |
| **Total** | **23** |

## A pergunta desconfortável da entrevista

Se eu tivesse dez minutos com o autor, seriam estas três, nesta ordem:

1. *"Você mediu que o LLM empata com seis strings. Também rodou sentimento e produto na mesma execução. Por que só o primeiro resultado está no PRD?"* (C-1, C-3, C-4)
2. *"O gabarito v1 dá F1 0,83, abaixo do seu alvo de 0,85. O v2 dá 0,86. A diferença é uma marcação que você acrescentou depois de ver o modelo marcá-la. Como você me convence de que o alvo não foi atingido movendo o alvo?"* (C-2)
3. *"O relatório HTML não existe, mas cinco requisitos e duas métricas descrevem o comportamento dele no presente do indicativo. Como eu distingo, lendo este documento, o que você construiu do que você planeja?"* (A-4)

A boa notícia: as três têm resposta boa e curta, e o material para dá-la já está no repositório. É trabalho de meio dia — não de reescrita.
