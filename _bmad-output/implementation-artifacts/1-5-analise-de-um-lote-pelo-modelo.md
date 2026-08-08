# Story 1.5: Análise de um lote pelo modelo

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a operador,
I want que cada lote de reclamações volte do modelo com sentimento, produto e sinais já casados por identificador,
so that uma resposta incompleta ou inventada seja detectada em vez de corromper a base em silêncio.

## Acceptance Criteria

**AC1 — Payload carrega só id e texto (AD-16)**

**Given** um lote de reclamações
**When** o payload é montado para o modelo
**Then** ele carrega apenas `id` e `texto` de cada reclamação
**And** `empresa` e `titulo` estão ausentes por construção, não por instrução no prompt

**AC2 — Resposta por `response_schema`, nunca texto livre**

**Given** a chamada ao modelo
**When** a resposta é obtida
**Then** ela vem por `response_schema` do `google-genai`, derivado de `Analise` e `Sinal`
**And** nenhum parsing de texto livre é feito
**And** cada item traz `sentimento` em `{positivo, neutro, negativo}`, `produto` (`str | None`) e `sinais`

**AC3 — Identificador faltante vira `Falha` (NFR-7, AD-5)**

**Given** um lote de 20 e uma resposta com 19 itens
**When** o casamento por identificador roda
**Then** o identificador faltante é detectado e vira uma `Falha` que carrega aquele id

**AC4 — Identificador repetido ou inventado é descartado (NFR-7)**

**Given** uma resposta que traz um identificador repetido ou um que não estava no lote
**When** o casamento por identificador roda
**Then** o item é descartado e não soma a agregado nenhum

**AC5 — Resposta fora do schema vira falha de conteúdo, não exceção**

**Given** uma resposta que não casa com o `response_schema`
**When** ela é processada
**Then** vira falha de conteúdo registrada como `Falha`, não exceção que aborta a execução

**AC6 — Verificação de evidência roda antes do delta entrar no estado (AD-1)**

**Given** cada sinal devolvido pelo modelo
**When** o delta do nó é montado
**Then** a verificação de evidência já rodou sobre ele antes de o delta entrar no estado

**AC7 — Produto passa sem julgamento (AD-21)**

**Given** o campo `produto` devolvido pelo modelo
**When** ele entra no estado
**Then** vem como o modelo leu, sem julgamento de genérico
**And** `produto = None` significa apenas *o texto não permitiu identificar*

**AC8 — Único módulo com o SDK, cliente só dentro da função (AD-7)**

**Given** o pacote `plataforma/`
**When** os imports de todos os módulos são inspecionados
**Then** `analise.py` é o único que importa `google.genai`
**And** o cliente é construído dentro de `analisar_lote`, nunca em escopo de módulo
**And** `import plataforma.analise` funciona sem credencial definida

## Tasks / Subtasks

- [x] **Task 0 — Declarar `pydantic` como dependência direta** (AC: 2)
  - [x] Acrescentar `pydantic>=2.13` a `[project] dependencies` em `pyproject.toml` (já instalado como transitivo do `google-genai`, versão real `2.13.4` — regra do repo: dependência direta não herda em silêncio, precisa constar)
  - [x] Rodar `uv sync` (ou equivalente) e confirmar que `uv.lock` não muda de forma inesperada

- [x] **Task 1 — Criar `plataforma/analise.py`** (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [x] **A decisão central desta story: separar a chamada impura da lógica pura de casamento.** `analisar_lote(lote: list[Reclamacao]) -> dict` faz só a parte impura — construir o cliente, montar o payload, chamar o modelo — e delega toda a lógica de casamento/descarte/falha para uma função pura auxiliar, algo como `_montar_delta(lote: list[Reclamacao], analises_modelo: list[_AnaliseResposta] | None) -> dict`. **Sem essa separação, AC3/AC4/AC5 são improváveis de testar** — o repositório proíbe mock do SDK (ver Dev Notes), então a única forma de testar "resposta incompleta" ou "resposta fora do schema" é alimentar a função pura diretamente com uma lista fabricada ou com `None`, nunca chamando `generate_content`
  - [x] Duas classes `pydantic.BaseModel` privadas ao módulo (prefixo `_`) para o `response_schema` — **não** reexportar nem usar em outro módulo: `_SinalResposta` com `codigo: str` e `citacao: str` (sem `valida` — o modelo nunca decide validade, só o código decide, via `evidencia.verificar`); `_AnaliseResposta` com `id: str`, `sentimento: Literal["positivo","neutro","negativo"]`, `produto: str | None`, `sinais: list[_SinalResposta]`. Envolver numa terceira, `_LoteResposta` com `analises: list[_AnaliseResposta]`, no padrão que `classificador.py:28-39` já usa (`Analise`/`Lote`)
  - [x] `_montar_payload(lote) -> list[dict]`: só `{"id": r["id"], "texto": r["texto"]}` por reclamação — função pura, testável isolada (AC1)
  - [x] `_montar_instrucao() -> str`: monta o texto do prompt iterando `catalogo.CATALOGO` (cada código com `definicao` e `exemplo`) mais as regras de `sentimento` e `produto` — **não reescrever as definições dos sinais**, elas já vivem em `catalogo.py` (CAP-4, AD-18) e foram validadas contra o gabarito; só formatar. Reaproveitar o tom de `classificador.py:42-77` (`INSTRUCAO`) para a prosa de sentimento/produto e para a instrução geral de "nunca invente citação"
  - [x] `analisar_lote(lote)`: constrói `cliente = genai.Client()` **dentro** da função (AD-7); monta payload e instrução; chama `cliente.models.generate_content(model=..., contents=json.dumps(payload, ensure_ascii=False), config=types.GenerateContentConfig(system_instruction=..., response_mime_type="application/json", response_schema=_LoteResposta, temperature=0))`, no padrão de `classificador.py:82-91`; lê `resposta.parsed.analises if resposta.parsed else None`; delega a `_montar_delta(lote, ...)`
  - [x] `_montar_delta(lote, analises_modelo)`:
    - Se `analises_modelo is None` (schema não casou — AC5): devolve `{"analises": [], "falhas": [Falha(ids=[r["id"] for r in lote], causa="...", no="analisar_lote")]}` — **o lote inteiro** vira uma `Falha`, porque sem resposta casada não há como saber qual item era qual
    - Senão, casar por `id`: para cada item de `analises_modelo`, ignorar se o `id` não está no lote (inventado, AC4); manter só a primeira ocorrência de cada `id` (repetido, AC4) — **não gerar `Falha` nem para o inventado nem para o repetido**, eles são apenas descartados
    - Para cada `id` do lote sem correspondência na resposta: acumular numa lista de faltantes
    - Para cada item casado: construir os `Sinal` brutos (`valida=False`) a partir de `_SinalResposta`, chamar `evidencia.verificar(sinais_brutos, texto_da_reclamacao)` **antes** de montar a `Analise` final (AC6) — este é o ponto de integração com a Story 1.4
    - Montar `Analise(id=..., sentimento=..., produto=..., sinais=sinais_verificados, prazo_prometido_dias=None, data_evento=None)` — ver Dev Notes sobre os dois últimos campos
    - Se houver faltantes, acrescentar **uma** `Falha(ids=faltantes, causa="...", no="analisar_lote")` à lista de falhas (AC3)
    - Devolver `{"analises": [...], "falhas": [...] ou []}`
  - [x] Docstring de módulo no padrão dos anteriores: propósito, porquê não-óbvio (a separação impuro/puro é o candidato natural)
  - [x] Imports permitidos: `json`, `typing.Literal`, `pydantic.BaseModel`, `google.genai`/`google.genai.types`, mais `plataforma.estado`, `plataforma.catalogo`, `plataforma.evidencia` (única exceção documentada de filtro importando filtro)

- [x] **Task 2 — Criar `tests/test_analise.py`** (AC: 1, 3, 4, 5, 6, 7, 8)
  - [x] `_montar_payload`: lote com `empresa`/`titulo` preenchidos → payload não contém essas chaves, só `id`/`texto` (AC1)
  - [x] `_montar_delta` caso feliz: lote de 2, `analises_modelo` fabricado com os 2 ids, sinais com citação real de um texto controlado → `analises` tem 2 itens, `falhas` vazia, e o `Sinal` verificado reflete `evidencia.verificar` (uma citação inventada no meio deve sair `valida=False` — prova que AC6 realmente rodou, não só que a função foi chamada)
  - [x] `_montar_delta` com id faltante: lote de 2, `analises_modelo` só com 1 → `falhas` tem uma `Falha` com o id faltante (AC3)
  - [x] `_montar_delta` com id repetido: `analises_modelo` traz o mesmo id duas vezes → só uma `Analise` no resultado, sem `Falha` extra (AC4)
  - [x] `_montar_delta` com id inventado: `analises_modelo` traz um id que não está no lote → esse item não aparece em `analises`, e não gera `Falha` (AC4)
  - [x] `_montar_delta` com `analises_modelo=None`: devolve `analises=[]` e uma única `Falha` cobrindo todos os ids do lote (AC5)
  - [x] `produto=None` do modelo atravessa sem alteração até a `Analise` final (AC7)
  - [x] Import sem credencial: `monkeypatch.delenv("GOOGLE_API_KEY")`/`GEMINI_API_KEY`, importar `plataforma.analise` e confirmar que não levanta (AC8) — **não** acrescentar este módulo a `tests/test_import_sem_credencial.py::MODULOS`, que é para módulos que **não** arrastam o SDK; `analise.py` arrasta por design. Escrever um teste próprio em `test_analise.py`
  - [x] Nenhum teste chama `generate_content` nem monta `genai.Client()` — todo teste alimenta `_montar_delta` ou `_montar_payload` diretamente com dados fabricados à mão (AD-12; o repositório não tem camada de mock do SDK)

## Dev Notes

### A decisão que torna esta story testável sem rede — leia antes de codar

O repositório **proíbe mock do `google.genai`** (`project-context.md`: "Sem mocks do SDK... não existe camada de mock do `google-genai` neste projeto"). Isso parece, à primeira vista, incompatível com testar AC3 (id faltante), AC4 (id repetido/inventado) e AC5 (schema não casa) — três cenários que só existiriam numa resposta real do modelo.

A saída é estrutural, não é mockar: `analisar_lote` fica fino — só client, payload, chamada — e delega **toda** a lógica de decisão (casamento por id, descarte, verificação de evidência, montagem de `Falha`) para `_montar_delta`, uma função pura que recebe a resposta **já como estrutura Python** (`list[_AnaliseResposta] | None`), nunca uma resposta HTTP. Testar `_montar_delta` diretamente com listas fabricadas à mão cobre AC3/AC4/AC5 inteiramente sem tocar o SDK — no mesmo espírito de AD-12 ("tudo que o modelo não decide é testável sem o modelo"): quem decide o schema, o texto de resposta, a rede — isso é do SDK; quem decide o que fazer com o resultado — isso é nosso e é puro.

### Confirmado no SDK instalado: como detectar "resposta fora do schema" (AC5)

`google/genai/types.py:8708-8724` (SDK `2.17.0`+ instalado neste projeto): quando `response_schema` é uma classe `pydantic.BaseModel`, a lib tenta `response_schema.model_validate_json(result_text)` dentro de um `try`; se levantar `pydantic.ValidationError` ou `json.decoder.JSONDecodeError`, o `except` **engole a exceção e `result.parsed` simplesmente não é setado** — fica com o default (`None`). **Não há exceção para capturar.** A checagem certa é `if resposta.parsed is None`, não `try/except`. Verificado lendo o código-fonte instalado, não a documentação pública — mesma disciplina que a Story 1.2 aplicou para `GOOGLE_API_KEY`/`GEMINI_API_KEY`.
[Source: .venv/Lib/site-packages/google/genai/types.py:8708-8724]

### Dois campos do contrato que esta story deliberadamente não preenche

`Analise.prazo_prometido_dias` e `Analise.data_evento` existem em `estado.py` (Story 1.1) e em `state-contract.md`, mas **nenhuma AC de nenhuma story** — nem `epics.md`, nem `SPEC.md` (CAP-2/3/4 cobrem só sentimento, produto, sinais) — pede que o modelo os preencha. `risk-signals.md`/`SPEC.md` já registram que `prazo_estourado` foi resolvido como **código de sinal simples**, sem aritmética de data: *"Prazo estourado sem data de evento — resolvido: parcela mantida com peso 1, reconhecidamente fraca nesta base."* Tudo indica que os dois campos são resíduo do brainstorm original (`spec-tecnico-v1.md:30-31,72`) que não sobreviveu à triagem de capacidades.

**Decisão desta story: `_AnaliseResposta` não pede esses campos ao modelo, e `_montar_delta` sempre monta `Analise` com `prazo_prometido_dias=None` e `data_evento=None`.** O contrato de estado continua satisfeito (`AD-20` exige os campos presentes, não exige valor não-nulo) sem inventar uma capacidade que nenhum requisito pede. Se isso estiver errado, é conversa de correção de curso, não decisão a tomar durante a implementação.
[Source: plataforma/estado.py:39-40, state-contract.md:34-35, SPEC.md#Resolved, epics.md#Story 1.5 AC2 — só três dimensões]

### O que esta story NÃO faz

**Não integra com `grafo.py`.** `analisar_lote` já tem a forma que um nó de `Send` vai precisar (função que devolve `{"analises": [...], "falhas": [...]}`, o delta de estado), mas conectar isso a `StateGraph`, `add_node`, `retry_policy` e `error_handler` é a Story 1.6. Nenhum import de `langgraph` aqui.

**Não repete chamada por falha de transporte.** Se `generate_content` levantar por erro de rede/limite de taxa, deixe propagar — `retry_policy` no `add_node` da Story 1.6 é quem trata isso (AD-9). Não escrever `try/except` genérico em volta da chamada de rede nesta story; o único `if` que existe aqui é sobre `resposta.parsed`, que é falha de **conteúdo**, não de infraestrutura.

**Não decide pontuação nem filtra produto genérico.** `pontuacao.py` (Story 2.1) e `agregacao.py` (Story 2.2) são donos dessas decisões — `analise.py` só repassa `produto` como veio (AC7).

### Contrato de entrada e saída de `_montar_delta`

```python
def _montar_delta(
    lote: list[Reclamacao],
    analises_modelo: list[_AnaliseResposta] | None,
) -> dict:
    ...  # {"analises": list[Analise], "falhas": list[Falha]}
```

Devolve um `dict` simples (não `Estado` inteiro) — é o delta que o nó do grafo (Story 1.6) vai mesclar via os redutores `add` de `analises`/`falhas`. Mesmo padrão de retorno que os nós de LangGraph esperam: um dicionário só com as chaves que aquele nó escreve.

### Padrão de chamada ao modelo — já provado em `classificador.py`

`classificador.py:80-92` (`analisa_lote`) já demonstra o padrão inteiro: `genai.Client()`, `cliente.models.generate_content(model=..., contents=json.dumps(...), config=types.GenerateContentConfig(system_instruction=..., response_mime_type="application/json", response_schema=Lote, temperature=0))`, e `resposta.parsed`. **Reaproveitar a forma da chamada**, não o schema (o de `classificador.py` é o antigo, por booleano — `dinheiro_retido: bool` — que a spine já substituiu pelo par `codigo`/`citacao`, ver AD-1). Não copiar `classificador.py` inteiro; só a mecânica de `generate_content`.
[Source: classificador.py:28-39,80-92]

### Estrutura de arquivos

```text
plataforma/
  analise.py            # NOVO — analisar_lote(lote) -> dict; _montar_delta pura
tests/
  test_analise.py         # NOVO
pyproject.toml             # UPDATE — pydantic como dependência direta
```

**Não criar nesta story:** `pontuacao.py`, `agregacao.py`, `relatorio.py`, `grafo.py`, `main.py`, `templates/`.

**Não tocar:** `plataforma/ingestao.py`, `plataforma/config.py`, `plataforma/evidencia.py` (só importar, não modificar), `docs/reclamacoes_reclameaqui.csv`, `baseline.py`, `classificador.py`.

### Bibliotecas e versões

| Item | Versão | Nesta story |
|---|---|---|
| `google-genai` | `>=2.17.0`, já declarado | sim — primeiro módulo que o importa de fato |
| `pydantic` | `2.13.4` instalado, transitivo | **declarar como direta** (Task 0) |
| `langgraph` | `1.2.10` | não — ainda ausente do `pyproject.toml`, Story 1.6 instala |

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-1** | `Sinal` só existe como par `codigo`+`citacao`; `valida` nunca vem do modelo, é sempre recalculado por `evidencia.verificar` |
| **AD-7** | Só `analise.py` importa `google.genai`; cliente construído dentro de `analisar_lote` |
| **AD-16** | `_montar_payload` só emite `id`/`texto` |
| **AD-18** | `_montar_instrucao` lê de `catalogo.CATALOGO`, nenhum código de sinal como literal em `analise.py` |
| **AD-21** | `produto` passa sem julgamento de genérico |
| **NFR-7** | Casamento por id — faltante vira `Falha`, repetido/inventado é descartado |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5] — ACs originais
- [Source: ARCHITECTURE-SPINE.md#AD-1, AD-7, AD-9, AD-16, AD-18, AD-21] — invariantes centrais
- [Source: classificador.py] — padrão de chamada ao modelo já provado neste repositório
- [Source: catalogo.py] — fonte única dos códigos e definições para o prompt
- [Source: plataforma/evidencia.py] — `verificar(sinais, texto)`, integrado aqui por `_montar_delta`
- [Source: .venv/Lib/site-packages/google/genai/types.py:8708-8724] — comportamento real de `response.parsed` quando o schema não casa
- [Source: _bmad-output/specs/spec-plataforma-analise-reclamacoes/state-contract.md, SPEC.md#Resolved] — a origem e o destino dos campos `prazo_prometido_dias`/`data_evento`
- [Source: _bmad-output/project-context.md] — proibição de mock do SDK; regra de declarar `pydantic` como direta

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (bmad-dev-auto) — implementado diretamente pelo agente principal após um subagent de implementação atingir o limite de sessão durante a leitura de contexto (nenhum código daquela tentativa foi produzido nem reaproveitado).

### Debug Log References

- `uv run pytest -q` → `92 passed` (baseline pré-story: 84; +8 novos, todos em `tests/test_analise.py`).
- `uv run python -c "import plataforma.analise"` sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` → `ok`, sem erro.
- Confirmado por leitura: nenhum teste chama `generate_content` nem constrói `genai.Client()`.

### Completion Notes List

- `analisar_lote` (impura, fina) e `_montar_delta` (pura) separadas exatamente como as Dev Notes mandaram — sem isso, AC3/AC4/AC5 não seriam testáveis sob a proibição de mock do SDK.
- Detecção de "schema não casou" via `resposta.parsed is None`, confirmado contra `google/genai/types.py:8708-8724` do SDK instalado (não documentação pública).
- `prazo_prometido_dias`/`data_evento` sempre `None`, conforme decisão registrada — nenhuma AC de nenhuma story pede que o modelo os preencha.
- Id inventado e id repetido são descartados sem gerar `Falha`; só id do lote sem correspondência vira `Falha`.
- Ordem de `Falha.ids` segue a ordem do `lote`, não a de um `set`, por determinismo (NFR-8) — pequeno ajuste feito durante a implementação, não estava explícito letra por letra no spec.
- `pydantic>=2.13` declarado em `pyproject.toml` como dependência direta.
- **Correção de revisão (achado de alta severidade):** a primeira versão hardcodeava `MODELO = "gemini-3.6-flash"` como constante de módulo, ignorando `plataforma.config` — a Story 1.2 inteira ficaria sem efeito sobre a única chamada paga do pipeline. Corrigido para `config.carregar().modelo`, chamado dentro de `analisar_lote`, no mesmo escopo que constrói `genai.Client()`. Ver Spec Change Log do spec-1-5 para o registro completo.
- Revisão (Blind Hunter + Edge Case Hunter): `95 passed` pós-revisão. Três testes acrescentados: verificação package-wide de AD-7 (`test_somente_analise_importa_o_sdk_do_modelo`), guarda contra lote vazio disparando chamada paga, cobertura de `_montar_instrucao`.

### File List

| Arquivo | Tipo |
|---|---|
| `plataforma/analise.py` | novo |
| `tests/test_analise.py` | novo |
| `pyproject.toml` | modificado |
