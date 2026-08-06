# Roadmap

Companion de `SPEC.md`. Detalha o que os Non-goals deferem e em que ordem.

Tudo aqui é **aditivo** — pluga sobre o v1 sem reescrever, desde que o contrato em `state-contract.md` esteja correto desde o início.

## v2

**Níveis de criticidade em vez de fila binária.** O corte binário do v1 infla a fila. O modelo de referência é a triagem de pronto-socorro: níveis com **tempo máximo de atendimento** em vez de posição na fila, classificação por sinal medido e não por queixa declarada, e reclassificação automática conforme a espera avança. Decidir isso **antes** de calibrar o corte binário — calibrar o corte errado é trabalho jogado fora.

**Cascata entre modelos.** Modelo barato tria o lote e marca suspeitos; roteador condicional remonta um sublote apenas com eles; modelo caro confirma. Ataque direto ao falso positivo: um sinal só sobrevive se dois modelos concordarem. Ver o segundo diagrama em `architecture-diagrams.md`.

**Cache de chamadas.** Chave = `hash(texto + versão_do_prompt + modelo)`. Três campos, não um: a reclamação é imutável, o prompt não. Chave apenas com o texto envenena o cache no primeiro ajuste de prompt e produz depuração perdida.

## v3 e além

**Guard-rails de entrada e saída.** Validação antes e depois da etapa de LLM.

**Loop de crítica.** Um avaliador confere a saída da análise. Exige `max_iteracoes` e rota de escape definida desde o desenho: guard-rail de saída reprovando dentro de um loop sem freio é loop infinito. Definir o que acontece com a reclamação que falha três vezes — descarte, marcação como indeterminada, ou fila humana.

**Checkpoint persistido.** O checkpoint do orquestrador vira o estado do job.

**Interface web.** Upload de CSV, processamento, gráficos. Exige job assíncrono: o pipeline sobre um lote demora minutos e um request HTTP estoura antes. O desenho é `upload → cria job → devolve id → cliente faz polling → resultado`. O checkpoint acima é o que torna isso possível.

**Reclassificação por tempo de espera.** Reclamação que envelhece na fila sobe de nível sozinha. Depende dos níveis do v2.

## Fora de todas as versões

Relatório como ferramenta de decisão elaborada. Normalização de CSV por LLM. Agentes divididos por dimensão de análise ou especialidade de domínio. Base inteira num único prompt.
