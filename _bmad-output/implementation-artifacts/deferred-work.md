# Trabalho deferido

## Deferred from: code review of 1-1-contrato-de-estado-e-catalogo-de-sinais (2026-08-07)

- **Invariantes do contrato sem verificação executável** — `Motivo.citacao` não-nula sse `origem == "sinal"` existe só como comentário; `total_na_fila` é `len(fila)` e `nao_analisadas` é uma soma sobre `falhas`, guardados como campos independentes sem asserção que os amarre à fonte. Duas fontes para o mesmo número num relatório cujo valor inteiro é "quatro números honestos". Endereçar nas Stories 2.1/2.2, junto do código que preenche esses campos. (`plataforma/estado.py:52,78,81-82`)
- **Redutor `add` sem deduplicação por `id`** — `add` só concatena. Um lote reexecutado por retry do LangGraph, ou um `Send` reemitido, anexa a mesma `Analise` de novo; a asserção de conservação (AD-6) passa a falhar por excesso, indistinguível do caso que ela existe para detectar. Nada impede que um `id` esteja em `analises` e em `Falha.ids` ao mesmo tempo. Endereçar na Story 1.6, onde o fan-out nasce. (`plataforma/estado.py:93-94`)
- **`Literal` sem validação em runtime** — `Reclamacao.status` (5 valores) e `Analise.sentimento` (3 valores) não são checados em execução: o projeto proíbe `mypy` e não há CI. Os cinco status cobrem as 50 linhas do CSV atual, mas um sexto valor numa base real entra no estado sem ruído e reaparece como `KeyError` ou categoria silenciosamente ignorada no modificador de `Status`. Endereçar na Story 1.3, na fronteira de leitura. (`plataforma/estado.py:19-20,36`)
- **`Reclamacao.data` sem valor legal para data ausente ou inválida** — `data: str` é obrigatório e não admite `None`, enquanto `data_evento` admite. Uma linha com `Data` vazia ou fora de `DD/MM/AAAA` obriga a ingestão a inventar string, descartar a linha ou violar o contrato; as três saídas divergem e nenhuma está decidida. Endereçar na Story 1.3. (`plataforma/estado.py:15`)
- **Divisão 0/0 em `ocupacao_fila` e `taxa_produto_nao_nomeado`** — ambos são `float` puro, sem `| None`. Com `analisadas == 0` não existe valor legal para o numerador indefinido, e `Agregados` continua sendo o tipo que `agregar` monta antes de saber que AD-13 vai encerrar. Endereçar na Story 2.2. (`plataforma/estado.py:83-84`)
- **`caminho_html` não representa "relatório não gerado" e `Estado` é `total=True`** — se o pipeline degrada antes de escrever o HTML, o único valor legal é string vazia, indistinguível de bug de caminho. E o estado inicial exigiria um `Agregados` completo (14 chaves) antes de qualquer nó rodar. Ambos vieram da seção *Contrato de estado — forma exata*, que a story manda implementar literalmente. Reavaliar quando `grafo.py` nascer. (`plataforma/estado.py:91-97`)
- **AC6 "nenhuma chamada de rede" sem guard de socket** — verificado só indiretamente, pela ausência de `google*` em `sys.modules`. Qualquer import que abra socket sem passar pelo SDK escapa. Hoje os dois módulos são stdlib puro e o risco real é zero; o guard ganha valor quando `analise.py` nascer. Endereçar na Story 1.5. (`tests/test_import_sem_credencial.py`)
- **`state-contract.md` contradiz AC2 sobre o campo `evidencia`** — a § *Regras*, linha 82, ainda afirma "`evidencia` é campo de primeira classe, não metadado. Ele atravessa o estado até o relatório". O bloco de código do mesmo documento já não tem o campo e a nota de revisão explica a remoção: a prosa é resíduo da versão anterior. O código seguiu AC2 corretamente. Corrigir no documento, não no código. (`_bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md:82`)

## Deferred from: code review of 1-2-configuracao-validada-antes-de-qualquer-chamada-paga (2026-08-07)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-configuracao-validada-antes-de-qualquer-chamada-paga.md`
  summary: O `README.md` deixou de mencionar `GEMINI_API_KEY`, mas `classificador.py:125` ainda faz a ponte para `GOOGLE_API_KEY` — caminho de credencial vivo no código e invisível na documentação.
  evidence: A ponte é código morto: `google-genai 2.17.0` já lê as duas variáveis com precedência e fallback em `_api_client.py:101-117`. Nada quebra hoje, e a Story 3.1 depende de `classificador.py` intacto — por isso não foi tocado aqui. Remover a linha quando a Story 3.1 liberar o arquivo.

## Deferred from: code review of 1-3-ingestao-que-rejeita-base-invalida-antes-de-gastar (2026-08-08)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-ingestao-que-rejeita-base-invalida-antes-de-gastar.md`
  summary: `Reclamacao.status` continua sem validação contra o `Literal` de cinco valores — a dívida registrada na revisão da Story 1.1 apontava para "Story 1.3, na fronteira de leitura", mas as ACs reais de `epics.md` para esta story não pedem essa validação, e o spec desta story a listou explicitamente como fora de escopo.
  evidence: Um `Status` fora dos cinco valores (erro de digitação na origem, ou base real com rótulo novo) entra no estado sem erro nenhum e só se manifesta silenciosamente onde `Status == "Respondida"` é lido como modificador de pontuação (Story 2.1). Redirecionar para lá, que é o primeiro nó que de fato lê `Status`.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-ingestao-que-rejeita-base-invalida-antes-de-gastar.md`
  summary: A detecção de `ID_Reclamacao` duplicado compara strings cruas, sem `strip()`; dois ids que diferem só por espaço em volta (`"RA1"` vs `"RA1 "`) passam como distintos, e um id vazio (não duplicado) não é rejeitado.
  evidence: `state-contract.md` garante unicidade só na origem, não formatação. Nenhuma AC desta story cobre esse caso e a base de referência não o exercita — risco real, mas baixo, contra uma base sintética controlada. Vale reavaliar se uma base real (Q-5 do SPEC, ainda em aberto) chegar com essa forma de ruído.

## Deferred from: code review of 1-4-verificacao-de-evidencia-deterministica (2026-08-08)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-verificacao-de-evidencia-deterministica.md`
  summary: `verificar()` não valida a forma de `sinais` — um `Sinal` malformado (chave `citacao`/`codigo` ausente, ou `citacao` não-string vinda de uma extração de modelo mal comportada) levanta `KeyError`/`TypeError` cru de dentro de uma compreensão de lista, derrubando o lote inteiro em vez de reportar qual sinal falhou.
  evidence: Achado convergente de dois revisores independentes (adversarial e edge-case). Hoje `Sinal` só nasce à mão em teste, então o risco é zero — mas a Story 1.5 (`analise.py`) vai construir `Sinal` a partir de `response_schema` do `google-genai`, e a garantia real contra forma malformada é essa validação de schema, não uma guarda em `evidencia.py`. Revisitar se a Story 1.5 mostrar que o schema não fecha essa lacuna.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-verificacao-de-evidencia-deterministica.md`
  summary: O piso de "cinco palavras" é `len(citacao.split()) >= 5`, que conta fragmentos como `"R$"` e `"890"` como palavra inteira — uma citação pode cruzar o piso com números/moeda em vez de cinco palavras de contexto real.
  evidence: Nenhuma AC ou documento define "palavra" com mais precisão que a contagem por espaço em branco, e o risco é de baixa probabilidade (exige citação curta padded com fragmentos numéricos). Vale reavaliar se M-1/M-2 (Épico 3) revelarem citações que passam no piso sem sustentar o sinal de fato.

## Deferred from: code review of 2-2-agregacao-que-fecha-com-a-contagem-direta (2026-08-09)

- source_spec: `_bmad-output/implementation-artifacts/2-2-agregacao-que-fecha-com-a-contagem-direta.md`
  summary: `_fila_ordenada` levanta `KeyError` cru se `Pontuacao.id` não existir em `reclamacoes_por_id`.
  evidence: Mesmo padrão de risco já presente em `plataforma/pontuacao.py` desde a Story 2.1 (`reclamacoes_por_id[analise["id"]]`), não introduzido por esta story. `main.py` embrulha `invoke()` inteiro num `except Exception` genérico, então uma violação de invariante apareceria ao operador como `"encerrado: 'R99'"` — indistinguível de erro comum de entrada. Reavaliar junto de um tratamento de erro mais específico em `main.py`, se um dia for pedido.
- source_spec: `_bmad-output/implementation-artifacts/2-2-agregacao-que-fecha-com-a-contagem-direta.md`
  summary: Nenhum teste trava `agregacao._contar_codigos` em sincronia com `main._contar_codigos_derrubados` — as duas funções replicam a mesma semântica de contagem por decisão consciente (ver Dev Notes da Story 2.2), sem import cruzado.
  evidence: Um teste de sincronia exigiria acoplar os dois módulos ou duplicar a fixture entre `tests/test_agregacao.py` e `tests/test_main.py`, o que a própria story rejeitou para não inverter a dependência entrypoint↔filtro. Reavaliar quando `main.py` for religado para ler `agregados` em vez de recalcular (candidato: perto da Story 2.6).

## Deferred from: code review of 2-3-relatorio-com-a-fila-no-topo-e-a-evidencia-a-vista (2026-08-09)

- source_spec: `_bmad-output/implementation-artifacts/2-3-relatorio-com-a-fila-no-topo-e-a-evidencia-a-vista.md`
  summary: `_itens_fila` faz `pontuacoes_por_id[id_]`/`reclamacoes_por_id[id_]` sem guarda contra um id de `agregados["fila"]` ausente ou duplicado nos mapas.
  evidence: Mesmo padrão de risco já aceito em `agregacao._fila_ordenada` desde a Story 2.2 (que por sua vez replica o padrão de `pontuacao.py` desde a Story 2.1) — sustentado pela conservação AD-6 (`lidas == analisadas + afetadas`) e por `pontuar` produzir exatamente uma `Pontuacao` por `Analise` (AD-19). Reavaliar junto do mesmo tratamento de erro mais específico em `main.py` cogitado na Story 2.2, se um dia for pedido.

## Deferred from: code review of 2-6-o-arquivo-entregue-nasce-seguro-e-autocontido (2026-08-09)

- source_spec: `_bmad-output/implementation-artifacts/2-6-o-arquivo-entregue-nasce-seguro-e-autocontido.md`
  summary: Corrida TOCTOU entre o cheque de existência do arquivo de saída (antes de `.invoke()`, que pode levar minutos com chamadas pagas) e a escrita de fato dentro do nó `renderizar` — duas execuções concorrentes, ou um arquivo criado durante a execução, passariam pelo cheque sem erro.
  evidence: Ferramenta de linha de comando de operador único, sem requisito de concorrência ou agendamento em nenhuma AC/NFR do projeto. Reavaliar se execução concorrente ou agendada (cron, pipeline CI) virar requisito real.
- source_spec: `_bmad-output/implementation-artifacts/2-6-o-arquivo-entregue-nasce-seguro-e-autocontido.md`
  summary: O cheque prévio de sobrescrita só verifica existência do arquivo, não gravabilidade — diretório sem permissão de escrita ou arquivo travado por outro processo só falha dentro de `renderizar`, depois das chamadas pagas já terem acontecido.
  evidence: Cobrir esse caso plenamente exigiria sondar gravabilidade sem efeito colateral (ex.: abrir e fechar o arquivo, checar permissão do diretório), complexidade não pedida por nenhuma AC. Baixa probabilidade prática — o diretório já é o mesmo onde o CSV de entrada vive e foi lido com sucesso.

## Deferred from: code review of 2-4-graficos-embutidos-com-a-ressalva-ao-lado (2026-08-09)

- source_spec: `_bmad-output/implementation-artifacts/2-4-graficos-embutidos-com-a-ressalva-ao-lado.md`
  summary: `_barras_ranking` confia que `ranking_produtos` já chega ordenado por `total` decrescente, sem reverificar — a barra mais larga (100%) só está correta se essa ordem for honrada.
  evidence: Mesma classe de confiança em invariante upstream já aceita para `_itens_fila` (Story 2.3) e `_fila_ordenada` (Story 2.2), sustentada por `agregacao._ranking_produtos` ordenar antes de devolver (AD-19/AD-22). Reavaliar se `agregacao.py` algum dia parar de garantir essa ordem.
- source_spec: `_bmad-output/implementation-artifacts/2-4-graficos-embutidos-com-a-ressalva-ao-lado.md`
  summary: A ressalva do ranking cita "produto"/"fatura" como exemplos de termo genérico, texto livre duplicando `catalogo.TERMOS_GENERICOS` sem vínculo executável.
  evidence: Se a lista canônica de `catalogo.py` ganhar ou perder termos, a ressalva do template não acompanha automaticamente. Baixo risco — a lista muda por medição (ver `catalogo.py`), não por acaso. Reavaliar se `TERMOS_GENERICOS` for revisada.
- source_spec: `_bmad-output/implementation-artifacts/2-4-graficos-embutidos-com-a-ressalva-ao-lado.md`
  summary: `rotulo` do produto (texto livre do modelo) é renderizado em `<text>` de SVG sem tratamento de overflow ou quebra de linha para rótulos muito longos.
  evidence: A base sintética atual não expõe nomes de produto longos o suficiente para extrapolar o `viewBox` de 320 unidades. Reavaliar se uma base real (Q-5 do SPEC) trouxer nomes de produto mais longos.
