---
baseline_commit: 'cd9e9175b2fa8a1876cdb892cc49c16c522976fe'
---

# Story 3.3: A extensibilidade do grafo, demonstrada por diff

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a desenvolvedor que vai plugar o roadmap,
I want provar que uma etapa nova entra sem alterar as existentes,
so that a única métrica que mede o objetivo declarado do projeto pare de ser uma afirmação.

## Acceptance Criteria

**AC1 — Nó novo sem tocar assinatura de nó existente**

**Given** o grafo do v1 completo
**When** um nó novo sem efeito é acrescentado ao `StateGraph`
**Then** o diff não toca a assinatura de nenhum nó existente (M-6, CAP-9)
**And** o diff não toca `estado.py` além de acrescentar chave, se acrescentar

**AC2 — Mesmo relatório, sem regressão**

**Given** o nó novo acrescentado
**When** o pipeline roda
**Then** produz o mesmo relatório de antes, sem regressão

**AC3 — Diff anexado como evidência, nó removido do entregue**

**Given** o exercício concluído
**When** ele é registrado
**Then** o diff é anexado como evidência de M-6
**And** o nó de demonstração é removido do código entregue

**AC4 — Itens não-aditivos do roadmap registrados como tais**

**Given** os itens de `roadmap.md`
**When** eles são conferidos contra o resultado do exercício
**Then** os pontos que a spine declara **não** aditivos — cache (exige versão do prompt no estado), cascata (`Sinal.valida` é booleano), loop de crítica (exige terceiro balde além de `analises` e `falhas`), níveis de criticidade (`na_fila` é booleano) — são registrados como tais
**And** M-6 é declarada atendida no eixo que ela cobre, sem ser inflada para cobrir esses quatro

## Tasks / Subtasks

- [x] **Task 1 — Acrescentar nó de demonstração ao grafo, temporariamente** (AC: 1)
  - [x] `def _no_demonstracao_m6(estado: Estado) -> dict:` / `return {}` adicionado (forma exata de duas linhas, corrigida de paráfrase de uma linha — achado de revisão)
  - [x] `grafo.add_node("_no_demonstracao_m6", _no_demonstracao_m6)`
  - [x] Aresta final trocada: `renderizar -> _no_demonstracao_m6 -> END`
  - [x] Diff conferido: só adições, nenhuma linha de nó existente muda (ver Dev Notes)
  - [x] `estado.py` não tocado

- [x] **Task 2 — Rodar o pipeline com o nó de demonstração e provar ausência de regressão** (AC: 2)
  - [x] `uv run python -m pytest -q` → `208 passed`, suíte inteira intacta
  - [x] `uv run python main.py docs/reclamacoes_reclameaqui.csv --sobrescrever` rodado com credencial real e o nó de demonstração presente
  - [x] Contagens registradas em Completion Notes
  - [x] Arquivo de prova apagado depois de confirmado

- [x] **Task 3 — Capturar o diff como evidência e reverter o código** (AC: 3)
  - [x] Diff colado em Dev Notes (evidência de M-6)
  - [x] `plataforma/grafo.py` revertido — `git diff` vazio confirmado
  - [x] `uv run python -m pytest -q` rodado de novo após o revert → `208 passed`, mesma contagem de antes

- [x] **Task 4 — Registrar M-6 e os itens não-aditivos do roadmap** (AC: 4)
  - [x] M-6 declarada atendida no eixo estrutural, ver Completion Notes
  - [x] Quatro itens não-aditivos do roadmap listados com o porquê
  - [x] Nenhuma inflação de escopo de M-6

### Review Findings

- [x] [Review][Patch] `roadmap.md` abre com "Tudo aqui é **aditivo**" — texto que, lido isolado, parece contradizer a lista de itens "não aditivos" do AC4. Reconciliado: a frase de `roadmap.md` é condicional, e `ARCHITECTURE-SPINE.md` §Deferred é a determinação técnica específica de onde essa condição falha hoje [Dev Notes]
- [x] [Review][Patch] Cascata entre modelos é classificada por `ARCHITECTURE-SPINE.md` como "**meio** aditiva", não flatamente "não aditiva" como os outros três [Dev Notes]
- [x] [Review][Patch] AC2 apoiado só em contagens agregadas de execuções diferentes — conectado explicitamente à prova lógica/estrutural já existente nas Dev Notes como a prova real de conteúdo idêntico [Completion Notes]
- [x] [Review][Patch] Explicitado que o nó de demonstração só é alcançado no caminho de análises não-vazio [Dev Notes]
- [x] [Review][Patch] Revert conferido também com `git status --short` do repositório inteiro, não só `grafo.py` [Completion Notes]
- [x] [Review][Patch] Bullet do Task 1 corrigido para a forma exata de duas linhas [Tasks/Subtasks]
- [x] [Review][Patch] Escopo do AC4 (quatro itens nomeados por `epics.md`, não auditoria completa de `roadmap.md`) explicitado [Dev Notes]

**Achados descartados (padrão já aceito no projeto / fora de escopo da AC / risco já mitigado na prática):**
- Números auto-relatados sem testemunha independente — mesmo padrão já aceito para toda verificação manual deste projeto (Stories 1.7 AC7, 2.6 AC7/AC8, execuções reais das Stories 3.1/3.2).
- Rodar contra a API real foi "desnecessário" já que o nó é comprovadamente fora do caminho de dados por construção — já executado, deu confiança de integração real (LangGraph aceita o nó sem erro em runtime) além do argumento estático, não há como nem por que desfazer.
- Nenhuma guarda automatizada nova contra um futuro "esqueceram de reverter o nó" — adicionaria máquina permanente para um exercício único, contra o princípio já estabelecido de não introduzir telemetria/CI não pedida.
- Cenário de nó que também tocasse `Estado` nunca exercitado — explicitamente fora do escopo desta AC (pede nó "sem efeito", não um nó que testa a fronteira de `Estado`).
- Posição do nó (depois de `renderizar`) é "a menos representativa" dos itens reais do roadmap — já divulgado e justificado como tradeoff deliberado nas Dev Notes, não uma lacuna escondida.
- Resíduo de bytecode `__pycache__` — Python invalida cache obsoleto automaticamente por hash/mtime do fonte, já coberto por `.gitignore`, não é traço real do nó de demonstração.
- Risco de colisão de nome de arquivo com relatório legítimo do mesmo dia — checado empiricamente antes de rodar (`ls docs/relatorio-*` vazio), nenhuma colisão ocorreu de fato.

## Change Log

- 2026-08-10: Nó de demonstração `_no_demonstracao_m6` acrescentado, exercitado (suíte + execução real ponta a ponta, 50/50/0), diff capturado como evidência, código revertido (`git diff` vazio). M-6 registrada no eixo estrutural; itens não-aditivos do roadmap listados. Nenhuma mudança líquida de código nesta story.
- 2026-08-10: Revisão adversarial (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Acceptance Auditor confirmou AC1/AC3 de forma independente via hash de blob git (o diff colado bate com o blob real, não é texto inventado) e AC4 contra `ARCHITECTURE-SPINE.md`. 7 patches aplicados, todos edição de documentação (esta story não tem código entregue) — reconciliação `roadmap.md`/AC4, nuance de cascata "meio aditiva", prova de conteúdo do relatório reforçada com o argumento estrutural, escopo do nó de demonstração no caminho de análises não-vazio explicitado, revert confirmado repo-wide, texto do checklist corrigido, escopo do AC4 explicitado. 0 achados deferidos, 7 dispensados por já corresponderem a padrão aceito no projeto ou estarem fora do escopo da AC.

## Dev Notes

### Por que o nó de demonstração vai depois de `renderizar`, não no meio do pipeline

Inserir entre `agregar` e `renderizar`, por exemplo, ainda provaria AC1 (nenhuma assinatura de nó existente muda), mas deixaria uma pergunta em aberto: "o nó extra não alterou silenciosamente o que `renderizar` recebeu?" — porque tecnicamente um nó entre dois outros participa do fluxo de dados, mesmo devolvendo `{}`. Colocar depois de `renderizar`, antes de `END`, fecha essa pergunta por construção: o HTML já foi escrito em disco quando o nó de demonstração roda. Não há como ele influenciar o relatório, nem em teoria — a prova de "sem regressão" (AC2) fica mais forte, não mais fraca, com essa escolha de posição.

### O entregável desta story é a evidência, não o código

Diferente de toda story anterior, o código final desta story é **idêntico** ao que existia antes dela — o nó de demonstração é acrescentado, exercitado, e revertido dentro da mesma story (AC3 exige isso explicitamente: "o nó de demonstração é removido do código entregue"). O que fica é: (1) o diff exato capturado nesta story como texto, (2) os números da execução real que provam que o pipeline com o nó extra funcionou, (3) a declaração honesta de M-6 no eixo que ela cobre. Não é trabalho perdido — é a natureza de uma métrica de **extensibilidade**: provar que dá para estender sem manter a extensão.

### Diff de evidência (Task 3 — capturado em 2026-08-10, antes do revert)

```diff
diff --git a/plataforma/grafo.py b/plataforma/grafo.py
index c0e9557..5a3579b 100644
--- a/plataforma/grafo.py
+++ b/plataforma/grafo.py
@@ -126,6 +126,9 @@ def construir_grafo(caminho: str, caminho_saida: str) -> CompiledStateGraph:
         provisorio.replace(destino)
         return {"caminho_html": str(destino)}
 
+    def _no_demonstracao_m6(estado: Estado) -> dict:
+        return {}
+
     grafo = StateGraph(Estado)
     grafo.add_node("carregar", carregar)
     grafo.add_node("analisar_lote", analise.analisar_lote)
@@ -133,6 +136,7 @@ def construir_grafo(caminho: str, caminho_saida: str) -> CompiledStateGraph:
     grafo.add_node("pontuar", pontuacao.pontuar)
     grafo.add_node("agregar", agregacao.agregar)
     grafo.add_node("renderizar", renderizar)
+    grafo.add_node("_no_demonstracao_m6", _no_demonstracao_m6)
 
     grafo.add_edge(START, "carregar")
     grafo.add_conditional_edges("carregar", despachar)
@@ -140,6 +144,7 @@ def construir_grafo(caminho: str, caminho_saida: str) -> CompiledStateGraph:
     grafo.add_conditional_edges("_verificar_conservacao", _rotear_apos_conservacao)
     grafo.add_edge("pontuar", "agregar")
     grafo.add_edge("agregar", "renderizar")
-    grafo.add_edge("renderizar", END)
+    grafo.add_edge("renderizar", "_no_demonstracao_m6")
+    grafo.add_edge("_no_demonstracao_m6", END)
 
     return grafo.compile()
```

**Leitura do diff (AC1):** as únicas linhas tocadas são adições — uma função nova (`_no_demonstracao_m6`), um `add_node` novo, e a troca de `grafo.add_edge("renderizar", END)` por duas arestas que passam pelo nó novo antes de `END`. Nenhuma linha de `carregar`, `despachar`, `_verificar_conservacao`, `_rotear_apos_conservacao`, nem das chamadas a `pontuacao.pontuar`/`agregacao.agregar`/`analise.analisar_lote`, muda. `plataforma/estado.py` não aparece no diff — zero toque.

**O nó de demonstração só é alcançado no caminho de análises não-vazio (achado de revisão).** `_rotear_apos_conservacao` desvia direto para `END` quando `analises` está vazio (AD-13) — essa aresta condicional nunca passa por `renderizar`, então nunca passa pela nova aresta `renderizar -> _no_demonstracao_m6` também. Isso não é uma lacuna do exercício: o caminho de zero análises não produz relatório de qualquer forma, com ou sem o nó de demonstração — não há nada para regredir ali por construção. A execução real desta story (Task 2) exercitou o caminho comum (análises não-vazio), que é exatamente onde o nó novo entra.

### Por que `test_construir_grafo_tem_os_nos_esperados_sem_invocar` não precisa mudar

O teste existente (`tests/test_grafo.py`) faz `assert esperado in nos` para cada nó esperado — verifica que a lista conhecida de nós **está presente**, não que **só ela existe**. Um nó extra no grafo compilado não quebra esse teste. Isso é uma propriedade favorável para esta story (o exercício não exige tocar `tests/test_grafo.py`), mas também significa que a suíte **não detectaria sozinha** se o nó de demonstração fosse esquecido no código entregue — por isso a Task 3 confere `git diff` vazio manualmente, não confia só em testes passando.

### Reconciliando `roadmap.md` ("tudo é aditivo") com o AC4 (achado de revisão)

`roadmap.md` abre com "Tudo aqui é **aditivo** — pluga sobre o v1 sem reescrever, **desde que o contrato em `state-contract.md` esteja correto desde o início**." Essa é uma condição, não uma garantia incondicional. `ARCHITECTURE-SPINE.md` §Deferred é a determinação técnica específica de **onde** essa condição falha hoje: cache, cascata, loop de crítica e níveis de criticidade cada um exigiria mudança na forma de `Estado`/`Sinal`/`Falha` que o v1 não tem — não é contradição entre os dois documentos, é `roadmap.md` declarando a intenção de design e `ARCHITECTURE-SPINE.md` registrando onde a intenção ainda não foi atendida. O AC4 desta story cita corretamente a segunda fonte, mais específica, para a lista de itens não aditivos.

**Nuance de grau, não de categoria:** dos quatro, `ARCHITECTURE-SPINE.md` classifica cascata como "**meio** aditiva" (não flatamente não-aditiva como os outros três) — o contrato de `Sinal.valida` (`bool`) não comporta "dois modelos concordaram", mas o resto da cascata (roteamento condicional, sublote de escalada) já tem estrutura pronta no fan-out via `Send` (AD-8). Os outros três — cache, loop de crítica, níveis de criticidade — são não-aditivos sem ressalva.

**Escopo do AC4:** a AC nomeia exatamente estes quatro itens (texto de `epics.md`), não pede uma auditoria de todo `roadmap.md`. Outros itens do roadmap (checkpoint persistido, guard-rails de entrada/saída) já são classificados como "aditivos de fato" pelo mesmo `ARCHITECTURE-SPINE.md` §Deferred, fora do escopo desta AC.

### O que esta story NÃO faz

**Não implementa nenhum item do roadmap** (cache, cascata, loop de crítica, níveis de criticidade) — só demonstra que a estrutura aceita uma etapa nova sem quebrar as existentes.
**Não deixa o nó de demonstração no código entregue.** Ver AC3 e Task 3.
**Não altera `Estado`.** O nó de demonstração não lê nem escreve nenhuma chave.
**Não roda a suíte de medição (`medir_fila.py`/`medir_tempo_custo.py`) de novo** — os números de `lidas`/`analisadas` desta execução só precisam bater com os já registrados nas Stories 3.1/3.2 para confirmar ausência de regressão, não repetir a medição completa de M-1/M-3/M-4.

### Estrutura de arquivos

```text
plataforma/
  grafo.py   # UPDATE temporário — nó de demonstração acrescentado, exercitado, revertido dentro desta story
```

**Não criar/tocar nesta story, no código entregue final:** qualquer arquivo além do estado transitório de `grafo.py` durante o exercício (que volta ao original antes do commit). `estado.py`, `main.py`, `tests/`, `medir_fila.py`, `medir_tempo_custo.py` — nenhum precisa mudar.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **M-6** | Demonstrado por diff real, capturado e revertido — não uma afirmação sem exercício |
| **AD-19** | O nó de demonstração não escreve nenhuma chave de `Estado` — não compete com nenhum escritor existente |
| **CAP-9** | Orquestração: prova que `grafo.py` aceita nó novo sem alterar `carregar`/`analisar_lote`/`pontuar`/`agregar`/`renderizar` |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3] — ACs originais
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/roadmap.md] — itens v2/v3 a conferir contra o exercício (AC4)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-plataforma-analise-reclamacoes-2026-08-06/ARCHITECTURE-SPINE.md#Deferred] — por que cache/cascata/loop de crítica/níveis não são puramente aditivos, texto já pronto para reaproveitar no registro do AC4
- [Source: plataforma/grafo.py#construir_grafo] — onde o nó de demonstração entra e sai
- [Source: tests/test_grafo.py#test_construir_grafo_tem_os_nos_esperados_sem_invocar] — por que não precisa mudar (ver Dev Notes)
- [Source: _bmad-output/implementation-artifacts/3-1-a-fila-do-pipeline-medida-contra-o-gabarito.md, 3-2-o-tempo-e-o-custo-de-uma-execucao-medidos.md] — números de referência (lidas/analisadas) para comparar ausência de regressão

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-story) — implementado diretamente pelo agente principal.

### Debug Log References

- `uv run python -m pytest -q` (via PowerShell): `208 passed` com o nó de demonstração presente; `208 passed` de novo depois do revert — mesma contagem, prova de revert completo.
- `uv run python main.py docs/reclamacoes_reclameaqui.csv --sobrescrever` executado com o nó de demonstração presente, credencial real do ambiente.
- `git diff -- plataforma/grafo.py` vazio depois do `git checkout -- plataforma/grafo.py` — confirmado antes de prosseguir.

### Completion Notes List

**Execução de prova (2026-08-10), com o nó de demonstração presente:**

```
lidas                     50
analisadas                50
não analisadas             0  (0 evento(s) de falha)
códigos derrubados         0
arquivo gerado         docs\relatorio-reclamacoes_reclameaqui-2026-08-10.html
```

- **AC1:** diff conferido linha a linha (colado em Dev Notes) — só adições (uma função nova, um `add_node`, duas arestas substituindo uma). Nenhuma assinatura de `carregar`, `despachar`, `_verificar_conservacao`, `_rotear_apos_conservacao`, `analisar_lote`, `pontuar`, `agregar` ou `renderizar` muda. `plataforma/estado.py` não aparece no diff.
- **AC2 — duas provas complementares, não uma:** (1) **lógica/estrutural** — o nó de demonstração roda estritamente depois de `renderizar` já ter escrito o HTML em disco (`Path.replace` atômico já concluído) e `return {}` não lê nem escreve nenhuma chave de `Estado`, muito menos toca o sistema de arquivos; por construção, é impossível ele alterar o conteúdo do relatório, e essa prova não depende de rodar nada — é verificável só lendo o código. (2) **integração real** — o pipeline rodou ponta a ponta com o nó extra presente, sem erro do LangGraph nem do restante do grafo: 50 lidas, 50 analisadas, 0 falhas, 0 códigos derrubados, idêntico ao padrão já observado nas Stories 3.1/3.2. A prova (2) mostra que o grafo *aceita* o nó sem quebrar; a prova (1) é que garante *conteúdo* idêntico — a combinação das duas é o que sustenta "mesmo relatório, sem regressão", não a contagem agregada sozinha. O relatório gerado foi inspecionado (9,7K, seção de fila presente, `<!doctype html>` válido) antes de ser apagado — a prova de conteúdo não depende de reter o arquivo, porque vem do argumento (1).
- **AC3:** diff colado em Dev Notes como evidência permanente. `plataforma/grafo.py` revertido — `git diff -- plataforma/grafo.py` vazio confirmado. **Revert conferido também em nível de repositório** (achado de revisão): `git status --short` depois do revert mostra só a própria story e `sprint-status.yaml` modificados — nenhum outro arquivo (`estado.py` incluído) ficou com resíduo do exercício. Suíte com a mesma contagem de testes antes/depois (`208 passed` nos dois casos). Nenhum vestígio do nó de demonstração no código entregue.
- **AC4 — M-6 declarada no eixo que este exercício cobre:** acrescentar uma etapa passiva (que não lê nem escreve nenhuma chave de `Estado`) ao `StateGraph` não exigiu tocar a assinatura de nenhuma etapa existente. **M-6 não é declarada para os quatro itens abaixo**, que `ARCHITECTURE-SPINE.md` (§Deferred) já registra como não puramente aditivos:
  - **Cache de chamadas** — exige uma versão do prompt como campo em `Estado`, que hoje não existe em lugar nenhum; chave de cache sem essa versão serve resposta velha para prompt novo.
  - **Cascata entre modelos** — `Sinal.valida` é `bool`, não comporta "dois modelos concordaram"; o contrato de `Sinal` precisaria mudar de forma, não só ganhar um nó.
  - **Loop de crítica** — exige um terceiro balde reduzido além de `analises`/`falhas`, o que muda a identidade de AD-6 (conservação) e a semântica de `Falha` que FR-2/NFR-6 já consomem.
  - **Níveis de criticidade na fila** — `na_fila` é `bool`, decidido em `pontuacao.py` e consumido direto por `agregacao.py`/template; não é uma etapa nova, é uma mudança de forma no meio do pipeline existente.
- Nenhum desvio de design em relação ao que a story especificou. O código entregue por esta story é idêntico ao código antes dela — o entregável é a evidência documentada, não uma mudança de comportamento.

### File List

_(nenhum arquivo de código muda no estado final — `plataforma/grafo.py` foi revertido ao original; ver Dev Notes para o diff transitório usado como evidência)_

| Arquivo | Tipo |
|---|---|
| `_bmad-output/implementation-artifacts/3-3-a-extensibilidade-do-grafo-demonstrada-por-diff.md` | novo (este arquivo — contém a evidência) |
