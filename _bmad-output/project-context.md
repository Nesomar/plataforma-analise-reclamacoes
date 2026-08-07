---
project_name: 'plataforma-analise-reclamacoes'
user_name: 'Neo'
date: '2026-08-07'
sections_completed:
  ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
status: 'complete'
rule_count: 51
optimized_for_llm: true
existing_patterns_found: 9
---

# Project Context for AI Agents

_Este arquivo carrega as regras e padrões que agentes de IA devem seguir ao implementar código neste projeto. O foco é o que não é óbvio — o que um agente erraria por padrão._

---

## Technology Stack & Versions

**Gerenciador de pacotes: `uv`.** Há `uv.lock` versionado. Todo comando roda por `uv run python <arquivo>`, nunca `python` direto — o README documenta assim e o `.venv` é do uv.

| Camada | Item | Versão | Estado |
|---|---|---|---|
| Linguagem | Python | `>=3.11` | instalado |
| LLM SDK | `google-genai` | `>=2.17.0` | instalado |
| Config | `python-dotenv` | `>=1.2.2` | instalado |
| Schema | `pydantic` | transitivo do `google-genai` | **não declarado** em `pyproject.toml`, mas usado por `classificador.py` |
| Orquestração | `langgraph` | `1.2.10` | **ausente** — exigido pela spine, ainda não instalado |
| Template | `jinja2` | `3.1.6` | **ausente** — exigido pela spine |
| Testes | `pytest` | `9.1.1` | instalado — `[dependency-groups] dev` (Story 1.1) |
| Modelo | `gemini-3.6-flash` | pinado | em `classificador.py:23` |

**O modelo é pinado de propósito.** `classificador.py` registra o motivo: alias móvel invalida comparação de F1 entre execuções. Não trocar para `gemini-flash-latest` ou equivalente.

**Sem ferramentas de qualidade configuradas.** Não há `ruff`, `black` nem `mypy`. A única seção `[tool.*]` do `pyproject.toml` é `[tool.pytest.ini_options]`, com `pythonpath = ["."]` e `testpaths = ["tests"]` — o pacote não é instalado (não há `[build-system]`), então o import resolve pelo diretório de trabalho. Não introduzir ferramenta de qualidade sem pedido — o projeto é deliberadamente enxuto.

**Estado do repositório:** `baseline.py` e `classificador.py` na raiz (medição, preexistentes), `docs/` com CSVs, `_bmad-output/` com o planejamento. O pacote `plataforma/` existe desde a Story 1.1 com `estado.py` e `catalogo.py`; `tests/` roda por `uv run pytest`.

## Critical Implementation Rules

### Regras de Linguagem (Python)

- **Português em tudo:** módulos, funções, variáveis, docstrings, mensagens ao operador. Nós do grafo nomeados pelo verbo da etapa: `carregar`, `analisar_lote`, `pontuar`, `agregar`, `renderizar`.
- **Sem classes em código de domínio.** `TypedDict` para o estado, funções puras sobre dicts. `pydantic.BaseModel` só onde o `response_schema` do `google-genai` exige.
- **`sys.stdout.reconfigure(encoding="utf-8")` em todo entrypoint executável.** O console do Windows não é UTF-8 por padrão e a saída sai corrompida sem isso.
- **CSV sempre `encoding="utf-8-sig"` e `delimiter=";"`.** Ler com `utf-8` cru cola um BOM no nome da primeira coluna, e o `KeyError` aparece longe da causa.
- **Datas ISO-8601 no estado.** `DD/MM/AAAA` existe só na fronteira de leitura do CSV.
- **Docstring de módulo:** uma linha de propósito, depois o porquê da escolha não-óbvia, depois `Rode: uv run python <arquivo>.py` se for executável.
- **Comentário explica _por que_, nunca _o que_.** Padrão do repo: `MODELO = "gemini-3.6-flash"  # pinado de propósito: alias móvel invalida comparação de F1`
- **`# ponytail:` prefixa simplificação deliberada** com o teto nomeado e o caminho de upgrade.
- **Executar sempre por `uv run python`**, nunca `python` direto.

### Regras de Framework (LangGraph · google-genai · Jinja2)

- **Um único filtro impuro (AD-7).** Só `analise.py` importa `google.genai`, direta ou transitivamente. O cliente é construído **dentro** de `analisar_lote` — cliente em escopo de módulo faz `import analise` exigir credencial e derruba a suíte inteira.
- **O payload do modelo carrega `id` e `texto`, nada mais (AD-16).** `empresa` e `titulo` ficam fora **por construção**, não por instrução no prompt. O título desta base é canônico e entrega a resposta — enviá-lo esvazia M-1.
- **Saída do modelo por `response_schema` com `temperature=0`.** Nunca parsing de texto livre. Resposta fora do schema é falha de conteúdo (vira `Falha`), não exceção que aborta.
- **Casamento por `id`, nunca por posição.** Id faltante vira `Falha`; id repetido ou inventado é descartado e não soma a agregado nenhum.
- **O lote é uma execução de nó (AD-8),** despachada por `Send`, não uma iteração dentro de um nó. `analises` e `falhas` acumulam pelo redutor `add`.
- **Repetição é política, não código (AD-9).** `retry_policy=` e `error_handler=` no `add_node`; nenhum laço de repetição dentro do nó. `error_handler` é **obrigatório** — sem ele, retry esgotado propaga exceção e aborta o grafo.
- **Um escritor por chave de `Estado` (AD-19).** `pontuacoes` é de `pontuar`, inclusive `na_fila`. `agregados` é de `agregar`, que ordena e conta e nunca decide pertencimento.
- **Jinja2: um único `Environment`, em `relatorio.py`, com `autoescape=True` literal (AD-10).** Não usar `select_autoescape` — o seletor casa por extensão, `relatorio.html.j2` cai no `default=False`, e o escape fica desligado numa linha que parece a defesa.
- **Nada externo no HTML (AD-11).** Nenhum `<script src>`, `<link href>` ou `@import` apontando para fora do arquivo. Gráficos são `<svg>` no template.

### Regras de Teste

- **Nenhum teste faz chamada de rede (AD-12).** Verificar, pontuar, agregar e renderizar são funções puras alimentadas por `Analise` fabricada à mão.
- **A suíte roda sem `GOOGLE_API_KEY` definida.** Importar qualquer módulo do pacote sem credencial precisa funcionar — é a verificação executável de AD-7.
- **`pytest` em `tests/`, mas `autoteste()` continua vivo.** Módulo executável na raiz (`baseline.py`, `classificador.py`) carrega `autoteste()` com `assert` chamado no `if __name__ == "__main__"`. Não converter esses dois para pytest; não replicar o padrão dentro de `plataforma/`.
- **`assert` com mensagem que nomeia o valor observado.** Padrão do repo: `assert filtrado["precisao"] >= 0.95, f"M-1: precisão {filtrado['precisao']:.1%}"`
- **Sem mocks do SDK.** O que depende do modelo não é testado; o que não depende é testado sem ele. Não existe camada de mock do `google-genai` neste projeto.
- **Casos construídos à mão são obrigatórios para o que a base não exercita:** `ameaca_explicita`, `dano_continuado`, `registro_contraditorio` e a citação falsa injetada de propósito. A suíte é a única coisa que executa esses caminhos — CM-2 em zero é indistinguível de mecanismo morto sem eles.
- **Asserção de conservação (AD-6)** roda em produção, não só em teste: `len(reclamacoes) == len(analises) + sum(len(f["ids"]) for f in falhas)`, após o gather e antes de `pontuar`.
- **Sem meta de cobertura.** Nenhuma é declarada e não se deve inventar uma.

### Regras de Qualidade e Estilo

- **Não introduzir `ruff`, `black`, `mypy` ou hooks.** Nenhum está configurado, e a ausência é deliberada.
- **Não acrescentar dependência que uma dúzia de linhas resolve.** As deps são a lista fechada da spine: `langgraph`, `google-genai`, `jinja2`, `python-dotenv`, `pytest`. Qualquer outra exige justificativa explícita.
- **`pydantic` é transitivo do `google-genai`.** Se um módulo passar a depender dele diretamente, declarar em `pyproject.toml` — não herdar em silêncio.
- **Um arquivo por filtro, nomeado pela etapa.** `plataforma/{estado, catalogo, ingestao, analise, evidencia, pontuacao, agregacao, relatorio, grafo, config}.py` · `plataforma/templates/relatorio.html.j2` · `main.py` · `tests/`.
- **Nenhum filtro importa outro filtro.** Exceção única e declarada: `analise` importa `evidencia`. `estado.py` não importa nada de `plataforma/`.
- **Texto visível ao leitor vive no template, não em Python (AD-10).** Ressalvas de FR-13, FR-16 e FR-18 são conteúdo do `.j2`.
- **Nenhum código de sinal como literal solto (AD-18).** Códigos, definições, pesos e a lista de termos genéricos vivem em `catalogo.py` e `pontuacao.py`, importados de lá pelo prompt, pela pontuação e pelo template.
- **Saída de terminal em tabela alinhada por f-string,** no padrão de `baseline.py`. A saída do operador é a observabilidade do sistema — não há log estruturado, métrica exportada nem trace, e não se deve adicionar.

### Regras de Workflow

- **Branch por tipo:** `docs/`, `chore/`, `feat/`, `fix/`. Trabalho vai em branch e entra por PR; não commitar em `main`.
- **Nunca commitar sem pedido explícito do usuário.**
- **Dados: só sintéticos no repositório (DG-1).** Base real de reclamações nunca entra, nem relatório gerado a partir dela (DG-2). Relatório sobre base real herda os dados pessoais das citações que exibe e é documento restrito (DG-3).
- **`.gitignore` é dependência funcional, não higiene.** AD-15 depende do glob `relatorio*.html`: o arquivo de saída precisa começar com `relatorio-` para nascer ignorado. Renomear a saída sem ajustar o glob vaza relatório para o repositório público.
- **Credencial só de variável de ambiente (NFR-10).** Nunca em código, template, teste ou repositório. `.env.example` lista os nomes e nenhum valor.
- **Fonte única para números medidos:** `risk-signals.md` para pesos e corte, `state-contract.md` para a forma do estado, `SPEC.md` para capacidades. Código que discorda de um deles é o código que está errado.

### Armadilhas Deste Repositório

- **`GEMINI_API_KEY` vs `GOOGLE_API_KEY`.** O README exporta `GEMINI_API_KEY`, o `.env.example` declara `GOOGLE_API_KEY`, e `classificador.py:125` faz a ponte com `os.environ.setdefault`. **`GOOGLE_API_KEY` é o nome que o SDK lê.** Ao criar `config.py`, adotar `GOOGLE_API_KEY` como canônico e corrigir o README.
- **`Agregados` é referenciado em `state-contract.md` e nunca definido lá.** Os campos vêm de AD-22: as contagens que FR-2, FR-14, NFR-6, CM-2 e CM-3 reportam. Não inventar forma sem consultar essas fontes.
- **`langgraph` e `jinja2` não estão em `pyproject.toml`.** Confirmado contra `uv.lock`. Instalar na story que primeiro precisar, não as duas de uma vez. `pytest` já entrou na Story 1.1.
- **`.cache_analises.json` na raiz é cache de medição de `classificador.py`.** Q-8 exige cronometrar NFR-1 **com ele desligado** — medir com cache mede o disco, não o pipeline.
- **`INSTRUCAO` em `classificador.py:42-77` já contém a definição escrita de `dinheiro_retido` (as seis situações) e de `ameaca_explicita`.** É texto validado contra o gabarito. Reaproveitar em `catalogo.py` em vez de reescrever.
- **Um lote residual de tamanho 1 é proibido (AD-17).** `tamanho_lote = 7` em 50 linhas deixa um último lote de 1 — a chamada individual que o SPEC veta. Fundir ao anterior. Faixa válida: 2 a 25, validada antes de qualquer chamada paga.
- **Citação vazia passa em `in` (FR-6).** String vazia é substring de qualquer texto. O piso de cinco palavras é verificado **no mesmo lugar** que a verificação de substring, nunca só no prompt.
- **Citação inválida derruba o código inteiro (AD-2),** inclusive os pares do mesmo código que passaram. A contagem reportada é de **códigos derrubados** — não de pares reprovados, não de reclamações afetadas.
- **Relatório sobre zero análises não é relatório (AD-13).** `len(analises) == 0` encerra com causa nomeada e **não escreve arquivo**. Falha absorvida não é permissão para produzir relatório sobre nada.
- **Falha de conteúdo vira `Falha` e a execução segue; falha de infraestrutura encerra sem escrever relatório,** informando o que havia concluído.

---

## Usage Guidelines

**Para agentes de IA:**

- Ler este arquivo antes de implementar qualquer código.
- Seguir todas as regras exatamente como documentadas.
- Na dúvida, escolher a opção mais restritiva.
- Quando uma regra daqui conflitar com o código existente, o código está errado — as fontes canônicas são `SPEC.md`, `ARCHITECTURE-SPINE.md`, `state-contract.md` e `risk-signals.md`.
- Atualizar este arquivo quando um padrão novo se estabelecer.

**Para humanos:**

- Manter enxuto e focado no que o agente erraria sozinho. Regra óbvia é ruído.
- Atualizar quando a stack mudar — em especial ao instalar `langgraph` e `jinja2`.
- Remover armadilha que deixar de existir: a divergência `GEMINI_API_KEY`/`GOOGLE_API_KEY` e a ausência de `Agregados` em `state-contract.md` são dívidas, não fatos permanentes.

Last Updated: 2026-08-07
