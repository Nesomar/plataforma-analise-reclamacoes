# Reconciliação SPEC ↔ PRD

**Data:** 2026-08-06
**Alvo:** `_bmad-output/planning-artifacts/prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md`
**Input:** `SPEC.md` + companions `risk-signals.md`, `state-contract.md`, `roadmap.md`, `architecture-diagrams.md`

> **Premissa aceita.** O PRD declara que não repete capacidades, restrições técnicas, contrato de estado e diagramas. Isso é decisão registrada e **não** é tratado como lacuna neste relatório. O que se procura aqui é: contradição factual, contradição interna nos companions, ideia qualitativa perdida na tradução para FR/NFR, e desalinhamento de Questões Abertas.

**Método.** Além da leitura cruzada, os números foram recalculados contra os arquivos reais do repositório (`docs/reclamacoes_reclameaqui.csv`, `docs/gabarito.csv`, `docs/gabarito-v1.csv`). Onde há divergência entre documentos, o dado medido decide quem está certo.

### Verdade de campo apurada

| Fato | Valor medido |
|---|---|
| Linhas na base | 50 |
| `ID_Reclamacao` únicos | 50 de 50 |
| Empresas distintas | 14 |
| Descrições distintas | 30 |
| Títulos (categorias) distintos | **18** |
| Grupos de texto idêntico | 10 (máx. 4 repetições) |
| Datas | todas em 2026 |
| `gabarito.csv` (v2) | **19 `sim` / 50 = 38%** |
| `gabarito-v1.csv` | 18 `sim` / 50 = 36% |
| Delta v1→v2 | exatamente `RA645276696` |
| Regra "categoria de dinheiro retido" | TP 16 · FP 2 · FN 3 · P 88,9% · R 84,2% · **F1 0,865** |
| FP da regra | 2 × *Cobrança indevida no cartão de crédito*, ambas `Status` = Respondida |
| FN da regra | *Aplicativo travando*, *Plano de saúde negou meu exame*, *Mensalidade aumentou sem aviso* |
| Grupos texto+status idênticos com marcação divergente | 1 (*Aplicativo travando*, ambos `Resolvido`) |

---

## 1. Contradições numéricas e factuais

### C-1 — `SPEC.md` carrega o gabarito v1; companion e PRD carregam o v2 · **Alta**

`SPEC.md` § Resolved:

- *"Corte da fila — resolvido pelo gabarito: o julgamento humano marcou **36%** da base"*
- *"Gabarito de aceitação — resolvido: `docs/gabarito.csv`, **18 de 50** na fila"*

`risk-signals.md` § O score: *"Versão vigente: **v2, 19 marcadas (38%)**, em `docs/gabarito.csv`"*.
PRD M-1 e Q-3: *"19 de 50"*, *"38%"*.

**Medido:** `docs/gabarito.csv` tem 19 `sim`; os 18/36% são de `docs/gabarito-v1.csv`. **O PRD está certo e o SPEC está desatualizado** — o SPEC não foi reescrito quando a revisão v1→v2 foi aceita.

Consequência prática, e não cosmética: o SPEC afirma 36% contra o limiar de 40% da CM-1 (folga de 4 pontos); a realidade é 38% (folga de **2 pontos**). O argumento que fecha a Q-3 ("binário fica no v1") sobrevive, mas com metade da margem que o SPEC anuncia.

**Ação:** corrigir `SPEC.md` § Resolved para 19 / 38%, citando `docs/gabarito-v1.csv` como histórico. O PRD não muda.

### C-2 — A folga de 2 pontos entre a ocupação real (38%) e a contramétrica CM-1 (40%) não é declarada em lugar nenhum · **Média**

Nem SPEC nem PRD notam que o **próprio julgamento humano** ocupa 38% da fila. Isto é, um classificador perfeito — que reproduzisse o gabarito linha a linha — dispararia a CM-1 com dois pontos de folga, e qualquer FP a mais a estoura. A CM-1, como escrita, é quase impossível de satisfazer com folga sob corte binário.

Isso não invalida a CM-1; torna-a uma contramétrica de gatilho quase imediato, o que precisa ser dito. Hoje o PRD apresenta 40% como uma margem confortável ("abaixo do limiar", Q-3) sem revelar quão pouco falta.

**Ação:** no PRD, anotar em CM-1 que o piso humano é 38% e que a contramétrica opera com folga de 2 pontos — é sinal antecipado de que os níveis do v2 são necessários, não um alarme de defeito.

### C-3 — O número "cerca de 3%" de inconsistência do gabarito não fecha com nenhum denominador · **Baixa**

Propagado idêntico por três documentos: `risk-signals.md` ("Taxa de inconsistência de cerca de 3%"), `SPEC.md` CAP-6 ("se contradiz em cerca de 3% dos casos de texto idêntico") e PRD M-1 ("se contradiz em cerca de 3% dos casos").

**Medido:** 1 grupo divergente em 10 grupos de texto idêntico (10%); 2 linhas afetadas em 50 (4%); 1 par divergente entre 20 linhas em grupos repetidos (5%). Nenhuma leitura produz 3%.

O fato qualitativo — *o gabarito não concorda consigo mesmo, logo 100% é impossível* — é sólido e está correto. Só o número é frouxo, e está repetido em três lugares como se fosse medido.

**Ação:** substituir por formulação verificável: *"em 1 dos 10 grupos de texto idêntico a marcação humana diverge (2 linhas de 50)"*. Corrigir nos três documentos.

### C-4 — PRD UJ-1: "a fila tem cinco itens" contradiz a ocupação medida · **Média**

PRD § UJ-1: *"vê que a fila tem cinco itens com citação visível em cada um"*.

Com ocupação de 38% medida sobre a base do projeto, uma execução sobre 50 reclamações produz ~19 itens, não 5. Cinco itens sobre 50 seriam 10% — número que só aparece no corpus de referência de cinco reclamações do `risk-signals.md`, que é outra coisa.

A jornada não fixa o tamanho da base ("a base do mês"), então não é falso em sentido estrito — mas a única imagem concreta que o PRD dá da fila mostra um relatório enxuto, quando o v1 é **sabidamente inflado** (Non-goal explícito do SPEC). A ilustração desmente a limitação declarada.

**Ação:** ajustar UJ-1 para um número coerente com 38%, ou explicitar o tamanho da base na jornada. A fila enxuta é o comportamento do v2, não do v1.

### C-5 — Dois "corpus de referência" diferentes, ambos sem nome próprio · **Média**

`SPEC.md` § Success signal e CAP-4 falam em "corpus de referência". Existem dois candidatos:

- o **corpus de 5 reclamações** — `risk-signals.md` § Gabarito de aceitação, com 3 dos 5 na fila;
- a **base de 50** — `docs/gabarito.csv`, 19 marcadas, que é contra quem CAP-6 mede F1.

CAP-4 diz *"os cinco tipos de exposição factual do catálogo são reconhecidos sobre o corpus de referência"*. Sobre a base de 50 isso é **impossível**: o próprio `risk-signals.md` § Pesos do v1 registra `registro_contraditorio` como *"Não exercida — nenhum caso limpo nesta base"*. O critério só é satisfazível sobre o corpus de 5, onde o sinal B aparece 5 de 5.

O PRD nunca menciona o corpus de 5 e resolve tudo silenciosamente sobre a base de 50.

**Ação:** nomear os dois corpora distintamente no SPEC (ex.: *corpus de aceitação* com 5 e *base de calibração* com 50) e amarrar cada critério de sucesso a um deles. Sem isso, CAP-4 é literalmente inatingível.

---

## 2. Contradições internas nos companions

### C-6 — `risk-signals.md` tem duas tabelas de métrica em desacordo: a terceira nunca saiu do gabarito v1 · **Alta**

Mesmo arquivo, mesmas regras, números diferentes:

| Regra | § "O resultado que encerra a etapa" | § "Desempenho das regras candidatas" | Medido (v2) |
|---|---|---|---|
| Categoria de dinheiro retido | P 89% · R 84% · F1 **0,86** | P 88% · R 83% · F1 **0,86** | **P 88,9% · R 84,2% · F1 0,865** |
| Categoria + `Status` ≠ Respondida | P 100% · R **68%** · F1 **0,81** | P 100% · R **72%** · F1 **0,84** | **R 68,4% · F1 0,81** |
| Apenas `Status` | — | P 40% · R **44%** · F1 0,42 | R = 8/19 = **42%** |

Recalculado: 88%/83%, 72%/0,84 e 44% são exatamente os valores que saem com **18** marcações no denominador. A tabela "Desempenho das regras candidatas" é inteira da era v1 e ficou para trás quando o gabarito virou v2. A primeira tabela está correta.

Efeito colateral que já vazou: o **F1 0,42 do `Status` sozinho** — o único número daquela tabela que foi citado adiante — está reproduzido em `SPEC.md` § Resolved e no PRD Q-6. Sobre o v2 o valor é **0,42 também** (8 TP, 12 FP, 11 FN → P 40%, R 42%, F1 0,41), então a conclusão ("pior que a categoria, não vira parcela") se sustenta. É sorte, não rastreabilidade.

**Ação:** recalcular a tabela "Desempenho das regras candidatas" contra o v2 ou apagá-la — ela duplica a primeira tabela sem acrescentar nada.

### C-7 — `risk-signals.md` declara o `Status` como questão aberta e o resolve na mesma página · **Alta**

Linha 42: *"Não foi adotado como parcela porque o peso frente às três existentes é decisão em aberto — **ver Open Questions em `SPEC.md`**"*.

Vinte linhas adiante, § Pesos do v1 já atribui `Status` = Respondida com peso **−1**. `SPEC.md` § Resolved já registra a questão como **resolvida** em 2026-08-06. As Open Questions do `SPEC.md` **não contêm** nenhum item sobre `Status` — a referência cruzada aponta para o vazio.

**Ação:** reescrever a linha 42 para apontar `SPEC.md` § Resolved e § Pesos do v1 deste mesmo arquivo.

### C-8 — "três parcelas" (diagramas) × seis parcelas (risk-signals) · **Média**

`architecture-diagrams.md`, tabela de nós: *"`pontuar` — Aplica **as três parcelas** e a aritmética de prazo."*
`risk-signals.md`, § Pesos do v1: **seis** linhas — dinheiro retido (3), `Status` = Respondida (−1), ameaça explícita (3), dano continuado (2), registro contraditório (2), prazo estourado (1).
`risk-signals.md` linha 42 fala em *"as três existentes"*, ecoando a mesma contagem antiga.

"Três parcelas" é vocabulário do desenho original que sobreviveu à medição. Quem implementar `pontuar` lendo o diagrama vai codificar metade do score.

**Ação:** trocar "as três parcelas" por "as parcelas de `risk-signals.md` § Pesos do v1" — contagem em um lugar só.

### C-9 — "Dez categorias inteiras receberam zero marcações" — são nove, e a décima está duplicada · **Média**

`risk-signals.md` lista como zeradas: internet instável, voo cancelado, entregador que arremessou o pacote, mau atendimento, roupa no tamanho errado, propaganda enganosa, estofado rasgado, ração estragada, brinde não enviado e **cancelamento dificultado**.

**Medido:** as nove primeiras têm de fato 0 marcações. A décima não existe com esse nome; a categoria real mais próxima é *"Não consigo cancelar assinatura"*, que tem **1 de 1** e já aparece na tabela das seis categorias marcadas, logo acima. O mesmo item foi contado dos dois lados.

**Ação:** corrigir para nove categorias, com os títulos exatos do CSV.

### C-10 — A "única dimensão" tem uma exceção medida que o companion não registra · **Média**

`risk-signals.md`: *"Uma única dimensão explica quase tudo: **a empresa está com dinheiro do cliente**. Seis categorias concentram 16 das 19 marcações."* Os 16/19 estão corretos. As **3 marcações restantes** nunca são nomeadas.

**Medido**, são: *Aplicativo travando* (1/2 — a inconsistência conhecida), *Mensalidade aumentou sem aviso* (1/3 — mencionada só de passagem como "dano continuado não sustentada") e **_Plano de saúde negou meu exame_ (1/3)**, que não aparece em ponto algum de nenhum documento.

*Plano de saúde negou meu exame* é o caso mais interessante da base: marcado pelo humano, sem dinheiro retido, e é um dos três FN da regra vencedora. É a evidência de que a dimensão única **não** explica tudo, e é justamente a que sumiu.

**Ação:** nomear os três FN explicitamente e reconhecer *negativa de cobertura* como dimensão candidata para a base real — reforça a Q-4 em vez de enfraquecê-la.

---

## 3. Ideias qualitativas do SPEC que a estrutura de FR/NFR perdeu

Nenhuma delas é restrição técnica; todas têm efeito visível no produto, e é por isso que a exclusão deliberada de "capacidades e restrições técnicas" não as cobre.

### G-1 — *"As heurísticas de risco jurídico são engenharia, não parecer jurídico"* não vira nada no produto · **Alta**

`SPEC.md` § Constraints fecha com: *"Adequadas a estudo; produção exigiria validação profissional."*

O PRD tem **zero** requisitos derivados disso. E o produto entrega a um gestor uma tela chamada fila de risco jurídico, ordenada por score, com citação literal do cliente ao lado. FR-11 exige a citação *visível, não expansível* — desenho que maximiza a credibilidade do item. Nada no relatório diz que aquilo não é parecer.

Esta é a lacuna mais consequente do documento: é a única onde a ausência de um requisito produz risco real de uso indevido, num artefato que circula por e-mail e sai do contexto de quem o gerou.

**Ação:** criar **FR-15** — *o relatório exibe, no próprio corpo e não em rodapé, que a classificação de risco é heurística de engenharia e não avaliação jurídica* — e estender DG-5 para o README.

### G-2 — *"Falso positivo custa mais que falso negativo"* é assimétrico; F1 é simétrico · **Alta**

`SPEC.md` § Constraints: *"Fila inflada destrói a confiança do gestor no relatório inteiro; risco perdido custa menos que relatório abandonado."*

CAP-6 e PRD M-1 aceitam o sistema por **F1 ≥ 0,85** — média harmônica que pesa precisão e recall **igualmente**. A métrica de aceitação contradiz a economia declarada do produto: um sistema com P 80% / R 92% e outro com P 92% / R 80% passam os dois, e o SPEC diz explicitamente que o segundo é melhor.

O PRD reconhece a assimetria só de lado, na CM-1, e como contramétrica de ocupação — não como critério de aceitação.

**Ação:** ou adotar F-beta com β < 1 (ex.: F0.5), ou manter F1 e acrescentar um piso de precisão à M-1 (ex.: *F1 ≥ 0,85 **e** precisão ≥ 88%*). A regra medida já entrega P 88,9%, então o piso não é aspiracional — é o observado.

### G-3 — *"O modelo extrai; código determinístico julga"* não tem eco no PRD, e a NFR-7 corre no sentido oposto · **Alta**

O princípio de desenho mais central do SPEC — *score, contagem, ranking, ordenação e aritmética de prazo nunca passam pelo LLM* — não aparece no PRD sob nenhuma forma.

Cabe argumentar que é restrição técnica, exceto que a **NFR-7** já legislou sobre a matéria e legislou frouxo: *"A classificação pode variar entre execuções; a identidade da reclamação, não."* Lida isolada, ela autoriza que a fila inteira mude de ordem a cada rodada. O que o SPEC garante é mais forte e mais vendável: dada a mesma extração, **score, ordenação e agregados são bit a bit idênticos** — só a extração do LLM varia.

Não é repetição de restrição técnica; é a diferença entre um relatório auditável e um oráculo.

**Ação:** reescrever a NFR-7 para separar as duas camadas — *a extração pode variar; o julgamento sobre uma extração fixa é determinístico e reproduzível.*

### G-4 — A honestidade do `risk-signals.md` sobre o LLM não se paga chega ao PRD sem consequência · **Média**

`risk-signals.md` conclui com dois parágrafos deliberadamente desconfortáveis: *"O LLM não se paga aqui... o pipeline de agentes é infraestrutura cara para um resultado que um `in` entrega"* e o box *"Honestidade sobre o resultado"* (uma parcela só atinge F1 0,86; as outras quatro são aposta, não conclusão).

O PRD **carrega** o fato — M-1 diz *"o LLM não superou a regra nesta base"*, o que é mérito e vale registrar. Mas o fato morre ali. Nenhum FR, nenhuma métrica e nenhum item de governança faz alguma coisa com ele.

E o PRD declara, na § 1, que *"um avaliador técnico é parte do público"*. Para esse público, a comparação honesta LLM × regra determinística é o ativo mais valioso do projeto inteiro — e não há requisito nenhum de que ela apareça no entregável.

**Ação:** requisito de que o README (ou o próprio relatório) publique a comparação e o empate em F1 0,86. Custa um parágrafo e é a diferença entre portfólio e demo.

### G-5 — A assunção "por empresa ou agregada?" some do SPEC para o PRD, e a UJ-2 pressupõe a resposta · **Média**

`SPEC.md` § Assumptions: *"O relatório consolida a base inteira, sem filtro por empresa. A base contém 14 empresas distintas e nada define se a análise é por empresa ou agregada."* — reconhecidamente **em aberto**.

O PRD cita as 14 empresas (§ 1) e nunca mais volta ao ponto. A UJ-2 põe Ricardo, um gestor, decidindo *"a segunda-feira"* a partir da fila — o que só faz sentido se ele responde por todas as 14, ou se a base é de uma empresa só. A jornada resolveu por narrativa uma questão que o SPEC deixou explicitamente aberta.

Também colide com a § 2.2, que insiste que os dois papéis têm necessidades opostas e que confundi-los é "o erro mais provável do projeto": um leitor de 14 empresas e um leitor de uma empresa querem relatórios diferentes.

**Ação:** virar Questão Aberta do PRD (Q-8) ou fixar como decisão explícita na § 2.2. Não deixar a jornada decidir.

### G-6 — CAP-7 exige que os agregados fechem com a contagem por reclamação; nenhum FR/M cobre isso · **Baixa**

`SPEC.md` CAP-7 § success: *"Os números agregados batem com a contagem direta sobre a saída por reclamação."*

O PRD tem FR-12 (o aviso de que volume ≠ gravidade — realiza a **segunda** metade do CAP-7) e a CM-3 chega a dizer *"mesmo que os totais fechem"*, pressupondo a propriedade sem nunca exigi-la. A primeira metade — consistência aritmética entre o detalhe e o resumo — não tem requisito nem métrica.

**Ação:** um item em M-2 ou um FR curto: *soma dos agregados = contagem sobre a saída por reclamação, verificado a cada execução.*

---

## 4. Questões Abertas: correspondência

### Do SPEC para o PRD — completa

| `SPEC.md` § Open Questions | PRD § 9 | Situação |
|---|---|---|
| Produto não identificável | **Q-2** | Correspondida. O PRD vai além: FR-8 já decide *não descartar*, restando só o tratamento no ranking |
| Origem da base real | **Q-5** | Correspondida, e ampliada com "nem com que frequência" |
| Validade das parcelas não exercidas | **Q-4** | Correspondida, e melhor formulada que no SPEC — o PRD nomeia os números de cada parcela |

### Do PRD para o SPEC — completa

Q-1, Q-3, Q-6 e Q-7 estão riscadas como resolvidas e todas as quatro têm contrapartida em `SPEC.md` § Resolved. Nenhuma resolução do PRD é órfã.

### Desalinhamentos remanescentes

**OQ-1 — FR-8 fecha metade de uma Open Question sem o SPEC saber · Baixa.** O SPEC ainda oferece três opções (descartar / agrupar / marcar para revisão); o PRD já eliminou "descartar" via FR-8 e reduziu a questão ao tratamento no ranking. O SPEC deve absorver a eliminação, senão a Q-2 parece mais aberta do que é.

**OQ-2 — O SPEC registra uma resolução que o PRD não conhece · Baixa.** *"Prazo estourado sem data de evento — resolvido: parcela mantida com peso 1, reconhecidamente fraca nesta base."* Sem espelho no PRD. Como resolvida, não precisa virar questão — mas a fraqueza reconhecida pertence ao mesmo conjunto de apostas da Q-4 e deveria ser citada lá, senão a Q-4 lista três parcelas frágeis quando são quatro.

**OQ-3 — A questão do escopo por empresa não existe em nenhum dos dois como questão.** Ver G-5. É a única lacuna de Open Question genuinamente bidirecional: o SPEC a rebaixou a "assumption" e o PRD a perdeu de vez.

**OQ-4 — Numeração da § 9 fora de ordem · cosmética.** Q-1, Q-6, Q-7, Q-3, Q-2, Q-4, Q-5. As resolvidas foram empurradas para o topo. Legível, mas dificulta referência cruzada.

---

## 5. Lacunas estruturais: requisitos do PRD sem suporte no contrato de estado

`state-contract.md` se declara *"a única parte do v1 que não é aditiva"* — errar ali converte cada item do roadmap de plugin em reescrita. Três requisitos do PRD não têm onde morar nele.

### S-1 — `evidencia: list[str]` não sabe qual citação sustenta qual sinal · **Alta**

```python
sinal_a: bool
sinal_b: list[str]        # códigos do catálogo
evidencia: list[str]      # citações literais — lista plana, sem vínculo
```

Contra o que o SPEC exige:

- CAP-4: *"devolve, **para cada sinal**, a frase literal do texto que o sustenta"*
- CAP-5: *"citação fabricada anula **o sinal correspondente**"*
- `risk-signals.md`: *"sem citação que sustente intenção, o sinal A não sobrevive"* — derrubada seletiva de A sem tocar em B
- PRD FR-6/FR-7 e o diagrama de fluxo da evidência, ambos operando sinal a sinal

Com uma lista plana de citações, "o sinal correspondente" é indeterminável. Uma reclamação com `sinal_a=True` e `sinal_b=["cobranca_indevida"]` e duas citações não permite saber qual cai quando uma falha na verificação. **A regra central do sistema — a defesa primária contra falso positivo — não é implementável sob o contrato como está escrito.**

**Ação:** `evidencia: dict[str, list[str]]`, chaveado por `"sinal_a"` e pelos códigos do catálogo. Correção de uma linha agora; reescrita depois, por ser a parte não-aditiva.

### S-2 — Os contadores que a FR-2 exige não têm campo no `Estado` · **Média**

FR-2 obriga o sistema a reportar quatro números ao operador: lidas, analisadas com sucesso, com falha, e sinais derrubados na verificação. A CM-2 e a CM-4 monitoram dois deles.

`Estado` tem `reclamacoes`, `analises`, `scores`, `agregados`, `caminho_html`. "Lidas" e "analisadas" saem de `len()`; **falhas e derrubadas não existem em lugar nenhum** — a derrubada acontece dentro da verificação e o número morre ali. Só `agregados: dict` (sem tipo) poderia acomodá-los, por acidente.

**Ação:** campo explícito para os contadores de execução, ou tipar `agregados` de modo a incluí-los.

### S-3 — A NFR-5 exige que a reclamação falhada seja registrada; o `Analise` não representa "não analisada" · **Média**

NFR-5 e a linha *"Resposta do modelo malformada ou incompleta"* da § 6 exigem prosseguir e registrar a reclamação afetada como não analisada. `Analise` é um `TypedDict` com `sentimento` obrigatório (`Literal` de três valores, sem opção nula) e sem campo de estado. Não há como representar uma reclamação processada-e-falhada — só ausência da entrada, que é indistinguível de "ainda não processada".

Convive mal com a regra do próprio contrato (*"a etapa de análise detecta qual faltou e **registra a falha**"*) — que descreve exatamente o registro que a estrutura não comporta.

**Ação:** entrada de falha explícita, ou lista separada de identificadores não analisados no `Estado`.

---

## 6. Contradição PRD ↔ `roadmap.md`

### R-1 — Ordem de decisão do v2 · **Média**

`roadmap.md` § v2: *"**Decidir isso antes** de calibrar o corte binário — calibrar o corte errado é trabalho jogado fora."* Ou seja: os níveis de criticidade são **pré-requisito** para mexer no corte.

PRD Q-3: *"Binário fica no v1; níveis com prazo seguem no roadmap **sem urgência**."*

As duas afirmações são compatíveis apenas se o corte binário nunca for calibrado. Ninguém diz isso. Com a ocupação real em 38% contra o teto de 40% da CM-1 (ver C-2), a pressão para calibrar o corte é bem maior do que "sem urgência" sugere — e no momento em que alguém calibrar, terá violado a instrução do roadmap.

**Ação:** o PRD deve registrar a condição, não só a prioridade: *níveis ficam adiados **enquanto o corte binário não for tocado**; qualquer calibragem do corte reabre a decisão dos níveis primeiro.*

---

## 7. Resumo de ações

| # | Onde | Ação | Severidade |
|---|---|---|---|
| C-1 | `SPEC.md` § Resolved | 18/36% → 19/38%; citar `gabarito-v1.csv` como histórico | Alta |
| C-6 | `risk-signals.md` | Recalcular ou remover "Desempenho das regras candidatas" (tabela inteira é v1) | Alta |
| C-7 | `risk-signals.md` l.42 | Referência cruzada aponta para Open Question inexistente | Alta |
| G-1 | PRD (novo FR-15) | Disclaimer "não é parecer jurídico" visível no relatório | Alta |
| G-2 | PRD M-1 / SPEC CAP-6 | F1 simétrico contradiz "FP custa mais que FN" — piso de precisão ou F-beta | Alta |
| G-3 | PRD NFR-7 | Separar variabilidade da extração do determinismo do julgamento | Alta |
| S-1 | `state-contract.md` | `evidencia` precisa ser mapeada por sinal — parte não-aditiva | Alta |
| C-2 | PRD CM-1 | Declarar que o piso humano é 38% e a folga é de 2 pontos | Média |
| C-4 | PRD UJ-1 | "cinco itens" contradiz 38% de ocupação | Média |
| C-5 | `SPEC.md` | Nomear os dois corpora; CAP-4 é inatingível sobre a base de 50 | Média |
| C-8 | `architecture-diagrams.md` | "três parcelas" → seis | Média |
| C-9 | `risk-signals.md` | São nove categorias zeradas, não dez; a décima está duplicada | Média |
| C-10 | `risk-signals.md` | Nomear os 3 FN; *Plano de saúde* não aparece em documento algum | Média |
| G-4 | PRD | Requisito de publicar a comparação LLM × regra | Média |
| G-5 | PRD § 2.2 / Q-8 | Por empresa ou agregada — resolvido só pela narrativa da UJ-2 | Média |
| R-1 | PRD Q-3 | "sem urgência" × "decidir antes de calibrar" do roadmap | Média |
| S-2 | `state-contract.md` | Sem campo para os contadores da FR-2 | Média |
| S-3 | `state-contract.md` | Sem representação de reclamação não analisada (NFR-5) | Média |
| C-3 | 3 documentos | "cerca de 3%" não fecha com nenhum denominador | Baixa |
| G-6 | PRD M-2 | Nenhum requisito de que agregados fechem com o detalhe (CAP-7) | Baixa |
| OQ-1 | `SPEC.md` | FR-8 já eliminou "descartar" da Open Question de produto | Baixa |
| OQ-2 | PRD Q-4 | "prazo estourado" é a quarta parcela frágil, não citada | Baixa |
| OQ-4 | PRD § 9 | Numeração fora de ordem | Cosmética |

**Leitura geral.** O PRD está **mais correto que o SPEC** nos pontos onde os dois divergem — ele absorveu a revisão v1→v2 do gabarito e o SPEC não. A dívida real não está no PRD: está no `risk-signals.md`, que acumulou três camadas de números de épocas diferentes na mesma página, e no `state-contract.md`, que é a única peça não-aditiva do projeto e não suporta a regra que o projeto inteiro chama de defesa primária.
