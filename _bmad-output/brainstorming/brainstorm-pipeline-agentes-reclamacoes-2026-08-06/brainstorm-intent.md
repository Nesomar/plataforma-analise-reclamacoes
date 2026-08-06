# Intent — Plataforma de Análise de Reclamações

**Origem:** sessão de brainstorming de 2026-08-06 (modo Parceiro Criativo).
**Natureza do projeto:** estudo. O aprendizado de arquitetura multi-agente é o entregável, não um meio.

---

## O sistema em uma frase

Um batch em Python que lê um CSV de reclamações, roda uma análise orquestrada por LangGraph sobre a API do Google AI Studio (Gemini), e gera um HTML com sentimento do cliente, produtos mais reclamados e uma fila de prioridade por risco jurídico.

## Quem consome

Gestores. O relatório é **apenas representação visual** dos resultados — decisão explícita de escopo, não omissão. Não é ferramenta de decisão elaborada, não tem drill-down, não tem série temporal.

---

## Descobertas que mudam o desenho

### 1. Risco jurídico são dois sinais independentes, não um

| Sinal | O que é | Frequência observada |
|---|---|---|
| **A — intenção declarada** | Ameaça explícita: *"vou procurar meus direitos"* | 0 de 5 no corpus real |
| **B — exposição factual** | Prazo estourado, cobrança indevida, registro falso | 5 de 5 no corpus real |

Um classificador treinado só no sinal A acerta o caso raro e perde o caro. O corpus de 5 reclamações realistas escritas durante a sessão não continha **nenhuma** ameaça explícita — e mesmo assim tinha risco espalhado por todas.

### 2. Citação obrigatória como defesa contra falso positivo

Requisito declarado na abertura: falso positivo dói mais que falso negativo (entope a fila de prioridade e o gestor perde a confiança no relatório).

Mecanismo escolhido: **toda classificação de risco precisa devolver a frase literal do texto que a sustenta.** Sem citação, a classificação cai. Isso mata o caso clássico do falso positivo retórico — *"isso é um absurdo, é um crime o que vocês fazem"* tem a palavra "crime" e nenhuma intenção jurídica.

### 3. O score de priorização é determinístico

Três parcelas, extraídas do veredito humano sobre o corpus (não inventadas antes):

1. **A empresa está com dinheiro do cliente** — cobrança indevida pesa mais que dívida pendente.
2. **O prejuízo cresce sozinho** — tarifa e assinatura recorrentes se multiplicam em silêncio; um produto defeituoso fica parado.
3. **O registro da empresa contradiz o fato** — sistema diz "entregue", cliente tem rastreio e diz que não recebeu.

Nenhuma precisa de LLM para ser **julgada**. Só para ser **extraída**. Aritmética de prazo é `datetime`, não Gemini.

### 4. Problema em aberto: a fila inflacionada

No corpus de teste, 3 de 5 reclamações entraram na fila de prioridade. Uma fila onde a maioria é prioridade não é uma fila.

Direção candidata (aceita para v2, não resolvida): trocar o binário por **níveis com prazo**, no modelo da triagem de pronto-socorro — cada nível é um tempo máximo de atendimento, não uma posição, e a reclamação envelhece de nível sozinha.

---

## Escopo decidido (MoSCoW)

### MUST — v1
- CLI batch: CSV → grafo LangGraph → HTML único
- Nós do grafo divididos **por etapa do fluxo**
- **Contrato de state com `id` estável por reclamação + campo de evidência** — único item não-aditivo de toda a lista
- Extração via LLM: sentimento, produto, sinais A e B, **com citação obrigatória**
- Lote de N reclamações por chamada
- Determinístico: parse do CSV, agregação, ranking, aritmética de prazo, cálculo do score
- HTML com os gráficos

### SHOULD — v2
- Cascata Flash → Pro: Flash tria o lote, roteador monta sublote só de suspeitos, Pro confirma
- Cache com chave `hash(texto + versão_do_prompt + modelo)`
- Níveis de criticidade em vez de binário prioritário/não

### COULD — v3+
- Guard-rails na entrada e na saída
- Loop de crítica com `max_iteracoes` e rota de escape definida
- Checkpoint do LangGraph como estado persistido
- Front com upload de CSV, job assíncrono e polling de status
- Reclassificação automática por tempo de espera

### WON'T — desta vez
- Relatório como ferramenta de decisão elaborada
- Divisão de agentes por dimensão de análise ou por especialidade de domínio
- Base inteira num prompt só
- Normalização do CSV com LLM

---

## Restrições fixadas

- **Lote se desfaz na escalada.** Flash recebe lote de N e devolve N com flag; o roteador filtra e monta um lote menor de suspeitos para o Pro. Nunca chamada individual.
- **Upload síncrono não sobrevive** (quando o front entrar): pipeline de LLM sobre lote demora minutos, request HTTP estoura antes. Exige job assíncrono. O checkpoint do LangGraph vira o estado do job.
- **Cache exige três campos na chave.** Reclamação é imutável; prompt não é. Chave só com o texto envenena o cache ao primeiro ajuste de prompt.

---

## Ressalva

Os padrões de risco jurídico aqui são heurísticas de engenharia, não parecer jurídico. Adequado para projeto de estudo; produção exigiria validação por profissional habilitado.

---

*Pronto para entrar em `bmad-spec`, `bmad-prd` ou `bmad-product-brief` como input.*
