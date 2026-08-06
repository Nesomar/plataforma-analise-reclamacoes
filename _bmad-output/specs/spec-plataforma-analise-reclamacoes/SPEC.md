---
id: SPEC-plataforma-analise-reclamacoes
companions:
  - risk-signals.md
  - state-contract.md
  - architecture-diagrams.md
  - roadmap.md
sources:
  - ../../brainstorming/brainstorm-pipeline-agentes-reclamacoes-2026-08-06/brainstorm-intent.md
  - ../../brainstorming/brainstorm-pipeline-agentes-reclamacoes-2026-08-06/spec-tecnico-v1.md
  - ../../brainstorming/brainstorm-pipeline-agentes-reclamacoes-2026-08-06/tasks-v1.md
---

> **Contrato canônico.** Este SPEC e os arquivos em `companions:` são o contrato completo do que construir, testar e validar. Os documentos em `sources:` servem só para rastreabilidade.

# Plataforma de Análise de Reclamações

## Why

**Visão a realizar, com aprendizado como motor.** Um profissional quer dominar arquitetura de pipeline multi-agente (LangGraph sobre Gemini) construindo algo que resolve um problema real em vez de um exemplo de tutorial. O problema escolhido: uma base bruta de reclamações de consumidor é ilegível em escala — ninguém lê 500 textos livres para descobrir qual cliente está prestes a acionar a empresa, qual produto concentra a queixa, e como a marca é percebida.

O sistema transforma essa base em três leituras acionáveis para gestores: uma fila de prioridade fundamentada em exposição real, um ranking de produtos, e a percepção do cliente sobre a marca. O aprendizado é o motivo; a utilidade é o critério de que o aprendizado foi real.

## Capabilities

- **CAP-1 — Ingestão**
  - **intent:** O sistema carrega um CSV de reclamações com schema fixo, adota o identificador que o arquivo já traz e garante que ele é único antes de prosseguir.
  - **success:** Identificador duplicado ou coluna ausente interrompem a execução antes de qualquer chamada paga; duas execuções sobre o mesmo arquivo produzem o mesmo conjunto de identificadores. Ver `state-contract.md`.

- **CAP-2 — Sentimento**
  - **intent:** O sistema determina, a partir do texto livre, o sentimento do cliente naquela reclamação.
  - **success:** Cada reclamação recebe exatamente um valor entre positivo, neutro e negativo; a distribuição agregada é a leitura de percepção de marca apresentada ao gestor.

- **CAP-3 — Produto**
  - **intent:** O sistema identifica qual produto ou serviço a reclamação menciona, mesmo quando citado informalmente no meio do texto.
  - **success:** Produto identificado alimenta o ranking; reclamação sem produto identificável recebe tratamento definido e não é silenciosamente descartada.

- **CAP-4 — Sinais de risco jurídico**
  - **intent:** O sistema detecta dois tipos independentes de sinal — intenção declarada de acionar a empresa, e exposição factual sem ameaça — e devolve, para cada sinal, a frase literal do texto que o sustenta.
  - **success:** Nenhum sinal é marcado sem citação associada; os cinco tipos de exposição factual do catálogo são reconhecidos sobre o corpus de referência. Ver `risk-signals.md`.

- **CAP-5 — Verificação de evidência**
  - **intent:** O sistema confirma, sem consultar o modelo, que cada citação devolvida existe de fato no texto original da reclamação, e derruba a classificação quando não existe.
  - **success:** 100% das citações presentes na saída final são substring exata do texto original; citação fabricada anula o sinal correspondente.

- **CAP-6 — Priorização**
  - **intent:** O sistema pontua cada reclamação por exposição e produz uma fila ordenada que diz ao gestor o que atender primeiro.
  - **success:** A fila produzida atinge **precisão ≥ 95% com recall ≥ 65%** contra `docs/gabarito.csv`, com o motivo de cada item visível. A métrica é assimétrica porque o custo é: F1 pesaria precisão e recall igualmente, contra a restrição declarada de que falso positivo custa mais. O teto não é 100%: o próprio gabarito humano se contradiz em 8% das linhas de mesmo template e mesmo `Status`.

- **CAP-7 — Agregação**
  - **intent:** O sistema consolida a base em ranking de produtos por volume, distribuição de sentimento e temas recorrentes.
  - **success:** Os números agregados batem com a contagem direta sobre a saída por reclamação; o ranking sinaliza ao leitor que volume não equivale a gravidade.

- **CAP-8 — Relatório**
  - **intent:** O sistema entrega o resultado como um relatório visual que o gestor abre sem instalar nada.
  - **success:** Arquivo único abre em navegador sem servidor e sem rede; cada item da fila de prioridade exibe a citação que sustentou sua classificação.

- **CAP-9 — Orquestração**
  - **intent:** Todo o fluxo é executado como um grafo cujo estado compartilhado é explícito e versionável, permitindo que etapas sejam adicionadas sem reescrever as existentes.
  - **success:** O contrato de estado em `state-contract.md` é respeitado por todas as etapas; adicionar uma etapa nova não exige alterar a assinatura das anteriores.

## Constraints

- **O modelo extrai; código determinístico julga.** Score, contagem, ranking, ordenação e aritmética de prazo nunca passam pelo LLM.
- **Produto é inferido do texto, nunca da empresa.** Na base do projeto empresa e reclamação estão pareadas ao acaso — supermercado com reclamação de voo cancelado, loja de moda com reclamação de ração. Derivar produto do nome da empresa produz ranking falso.
- **Sem citação literal não há classificação de risco.** É a defesa primária contra falso positivo.
- **Falso positivo custa mais que falso negativo.** Fila inflada destrói a confiança do gestor no relatório inteiro; risco perdido custa menos que relatório abandonado.
- **Processamento em lote, com desmonte na escalada.** O lote é a unidade de chamada; quando parte dele precisa de análise mais cara, um sublote é remontado apenas com os candidatos. Chamada individual por reclamação é proibida.
- **Casamento de resposta sempre por identificador, nunca por posição.** Resposta incompleta do modelo deve ser detectável, não silenciosa.
- **A saída é um arquivo único autocontido.** Sem servidor, sem CDN, sem dependência de rede na hora de abrir.
- **LangGraph é obrigatório, mesmo com fluxo linear.** É o objeto de estudo, não o meio — otimizar removendo-o anula o propósito.
- **Provedor de LLM: Google AI Studio (Gemini). Linguagem: Python.**
- **O relatório é apenas representação visual.** Sem drill-down, sem série temporal, sem ferramenta de decisão elaborada.
- **As heurísticas de risco jurídico são engenharia, não parecer jurídico.** Adequadas a estudo; produção exigiria validação profissional.

## Non-goals

- Interface web, upload de arquivo, job assíncrono e polling de status.
- Cache de chamadas, cascata entre modelos de custo diferente, guard-rails de entrada e saída, loop de crítica, checkpoint persistido — todos deferidos, ver `roadmap.md`.
- Níveis de criticidade na fila: o v1 é binário, sabidamente inflado.
- Normalizar ou limpar o CSV usando LLM.
- Agentes divididos por dimensão de análise ou por especialidade de domínio — a divisão é por etapa do fluxo.
- Enviar a base inteira num único prompt.
- Aceitar formatos de entrada além do schema fixo definido.
- Relatório como ferramenta de decisão elaborada.

## Success signal

Executar o pipeline sobre o corpus de referência produz um relatório HTML em que a fila de prioridade contém exatamente as reclamações que o julgamento humano marcou, cada uma mostrando a frase que a colocou ali — e um leitor que nunca viu a base consegue dizer, olhando o relatório, qual produto está pior e como o cliente se sente com a marca.

## Assumptions

- O relatório consolida a base inteira, sem filtro por empresa. A base contém 14 empresas distintas e nada define se a análise é por empresa ou agregada.
- Tamanho de lote é ponto de partida arbitrário, a calibrar por limite de contexto e taxa de resposta incompleta.
- A acurácia medida sobre a base do projeto superestima o desempenho em base real: 30 descrições distintas em 50 linhas, algumas repetidas quatro vezes na íntegra. Variedade linguística real é maior.

## Open Questions

- **Origem da base real.** A base do projeto é sintética. Nada define de onde viria uma base real nem em que formato ela chegaria. Adiada no PRD (Q-5): não bloqueia o v1, porque schema divergente falha de forma segura antes de qualquer chamada paga.

## Resolved

- **Dados pessoais** — resolvida em 2026-08-06 pela validação de `docs/reclamacoes_reclameaqui.csv`: base sintética, empresas fictícias, sem nome de pessoa, sem CPF, sem endereço, protocolos aleatórios. Segura para repositório público. A regra permanece válida para qualquer base real futura.
- **Schema do CSV** — resolvido pela mesma validação; formato real documentado em `state-contract.md`.
- **Corte da fila** — resolvido pelo gabarito: o julgamento humano marcou 38% da base, abaixo do limiar de 40% que tornaria a fila inútil. **Binário fica no v1.** Níveis com prazo permanecem em `roadmap.md` sem urgência.
- **`Status` como parcela** — resolvido pela medição: sozinho tem F1 0.42, pior que a categoria. Não vira parcela independente; entra como modificador negativo. Ver `risk-signals.md`.
- **Prazo estourado sem data de evento** — resolvido: parcela mantida com peso 1, reconhecidamente fraca nesta base.
- **Gabarito de aceitação** — resolvido: `docs/gabarito.csv` v2, 19 de 50 na fila, coletado por marcação manual cega. A v1 com 18 marcações está preservada em `docs/gabarito-v1.csv`; a revisão está justificada em `risk-signals.md`.
- **Produto não identificável** — resolvido no PRD (Q-2): entra no ranking como linha visível `não identificado`, com seu total. Omitir do ranking mas contar no total quebraria o critério de sucesso de CAP-7.
- **Validade das parcelas não exercidas** — resolvido no PRD (Q-4): as três permanecem no código e cada uma ganha um caso de teste construído à mão que a exercita. O teste prova que o caminho executa, não que a heurística acerta — e o PRD declara isso.
- **Critério de aceitação da fila** — resolvido: F1 substituído por precisão ≥ 95% com piso de recall em 65%. F1 é simétrico e o custo declarado não é. Ver M-1 no PRD e a tabela de regras candidatas em `risk-signals.md`.
