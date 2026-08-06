# Sinais de risco jurídico

Companion de `SPEC.md`. Sustenta CAP-4, CAP-5 e CAP-6.

## Os dois sinais

Risco jurídico é composto por dois sinais **independentes**. Detectar apenas o primeiro produz um sistema que acerta o caso raro e perde o caso caro.

| Sinal | O que é | Corpus de 5 | Base do projeto (50) |
|---|---|---|---|
| **A — intenção declarada** | O cliente anuncia que vai acionar seus direitos. Ex.: *"se não for resolvido em X dias vou procurar meus direitos."* | 0 de 5 | **0 de 50** |
| **B — exposição factual** | Nenhuma ameaça, apenas fato: prazo vencido, cobrança sem contratação, registro contraditório. | 5 de 5 | abundante |

A varredura da base real por `processo`, `advogado`, `Procon`, `direitos`, `juizado`, `justiça`, `Código de Defesa do Consumidor`, `acionar` e `jurídico` não retornou **nenhuma** ocorrência em 50 reclamações. O que existe é indignação retórica — *"é uma fraude"*, *"é um absurdo"*, *"exijo meu dinheiro"* — exatamente o material que produz falso positivo num classificador ingênuo.

A descoberta da sessão de brainstorming se confirma em escala dez vezes maior: **um detector de ameaça explícita não encontraria nada nesta base.**

## Catálogo do sinal B

| Código | Descrição |
|---|---|
| `cobranca_indevida` | Valor debitado sem contratação, sem notificação prévia, ou contra o que foi prometido na oferta |
| `prazo_estourado` | Prazo legal ou prometido pela própria empresa já vencido |
| `registro_contraditorio` | Registro da empresa afirma um fato que o cliente contesta apresentando protocolo ou rastreio |
| `servico_nao_contratado` | Item na fatura que o cliente nega ter solicitado |
| `lei_citada` | Cliente invoca norma de defesa do consumidor, artigo específico, ou pede ressarcimento em dobro |

### Candidato: `Status` como sinal determinístico

A base traz uma coluna `Status` que o desenho original não previu:

| Valor | Ocorrências em 50 |
|---|---|
| Respondida | 12 |
| Em réplica | 12 |
| **Não respondida** | **11** |
| **Não resolvido** | **9** |
| Resolvido | 6 |

`Não respondida` e `Não resolvido` são exposição factual pura, já estruturada, **de graça e sem LLM** — a empresa nem respondeu, ou respondeu e não resolveu. Vinte das cinquenta linhas. É o sinal mais barato disponível no projeto inteiro.

Não foi adotado como parcela porque o peso frente às três existentes é decisão em aberto — ver Open Questions em `SPEC.md`.

### Glossário no prompt

Cada tipo precisa de **definição escrita com exemplo dentro do prompt**. Categoria sem glossário explícito degrada a classificação — é o fator de maior impacto na acurácia.

## Regra da evidência

Todo sinal marcado como presente exige ao menos uma citação: **trecho literal do texto da reclamação**.

Pós-validação determinística, fora do LLM: se a citação não for substring do texto original, o sinal cai para falso. O modelo não é confiável para auditar a si mesmo; comparação de string é.

Isso mata o falso positivo retórico. *"Isso é um absurdo, é um crime o que vocês fazem"* contém a palavra "crime" e nenhuma intenção jurídica — sem citação que sustente intenção, o sinal A não sobrevive.

## O score, calibrado contra o gabarito

Gabarito humano coletado sobre as 50 reclamações da base em 2026-08-06. Versão vigente: **v2, 19 marcadas (38%)**, em `docs/gabarito.csv`.

> **Revisão v1 → v2, registrada por honestidade.** A v1 tinha 18 marcações e está preservada em `docs/gabarito-v1.csv`. Uma marcação foi acrescentada: `RA645276696`, *"não consigo cancelar assinatura"*. O motivo é auditável — o classificador com LLM a marcou citando literalmente **"sigo sendo cobrado"**, e o critério humano (*a empresa está com dinheiro do cliente*) qualifica o caso. A revisão foi aceita com o argumento à vista, não para melhorar métrica. A mesma correção foi aplicada à regra determinística, para que a comparação não fosse enviesada a favor do LLM.

## O resultado que encerra a etapa de medição

| Regra | TP | FP | FN | Precisão | Recall | F1 |
|---|---|---|---|---|---|---|
| Categoria (determinística, vê o título) | 16 | 2 | 3 | 89% | 84% | **0.86** |
| Gemini 3.6 Flash (vê apenas o texto livre) | 16 | 2 | 3 | 89% | 84% | **0.86** |
| Qualquer uma + filtro de `Status` | 13 | 0 | 6 | 100% | 68% | 0.81 |

Verificação item a item: **zero divergências nas 50 reclamações.** Não é empate estatístico — as duas abordagens tomam a mesma decisão em cada linha.

Duas leituras, ambas verdadeiras:

- **O LLM se validou.** Reconstruiu a categorização inteira lendo apenas o texto livre, sem nunca ver o título canônico que a regra determinística consome de graça. Numa base sem títulos padronizados, a regra não existiria e ele seria a única opção.
- **O LLM não se paga aqui.** Reproduzir exatamente um `set` de seis strings é custo sem retorno. Nesta base, o pipeline de agentes é infraestrutura cara para um resultado que um `in` entrega.

### O que o gabarito revelou

Uma única dimensão explica quase tudo: **a empresa está com dinheiro do cliente**. Seis categorias concentram 16 das 19 marcações.

| Categoria | Marcadas |
|---|---|
| Demora no estorno do cancelamento | 4 / 4 |
| Bloqueio de conta sem justificativa | 4 / 4 |
| Produto não entregue e passou do prazo | 1 / 1 |
| Produto veio com defeito e não trocam | 1 / 1 |
| Não consigo cancelar assinatura | 1 / 1 |
| Cobrança indevida no cartão de crédito | 5 / 7 |

Nove categorias inteiras receberam **zero** marcações: internet instável, voo cancelado, entregador que arremessou o pacote, mau atendimento, roupa no tamanho errado, propaganda enganosa, estofado rasgado, ração estragada, brinde não enviado. Todas são serviço ruim ou dano — nenhuma tem dinheiro preso.

A primeira parcela do desenho original se confirma em escala dez vezes maior. As outras não.

### Desempenho das regras candidatas

Todos os números abaixo são contra o gabarito v2, recalculados em 2026-08-06. A versão anterior desta tabela carregava números do v1 e contradizia a tabela duas seções acima.

| Regra | Precisão | Recall | F1 |
|---|---|---|---|
| Categoria de dinheiro retido | 88,9% | 84,2% | **0.865** |
| Categoria + `Status` ≠ Respondida | **100%** | 68,4% | 0.813 |
| Apenas `Status` ∈ {Não respondida, Não resolvido} | 40,0% | 42,1% | 0.410 |

**A regra adotada é a segunda.** O PRD trocou o critério de aceitação de F1 por precisão ≥ 95% com piso de recall em 65%, porque F1 é simétrico e o custo declarado não é — media 0.813 para a regra que não erra e 0.865 para a que erra duas vezes. Ver M-1 no PRD.

`Status` sozinho é pior que a categoria — **não vira parcela independente**. Mas dentro da categoria certa ele funciona como filtro de saída: os dois únicos falsos positivos da primeira regra são as duas cobranças indevidas com `Status` = Respondida.

### Pesos do v1

| Parcela | Peso | Situação |
|---|---|---|
| Dinheiro do cliente retido | 3 | **Validada.** Único sinal que explica o gabarito |
| `Status` = Respondida | −1 | Modificador negativo, elimina os falsos positivos observados |
| Ameaça explícita (sinal A) | 3 | **Não exercida** — 0 de 50 nesta base |
| Dano continuado | 2 | **Não sustentada** — *mensalidade aumentou sem aviso* teve apenas 1 de 3 |
| Registro contraditório | 2 | **Não exercida** — nenhum caso limpo nesta base |
| Prazo estourado | 1 | **Fraca** — a base não traz data de evento |

Corte binário, a partir de 3 pontos. As parcelas não exercidas permanecem no código com peso baixo: elas existem para a base real, não para esta.

> **Honestidade sobre o resultado.** Nesta base, um classificador de uma parcela só atinge F1 0.86. As outras quatro parcelas não são testáveis com os dados disponíveis, e mantê-las é uma aposta na variedade de uma base real — não uma conclusão apoiada em evidência.

### Ruído do gabarito

Depende de quão fundo se olha. Medido em 2026-08-06:

| Agrupamento | Linhas contraditórias |
|---|---|
| Texto exato + mesmo `Status` | 2 (4%) |
| Mesmo template + mesmo `Status` | 4 (**8%**) |
| Mesmo template, `Status` ignorado | 15 (30%) |

Os 30% são miragem: o maior grupo são sete cobranças indevidas em que as duas marcadas `não` são exatamente as duas com `Status` = Respondida. Ali o humano aplicava uma regra consistente — a mesma que virou o modificador negativo do score —, não se contradizia. **O número honesto é 8%**, que é o que sobra quando o `Status` é controlado.

Consequência direta: **exigir 100% de concordância com o gabarito é impossível**, porque o gabarito não concorda com si mesmo em 100%. O critério de aceitação é precisão ≥ 95% com piso de recall em 65%.

## Gabarito de aceitação

Sobre o corpus de referência de cinco reclamações, o julgamento humano colocou na fila:

| # | Empresa | Por quê |
|---|---|---|
| 2 | FastDelivery | Registro de entrega concluída sem entrega, contestado com rastreio |
| 3 | Banco Digital Prime | Tarifa contra oferta de isenção, sem notificação, com a lei citada pelo cliente |
| 4 | Conecta Móvel | Serviços nunca contratados na fatura, sob ameaça de bloqueio da linha |

Ficaram de fora: 1 (TechVibe, produto defeituoso com prazo de troca vencido) e 5 (Moda Certa, reembolso atrasado). Ambas têm prazo estourado — mas a empresa **deve** algo, não **tirou** algo.
