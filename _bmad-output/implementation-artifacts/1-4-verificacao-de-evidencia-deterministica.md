# Story 1.4: Verificação de evidência determinística

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a gestor que vai agir sobre a fila,
I want que toda citação seja conferida contra o texto original por comparação de string,
so that nenhum sinal sobreviva sustentado por uma frase que o modelo inventou.

## Acceptance Criteria

**AC1 — Citação válida (substring exata, ≥5 palavras) passa**

**Given** um `Sinal` cuja `citacao` é substring exata do texto da reclamação e tem cinco palavras ou mais
**When** a verificação roda
**Then** aquele `Sinal` fica com `valida = True`

**AC2 — Citação inválida derruba o código inteiro, inclusive os pares que passaram (AD-2)**

**Given** um `Sinal` cuja `citacao` não é substring do texto original
**When** a verificação roda
**Then** todo `Sinal` daquele mesmo `codigo` fica com `valida = False`, inclusive os pares do mesmo código cuja citação passou

**AC3 — Piso de cinco palavras verificado no mesmo lugar que a substring (FR-6, AD-1)**

**Given** um `Sinal` com citação de quatro palavras que é substring válida do texto
**When** a verificação roda
**Then** aquele `Sinal` fica com `valida = False`

**AC4 — Citação vazia reprova apesar de ser substring trivial**

**Given** um `Sinal` com `citacao` igual a string vazia
**When** a verificação roda
**Then** fica com `valida = False`, apesar de string vazia ser substring de qualquer texto

**AC5 — Citação falsa injetada é pega pela suíte, sem rede (AD-12, CM-2)**

**Given** uma `Analise` fabricada à mão com citação falsa injetada de propósito
**When** a suíte de testes roda
**Then** a verificação derruba o código correspondente
**And** nenhuma chamada de rede é feita durante o teste

**AC6 — Sem SDK do modelo nos imports (AD-7)**

**Given** o módulo `plataforma/evidencia.py`
**When** seus imports são inspecionados
**Then** ele não importa `google.genai`, direta nem transitivamente

## Tasks / Subtasks

- [x] **Task 1 — Criar `plataforma/evidencia.py`** (AC: 1, 2, 3, 4, 6)
  - [x] Escrever `verificar(sinais: list[Sinal], texto: str) -> list[Sinal]` — função pura, devolve uma **nova** lista (não muta os `Sinal` recebidos), no espírito "cada etapa é função do estado para um delta"
  - [x] Checagem individual por `Sinal`: `citacao` é substring exata de `texto` (`in`) **e** `len(citacao.split()) >= 5` — as duas condições no mesmo lugar, nunca uma só no prompt (AD-1, FR-6). String vazia falha sozinha pelo piso de palavras, sem precisar de caso especial (`len("".split()) == 0`)
  - [x] **Agrupar por `codigo` antes de decidir `valida` (AD-2) — este é o núcleo da story, não pule.** Um `codigo` pode aparecer em mais de um `Sinal` da mesma `Analise` (citações diferentes sustentando o mesmo risco). Calcular a checagem individual de cada `Sinal` primeiro; depois, para cada `codigo`, `valida` final de **todos** os `Sinal` daquele código é `True` só se **todas** as citações daquele código passaram na checagem individual. Uma checagem por `Sinal` isolado, sem o agrupamento, implementa AC1/AC3/AC4 mas **quebra AC2** — o caso que a story existe para cobrir
  - [x] Devolver `Sinal`s na mesma ordem de entrada, só com `valida` recalculado (demais campos, `codigo` e `citacao`, inalterados)
  - [x] Docstring de módulo no padrão de `config.py`/`ingestao.py`: propósito em uma linha, parágrafo com o porquê do agrupamento por código (AD-2) ser a parte não-óbvia
  - [x] Comentário no agrupamento cita `AD-2` e explica por que um `Sinal` individualmente válido pode sair com `valida = False`

- [x] **Task 2 — Criar `tests/test_evidencia.py`** (AC: 1, 2, 3, 4, 5, 6)
  - [x] Caso feliz: uma citação real (substring, ≥5 palavras) → `valida = True`
  - [x] Citação fabricada (não substring) → `valida = False`
  - [x] **AD-2 é o teste mais importante desta story:** dois `Sinal` do **mesmo** `codigo`, um com citação válida e outro com citação inventada → **os dois** saem com `valida = False`, inclusive o que individualmente teria passado
  - [x] Citação de 4 palavras, substring válida → `valida = False` (prova que o piso de palavras não é bypassável só por ser substring)
  - [x] Citação de exatamente 5 palavras, substring válida → `valida = True` (limite inclusivo)
  - [x] Citação vazia (`""`) → `valida = False`, com comentário explicando que passaria no `in` sozinho
  - [x] Caso com `Analise` fabricada à mão citando `ameaca_explicita`, `dano_continuado` ou `registro_contraditorio` com citação falsa injetada — prova de CM-2, no padrão que `project-context.md` exige para essas três parcelas (AD-12)
  - [x] Nenhum teste importa `google.genai` nem faz chamada de rede

- [x] **Task 3 — Registrar `plataforma.evidencia` na verificação de AD-7** (AC: 6)
  - [x] Em `tests/test_import_sem_credencial.py`, acrescentar `"plataforma.evidencia"` a `MODULOS`
  - [x] **Não** acrescentar `evidencia` ao `parametrize` de módulos-folha em `tests/test_contrato.py` — mesmo caso de `ingestao` na Story 1.3: `evidencia.py` importa `Sinal` de `plataforma.estado` por desenho (aresta `evidencia --> estado` já desenhada em `ARCHITECTURE-SPINE.md`), e esse teste é só para módulos que não importam nada de `plataforma/`
  - [x] Rodar `uv run pytest` e confirmar verde

## Dev Notes

### O núcleo desta story é o agrupamento por código (AD-2) — não a comparação de substring

A comparação de substring e o piso de 5 palavras são triviais. O que torna esta story não-óbvia é AD-2: **uma citação fabricada derruba o código inteiro**, não só o `Sinal` que carrega a citação ruim. Se o modelo devolver dois `Sinal` com `codigo="dano_continuado"` — um com citação real, outro inventado — **os dois** saem com `valida = False`. A métrica que FR-2 e CM-2 reportam é de **códigos derrubados**, não de pares reprovados nem de reclamações afetadas; as três seriam defensáveis e só uma é a que o sistema mede. Implementar checagem por `Sinal` isolado (sem agrupar por `codigo`) passa em quatro das seis ACs e falha silenciosamente na quinta — o comportamento vai parecer certo até o teste de AD-2 especificamente.
[Source: ARCHITECTURE-SPINE.md#AD-2, epics.md#Story 1.4 AC2]

### Por que `evidencia` não entra no teste de módulos-folha

Mesma decisão já tomada e documentada na Story 1.3 para `ingestao.py`: `tests/test_contrato.py::test_modulos_folha_so_importam_o_que_a_story_permite` é só para módulos que não importam **nada** de `plataforma/` (hoje `estado`, `catalogo`, `config`). `evidencia.py` importa `Sinal` de `plataforma.estado` por desenho — a arquitetura desenha essa aresta explicitamente. AC6 (não importar `google.genai`) é coberta por `test_import_sem_credencial.py`, que não exige lista-branca fechada de terceiros.
[Source: _bmad-output/implementation-artifacts/1-3-ingestao-que-rejeita-base-invalida-antes-de-gastar.md#Por que ingestao.py não entra no teste de módulos-folha]

### O que esta story NÃO faz

**Não integra com `analise.py`.** A spine diz que `analise` importa `evidencia` e roda a verificação sobre a resposta do modelo antes de o delta entrar no estado — mas `analise.py` é a Story 1.5. Esta story entrega só a função pura `verificar()` e a suíte que prova AD-2. Nenhum nó do grafo, nenhum import de `google.genai`, nenhum uso de `Analise` completa (a função trabalha com `list[Sinal]` e `texto: str`, não com o TypedDict `Analise` inteiro — `id`, `sentimento`, `produto` etc. são irrelevantes para a verificação).

**Não decide pontuação nem corte.** `pontuacao.py` (Story 2.1) é quem lê `Sinal.valida` para somar pontos; `evidencia.py` só recalcula esse campo.

### Contrato de entrada e saída

```python
class Sinal(TypedDict):
    codigo: str      # um dos seis de catalogo.py — evidencia.py não valida contra a lista
    citacao: str      # literal, piso de 5 palavras
    valida: bool      # é isto que verificar() recalcula
```

`verificar()` não importa `catalogo.py` — não precisa saber quais códigos existem, só agrupar pelo valor de `codigo` que já está em cada `Sinal`. Isso mantém `evidencia.py` desacoplado do catálogo, coerente com "nenhum filtro importa outro filtro" (a única exceção documentada é `analise` importar `evidencia`, não o inverso).
[Source: plataforma/estado.py, ARCHITECTURE-SPINE.md#Direção de dependência]

### Testando sem rede (AD-12)

Todo teste usa `Sinal`/`Analise` fabricados à mão com `texto` literal escrito no teste — nunca lendo `docs/reclamacoes_reclameaqui.csv` (esta story não lê CSV nenhum) nem chamando o modelo. `evidencia.py` nem importa o SDK, então não haveria como.

### Estrutura de arquivos

```text
plataforma/
  evidencia.py          # NOVO — verificar(sinais, texto) -> list[Sinal]
tests/
  test_evidencia.py      # NOVO
  test_import_sem_credencial.py  # UPDATE — plataforma.evidencia em MODULOS
```

**Não criar nesta story:** `analise.py`, `pontuacao.py`, `agregacao.py`, `relatorio.py`, `grafo.py`, `main.py`, `templates/`.

**Não tocar:** `plataforma/ingestao.py`, `plataforma/config.py`, `docs/reclamacoes_reclameaqui.csv`, `baseline.py`, `classificador.py`.

### Bibliotecas e versões

Nada a instalar. `verificar()` usa só `str.split()` e o operador `in`, ambos stdlib puro. Nenhuma linha nova em `pyproject.toml`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-1** | Piso de 5 palavras verificado no mesmo lugar que a substring, dentro de `verificar()` |
| **AD-2** | Citação inválida derruba todo `Sinal` do mesmo `codigo`, inclusive os que passaram individualmente |
| **AD-7** | `evidencia.py` não importa `google.genai`; verificado por `test_import_sem_credencial.py` |
| **AD-12** | Função pura, testada com `Sinal` fabricado à mão, sem rede |
| **FR-6** | Sinal sem citação, ou com citação abaixo do piso, não fica válido |
| **CM-2** | A suíte prova que a verificação derruba código com citação fabricada — sem esse teste, CM-2 em zero seria indistinguível de mecanismo morto |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4] — ACs originais
- [Source: _bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md#AD-1, AD-2, AD-7, AD-12] — invariantes centrais desta story
- [Source: _bmad-output/implementation-artifacts/epic-1-context.md#Verificação de evidência] — resumo do épico: "substring exata... piso de cinco palavras conferidos no mesmo lugar... citação vazia reprova... uma citação reprovada derruba o código inteiro"
- [Source: plataforma/estado.py] — contrato `Sinal`
- [Source: plataforma/ingestao.py, plataforma/config.py] — padrão de módulo (docstring, comentário cita fonte) das stories 1.2/1.3
- [Source: _bmad-output/implementation-artifacts/1-3-ingestao-que-rejeita-base-invalida-antes-de-gastar.md] — precedente da decisão de não entrar no teste de módulos-folha
- [Source: _bmad-output/project-context.md] — convenções e a exigência de caso construído à mão para `ameaca_explicita`, `dano_continuado`, `registro_contraditorio` e citação falsa

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5), via workflow bmad-dev-auto.

### Debug Log References

- `uv run pytest -q` → `81 passed` (baseline pré-story: 72; +9 novos, todos em `tests/test_evidencia.py`).
- `uv run python -c "import plataforma.evidencia, sys; assert not [m for m in sys.modules if m.startswith('google')]"` → sem saída, exit 0.
- Pós-revisão (Blind Hunter + Edge Case Hunter): `84 passed`. Três testes acrescentados reforçando o núcleo AD-2 (grupo intercalado por outro código, grupo de tamanho 3, lista vazia); dois itens de baixo risco deferidos (guarda contra `Sinal` malformado, contagem de palavra por `.split()`).

### Completion Notes List

- `verificar()` implementada em duas passadas: checagem individual por `Sinal` (substring + piso de 5 palavras), depois redução por `codigo` com `and` acumulado — um código só fica `valida=True` se todas as suas citações passaram individualmente (AD-2). Confirmado pelo teste `test_uma_citacao_fabricada_derruba_o_par_do_mesmo_codigo`: par do mesmo código, um válido e um fabricado, os dois saem `valida=False`.
- Função pura: cada `Sinal` de saída é reconstruído (não é o mesmo objeto de entrada mutado); ordem de saída igual à de entrada — cobertos por testes dedicados.
- `evidencia.py` importa só `plataforma.estado.Sinal`; verificado sem `google.genai` nos módulos carregados por `test_import_sem_credencial.py`.
- `evidencia` **não** foi acrescentado ao `parametrize` de módulos-folha em `test_contrato.py`, conforme instruído (mesma decisão da Story 1.3 para `ingestao`).
- Nenhum desvio do spec; nenhum arquivo fora da lista permitida foi tocado.

### File List

- `plataforma/evidencia.py` (novo)
- `tests/test_evidencia.py` (novo)
- `tests/test_import_sem_credencial.py` (modificado)
