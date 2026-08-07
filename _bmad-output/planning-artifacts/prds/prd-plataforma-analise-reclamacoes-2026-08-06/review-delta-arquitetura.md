# Revisão focada — delta do PRD contra dados, código e spine

**Escopo:** apenas FR-13 (marcação de genérico), FR-18 (novo), NFR-6 (duas condições), as duas linhas novas da §6 e o parágrafo novo de M-1. O resto do PRD não foi revisado.

**Veredito:** o delta é factualmente correto nas duas afirmações verificáveis, mas superestima a assimetria que M-1 alega, e FR-18 exige do relatório um comportamento que nenhum AD sustenta.

---

## 1. Verificação factual

Contado, não estimado, em `docs/reclamacoes_reclameaqui.csv` (50 linhas, separador `;`, `utf-8-sig`):

| Afirmação do delta | Verificação | Resultado |
|---|---|---|
| `Titulo` é "uma de dezoito strings canônicas" | 18 valores distintos em 50 linhas | **confirmado** |
| modelo recebe "apenas `id` e o texto livre" | `classificador.py:81` — `[{"id": r["ID_Reclamacao"], "texto": r["Descricao"]}]` | **confirmado** |
| genéricos `fatura`/`compra`/`produto`/`serviço` (FR-13, via §1 e CM-3) | `.cache_analises.json`: 7 + 4 + 4 + 3 = **18 de 50** | confirmado |
| sentimento constante (justificativa de FR-18) | 50/50 `negativo` | confirmado |

Nota lateral: `pedido`, listado em CM-3, **não ocorre nenhuma vez** na saída medida. Os 18 vêm inteiramente dos quatro termos que FR-13 enumera.

## 2. A assimetria de M-1 está superestimada

O parágrafo novo afirma que o modelo faz "trabalho diferente de casar uma string" porque não vê o título. O payload de fato não carrega título nem empresa — mas a `INSTRUCAO` de `classificador.py:50-64` enumera, em prosa, exatamente as categorias que `baseline.py:16-25` casa por string:

| `CATEGORIAS_DINHEIRO` (baseline) | Caso correspondente na `INSTRUCAO` |
|---|---|
| Demora no estorno do cancelamento | "estorno prometido e não feito" |
| Cobrança indevida no cartão de crédito | "cobrança de algo que o cliente não contratou" |
| Bloqueio de conta sem justificativa | "conta, saldo ou valor bloqueado" |
| Produto não entregue e passou do prazo | "produto pago e não entregue" |
| Produto veio com defeito e não trocam | "produto pago que chegou quebrado ou defeituoso e a empresa se recusa a trocar" |
| Não consigo cancelar assinatura | "assinatura que o cliente tenta cancelar e segue sendo cobrada" |

Seis de seis, um para um. O título não atravessa a fronteira do payload, mas o gabarito de categorias atravessa a fronteira do prompt. A paridade item a item deixa de ser surpreendente: os dois classificadores receberam a mesma lista, um como conjunto de strings e o outro como parágrafo. A conclusão do delta ("numa base sem títulos padronizados a regra determinística não existiria") continua válida; a premissa de que o modelo chegou lá "a partir de prosa de consumidor" não — ele chegou a partir de prosa de consumidor **mais** a enumeração das seis categorias.

Correção sugerida: nomear a segunda assimetria em vez de omiti-la — a regra recebe as categorias como chave de casamento, o modelo as recebe como definição a aplicar sobre texto livre. Isso é honesto e continua sustentando o argumento.

Imprecisão menor no mesmo parágrafo: "A regra determinística lê o `Titulo`" descreve `prioriza(..., filtrar_respondida=False)`. A regra que atende M-1 na tabela logo acima é `categoria + Status`, que lê `Titulo` **e** `Status` (`baseline.py:40-42`). O parágrafo descreve a regra reprovada.

## 3. Consistência com a spine

### AD-14 → FR-18: o PRD passou a exigir algo que o AD não sustenta

FR-18 pede a ressalva "do que os limita **na base analisada**". AD-14 resolve isso como "texto do template", e AD-22 proíbe o template de comparar com limiar. Um texto estático no template não sabe qual base foi analisada: rodado sobre uma base com variação de sentimento, ele afirmaria uma limitação que não existe — e um relatório que declara falsamente a própria leitura como não validada quebra a mesma confiança que FR-16 e FR-18 existem para proteger.

Escolha necessária, e nenhuma das duas está feita hoje:
- **ressalva estática** — então FR-18 deve dizer "nesta base", como AD-14 diz, e não "na base analisada";
- **ressalva condicional** — então é derivada de `Agregados` (contagem de sentimentos distintos, contagem de genéricos), decidida em `agregar` por AD-22, e AD-14 precisa ser reescrito, porque hoje ele fixa o conteúdo.

### AD-21 e AD-18 → FR-13: três listas de genéricos, uma fonte única prometida

AD-21 manda a lista de termos genéricos viver em `catalogo.py`; AD-18 é o AD que existe justamente para impedir que um catálogo divirja entre prompt, pontuação e teste. O delta cria a terceira cópia:

| Lugar | Lista |
|---|---|
| §1 | `fatura`, `compra`, `produto`, `serviço` |
| **FR-13 (delta)** | `fatura`, `compra`, `produto`, `serviço` — fechada, sem "e afins" |
| CM-3 | `fatura`, `compra`, `produto`, `serviço`, `pedido` **e afins** |

FR-13 e CM-3 já não coincidem. Como FR-13 é o requisito que o template realiza e CM-3 é a contramétrica que mede o mesmo conjunto, medir e marcar passam a usar listas diferentes. FR-13 deveria referenciar o catálogo ("os termos genéricos do catálogo, ver CM-3"), não enumerar.

### AD-13 → NFR-6 e §6: contraparte correta, unidade indefinida

As duas linhas novas da §6 batem com AD-13 (encerra sem escrever em zero análises; degradado em 100% de derrubada). O que falta é o **denominador**. AD-2 fixa a unidade contada: "a contagem que FR-2 e CM-2 reportam é de **códigos derrubados**, não de pares reprovados nem de reclamações afetadas; as três são defensáveis e só uma pode ser a métrica". NFR-6.2 e a linha da §6 dizem "100% dos sinais propostos" sem dizer sobre o quê — e o glossário da §3.0 define "sinal" como item marcado numa reclamação, que é um terceiro recorte. Adotar a palavra de AD-2 ("100% dos **códigos** de sinal propostos foram derrubados") resolve em uma edição.

**CM-2 × NFR-6.2: não há contradição.** CM-2 alerta na ponta zero (verificação possivelmente morta), NFR-6.2 degrada na ponta 100% (modelo fabricando tudo). São os dois extremos da mesma taxa, com o meio normal, e a leitura de 2026-08-06 (zero derrubadas em 50) cai no alerta de CM-2 sem acionar NFR-6.2. O que os dois compartilham é o defeito acima: nenhum declara o denominador.

### AD-16: sem contraparte normativa

AD-16 proíbe `empresa` e `titulo` no payload, por construção. No PRD isso aparece apenas como frase descritiva dentro de M-1 ("título e empresa nunca entram no payload"), que é uma métrica e não obriga nada. Se um dia alguém acrescentar o título ao prompt, nenhum FR ou NFR é violado — só uma nota de rodapé de métrica fica desatualizada. Falta um NFR de uma linha, ou FR-5 precisa carregar a restrição.

Nenhuma outra regra da spine tocada pelo delta ficou sem reflexo.

## 4. Prosa

- **NFR-6, frase de abertura:** "sob qualquer uma de duas condições" — falta o artigo (`de duas` → `das duas`) e `sob` rege mal aqui. Ler: "em qualquer uma das duas condições abaixo".
- **FR-18:** "a ressalva **do que** os limita" — regência torta; "a ressalva sobre o que os limita" ou "a ressalva daquilo que os limita".
- **FR-18, redundância interna:** diz "ao lado do próprio gráfico" na frase normativa e repete "é texto ao lado do gráfico, não nota de rodapé" no parêntese, a seis linhas de distância. Uma das duas basta — a do parêntese, que traz o contraste com a nota de rodapé.
- **NFR-6.2 → §6 → AD-13:** a mesma justificativa ("cinquenta análises, zero falhas, um modelo que fabricou tudo") aparece três vezes, duas delas dentro do PRD. A §6 é tabela de comportamento; ela deveria apontar para NFR-6 e parar. Hoje ela reexplica.
- **§6, linha nova:** "são 50 análises, zero falhas" fixa o tamanho desta base numa tabela cujas outras linhas são todas agnósticas ("Mais de 10% da base"). Trocar por "a contagem de reclamações fica cheia e as falhas em zero".
- **NFR-6.2:** "0% de degradação" mistura duas coisas — degradação é um estado binário no requisito, e 0% é a leitura da condição 1. Ler: "a condição 1 lê 0% de não analisadas".
- **FR-13 e FR-18** reenunciam os achados da §1 (os quatro termos genéricos; sentimento 50 de 50) em vez de referenciá-la. Aceitável em FR-18, que precisa do contexto no parêntese de justificativa; em FR-13 é a cópia de lista que a seção 3 acima já aponta como risco real, não só como repetição.
