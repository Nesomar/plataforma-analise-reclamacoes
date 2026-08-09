---
title: 'Story 2.1 — Pontuação que carrega o motivo de cada item da fila'
type: 'feature'
created: '2026-08-08'
status: 'done'
baseline_revision: 'e28b142'
final_revision: '9020d74'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/2-1-pontuacao-que-carrega-o-motivo-de-cada-item-da-fila.md'
warnings: []
---

<intent-contract>

## Intent

**Problem:** `Analise` tem sinais verificados, mas nada converte isso em pontuação nem decide o que entra na fila — e nada carrega o motivo (citação ou atributo estrutural) que sustenta cada decisão.

**Approach:** Criar `plataforma/pontuacao.py` com `pontuar(estado) -> {"pontuacoes": [...]}`: soma pesos por código válido (grupo A satura em 3), aplica modificador −1 se `Status=="Respondida"`, corta em 3 pontos. Cada `Sinal` válido vira um `Motivo` de origem `sinal`; o modificador de `Status` sempre vira um `Motivo` de origem `atributo`. Religar `grafo.py`: `_verificar_conservacao -> pontuar -> END`.

## Boundaries & Constraints

**Always:**
- Tudo em português: módulo, função, comentário.
- Pesos num único `MappingProxyType`, código do catálogo como chave (AD-18).
- Saturação do grupo A lida de `catalogo.GRUPO_SINAL_A`, nunca reimplementada.
- Pontuação por **código distinto válido**, não por instância de `Sinal` nem por par.
- Um `Motivo` por `Sinal` válido (não deduplicado por código); um `Motivo` sempre que o modificador de `Status` é aplicado.
- `pontuar` é o único nó que escreve `pontuacoes`, incluindo `na_fila` (AD-19).

**Block If:**
- Alguma AC exigir `agregar`, `relatorio` ou qualquer nó de story posterior — fora de escopo.
- A suíte existente falhar por motivo não previsto.

**Never:**
- Não inventar peso positivo para "categoria" — não existe na tabela ratificada de `risk-signals.md` nem no contrato de `Reclamacao`. AC6 (`Motivo` de origem `atributo`) é satisfeita estruturalmente pelo modificador de `Status`, não por um cenário onde o item entra na fila só por atributo (matematicamente impossível com a tabela atual — modificador é sempre negativo).
- Não tocar `plataforma/ingestao.py`, `plataforma/config.py`, `plataforma/evidencia.py`, `plataforma/analise.py`, `docs/`, `baseline.py`, `classificador.py`.
- Não importar `google.genai` nem qualquer módulo que o arraste.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Caso feliz | `dinheiro_retido` válido, `Status≠Respondida` | 3 pontos, `na_fila=True` | — |
| Regra validada (AC4) | `dinheiro_retido` válido + `Status=Respondida` | 2 pontos, `na_fila=False` | — |
| Saturação grupo A | `ameaca_explicita` + `lei_citada` válidos | 3 pontos (não 6), 2 `Motivo` | — |
| Código repetido | 2 `Sinal` válidos, mesmo código, citações diferentes | Peso somado 1×, 2 `Motivo` | — |
| Sinal inválido | `Sinal` com `valida=False` | Não soma pontos | — |
| Modificador isolado | `Status=Respondida` | `Motivo` origem `atributo`, `citacao=None` — sempre, independente de `na_fila` | — |

</intent-contract>

## Code Map

- `plataforma/pontuacao.py` — **NOVO**. `PESOS`, `CORTE`, `MODIFICADOR_STATUS_RESPONDIDA`, `pontuar(estado) -> dict`.
- `plataforma/catalogo.py` — `GRUPO_SINAL_A`, fonte da saturação.
- `plataforma/estado.py` — `Estado`, `Analise`, `Sinal`, `Reclamacao`, `Motivo`, `Pontuacao`.
- `plataforma/grafo.py` — religar aresta final: `_verificar_conservacao -> pontuar -> END`.
- `_bmad-output/specs/spec-plataforma-analise-reclamacoes/risk-signals.md#Pesos do v1` — tabela canônica de pesos.
- `tests/test_pontuacao.py` — **NOVO**.

## Tasks & Acceptance

**Execution:**
- [x] `plataforma/pontuacao.py` — `PESOS`/`CORTE`/`MODIFICADOR_STATUS_RESPONDIDA`; `pontuar(estado) -> {"pontuacoes": [...]}`: por `Analise`, motivos de origem `sinal` (um por `Sinal` válido), pontos por código distinto válido (grupo A saturado via `catalogo.GRUPO_SINAL_A`), modificador de `Status` com `Motivo` de origem `atributo`, `na_fila = pontos >= CORTE`. **Emenda:** `PESOS` deriva de `catalogo.CATALOGO[codigo]["peso"]` em vez de retipar os códigos como literais — a primeira versão caiu em `test_nenhum_outro_modulo_declara_codigo_de_sinal_como_literal` (AD-18); `catalogo.py` ganhou a chave `"peso"` em cada entrada, `tests/test_catalogo.py` atualizado para o novo formato.
- [x] `plataforma/grafo.py` — `add_node("pontuar", pontuacao.pontuar)`; aresta final `_verificar_conservacao -> pontuar -> END`; comentário apontando que Story 2.2 rewire de novo.
- [x] `tests/test_pontuacao.py` — cobrir a I/O Matrix inteira com `Analise`/`Reclamacao` fabricadas à mão; caso das três parcelas não exercidas pela base (AC9); ordem preservada; import sem credencial.

**Acceptance Criteria:**
- Given `dinheiro_retido` válido e `Status≠Respondida`, when `pontuar` roda, then 3 pontos, `na_fila=True`, um `Motivo` origem `sinal` (AC1, AC2, AC5).
- Given `dinheiro_retido` válido e `Status=Respondida`, when `pontuar` roda, then 2 pontos, `na_fila=False` (AC4 — valida a regra medida).
- Given `ameaca_explicita` e `lei_citada` ambos válidos, when `pontuar` roda, then 3 pontos (não 6), lidos de `catalogo.GRUPO_SINAL_A` (AC3).
- Given um código com `Sinal` inválido, when `pontuar` roda, then não soma pontos, mesmo com par válido do mesmo código (AC7, AD-2).
- Given o modificador de `Status=Respondida` aplicado, when `pontuar` roda, then produz `Motivo` origem `atributo`, `citacao=None` (AC6).
- Given o estado após `pontuar`, when inspecionado, then `pontuacoes` tem uma `Pontuacao` por `Analise`, só `pontuar` escreve essa chave (AC8, AD-19).
- Given `Analise` fabricada para `ameaca_explicita`/`dano_continuado`/`registro_contraditorio`, when a suíte roda, then cada uma pontua sem rede (AC9).
- Given `plataforma/pontuacao.py` inspecionado, when procurado por `google.genai`, then não há import (AC10).

## Spec Change Log

### 2026-08-08 — `PESOS` movido para `catalogo.py`, `pontuacao.py` só lê

- **Gatilho:** a primeira implementação declarava `PESOS = {"dinheiro_retido": 3, ...}` direto em `pontuacao.py`, como o `Approach` original descrevia. Rodar a suíte reprovou em `tests/test_catalogo.py::test_nenhum_outro_modulo_declara_codigo_de_sinal_como_literal` — teste pré-existente da Story 1.1, cujo próprio docstring já previa esse caso: "sem esta varredura o AC seguiria verde no dia em que `pontuacao.py` nascesse com a string repetida — que é o defeito que ela existe para pegar."
- **O que foi emendado:** `Code Map`/`Tasks` (fora do `<intent-contract>`, sem tocar Intent/Boundaries). `catalogo._CATALOGO` ganhou a chave `"peso"` em cada uma das seis entradas; `pontuacao.PESOS` passou a ser `{codigo: dados["peso"] for codigo, dados in catalogo.CATALOGO.items()}` — nenhum nome de código escrito em `pontuacao.py`. `tests/test_catalogo.py::test_cada_codigo_tem_definicao_e_exemplo_escritos` renomeado e estendido para exigir também `"peso"` (inteiro positivo).
- **Estado ruim evitado:** um `PESOS` com os seis nomes retipados em `pontuacao.py` é exatamente a duplicação que AD-18 proíbe — dois lugares para o mesmo código divergirem se um dia alguém corrigir a grafia ou adicionar um sétimo código só em um dos dois.
- **KEEP:** a lógica de `pontuar()` (agrupamento por código, saturação via `GRUPO_SINAL_A`, modificador de `Status`, `Motivo` por instância de `Sinal`) não mudou — só de onde `PESOS` vem.

## Review Triage Log

### 2026-08-08 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 7: (high 0, medium 2, low 5)
- defer: 0
- reject: 6: (high 0, medium 0, low 6)
- addressed_findings:
  - `[medium]` `[patch]` Saturação do grupo A dependia da ordem em que os códigos apareciam em `analise["sinais"]` ("primeiro que eu vi ganha"), só estável porque `ameaca_explicita` e `lei_citada` têm o mesmo peso hoje — se um dia divergirem, o resultado passaria a depender de qual o modelo citou primeiro, sem teste para pegar. Corrigido: soma o **maior** peso entre os códigos do grupo presentes, não o primeiro.
  - `[medium]` `[patch]` Acesso a `PESOS` inconsistente: `PESOS[codigo]` no grupo A (levanta `KeyError` para código desconhecido) vs `PESOS.get(codigo, 0)` fora dele (silencia). Unificado para `.get(..., 0)` nos dois — um código alucinado pelo modelo não deveria derrubar a execução inteira.
  - `[low]` `[patch]` Rótulo do `Motivo` do modificador tinha `"(−1)"` como string solta, independente da constante `MODIFICADOR_STATUS_RESPONDIDA` — mudar a constante mentiria sobre quantos pontos saíram. Corrigido para interpolar a constante.
  - `[low]` `[patch]` `peso` só testado com `isinstance(x, int)`, que aceita `bool` (subclasse de `int` em Python) — trocado para `type(x) is int`.
  - `[low]` `[patch]` Caminho de um código só do grupo A (sem o par) só era exercitado como subconjunto do teste de dois códigos — teste isolado acrescentado.
  - `[low]` `[patch]` Nenhum teste cobria o caso base (zero sinais, `Status` ≠ Respondida → 0 pontos, fora da fila) — acrescentado.
  - `[low]` `[patch]` Só 2 dos 5 valores do `Literal` de `Status` eram exercitados — acrescentado teste cobrindo os outros quatro, confirmando que só "Respondida" aciona o modificador.
- **Rejeitados, com motivo:** `reclamacoes_por_id[analise["id"]]` sem guarda (protegido pelo casamento por id da Story 1.5 — todo `Analise.id` vem de um `Reclamacao` do mesmo lote); id de `Reclamacao` duplicado sobrescrevendo em silêncio (protegido pela unicidade validada em `ingestao.py`, Story 1.3); id de `Analise` duplicado gerando duas `Pontuacao` (protegido por NFR-4 — cada reclamação é despachada uma vez só); pontos podendo ficar negativos sem *clamp* (não quebra `na_fila`, decisão de apresentação fica para o relatório, Épico 2); campo `"falhas": []` inerte no fixture de teste (cosmético, mantém o formato de `Estado`); AC10 "não testado" — na verdade já coberto pela varredura genérica existente em `test_analise.py`, que faz `glob("*.py")` sobre `plataforma/` e por isso já inclui `pontuacao.py` automaticamente.

## Design Notes

**AC6 é estruturalmente satisfeita, não pela fila.** A tabela ratificada de `risk-signals.md` só tem um atributo — `Status=Respondida`, peso −1, modificador puro. Nenhuma combinação de atributos cruza o corte de 3 sozinha. O `Motivo` de origem `atributo` é produzido sempre que o modificador é aplicado, testado isoladamente da decisão de `na_fila` — não forçado um cenário matematicamente impossível com os pesos atuais.

**Duas granularidades:** pontuação por código distinto (evita dobrar pontos por citação repetida), `Motivo` por instância de `Sinal` (preserva toda citação como evidência visível, FR-12).

## Verification

**Commands:**
- `uv run pytest` — expected: suíte inteira verde, incluindo `test_pontuacao.py` novo (baseline 124 testes).
- `uv run python -c "import plataforma.pontuacao"` sem `GOOGLE_API_KEY`/`GEMINI_API_KEY` — expected: sem erro.

**Manual checks (if no CLI):**
- Ler `plataforma/pontuacao.py` e confirmar que nenhum código de sinal aparece como string solta fora de `PESOS`.

## Auto Run Result

**O que foi implementado:** `plataforma/pontuacao.py` com `pontuar(estado) -> {"pontuacoes": [...]}`. `plataforma/grafo.py` religado: `_verificar_conservacao -> pontuar -> END`. **Emenda:** `catalogo.py` ganhou a chave `"peso"` em cada uma das seis entradas — `pontuacao.PESOS` deriva daí em vez de retipar os códigos como literais, corrigindo uma quebra real em `test_catalogo.py::test_nenhum_outro_modulo_declara_codigo_de_sinal_como_literal` (AD-18) que a primeira versão causou.

**Arquivos tocados:**

| Arquivo | Tipo | Descrição |
|---|---|---|
| `plataforma/pontuacao.py` | novo | `PESOS`, `CORTE`, `MODIFICADOR_STATUS_RESPONDIDA`, `pontuar` |
| `plataforma/catalogo.py` | modificado | `"peso"` em cada entrada de `_CATALOGO`; docstring atualizada |
| `plataforma/grafo.py` | modificado | aresta final religada para `pontuar` |
| `tests/test_pontuacao.py` | novo | 13 testes |
| `tests/test_catalogo.py` | modificado | teste de estrutura estendido para `"peso"` |

**Verificação (pós-revisão):**
- `uv run pytest -q` → `134 passed` pós-implementação → `137 passed` pós-revisão (baseline: 124).
- `uv run python -c "from plataforma import pontuacao; print(dict(pontuacao.PESOS))"` → pesos batem exatamente com a tabela ratificada de `risk-signals.md`.

**Achados da revisão.** Blind Hunter + Edge Case Hunter em paralelo. 13 achados únicos: 7 patches (2 medium — saturação do grupo A dependente de ordem em vez de valor, achado real e não-óbvio; acesso inconsistente a `PESOS` entre os dois branches; 5 low — rótulo hardcoded, `bool` passando como `int`, cobertura de teste em três pontos), 6 rejeitados, todos protegidos por invariantes já estabelecidos em stories anteriores (casamento por id da 1.5, unicidade de id da 1.3, NFR-4) ou fora de escopo (apresentação de pontos negativos é do relatório, Épico 2).

**Riscos residuais / decisões por ausência de fonte:**
- AC6 (`Motivo` de origem `atributo`) permanece estruturalmente correta mas não alcançável isoladamente com a tabela de pesos atual — decisão já registrada na story, reconfirmada.
- Nenhum outro desvio do spec além do já registrado no Spec Change Log (`PESOS` movido para `catalogo.py`).
