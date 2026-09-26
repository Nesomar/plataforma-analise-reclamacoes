---
title: 'Story 1.2 — Configuração validada antes de qualquer chamada paga'
type: 'feature'
created: '2026-08-07'
status: 'done'
baseline_revision: 'd11316a'
final_revision: '97348a9'
review_loop_iteration: 0
followup_review_recommended: true
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/1-2-configuracao-validada-antes-de-qualquer-chamada-paga.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
warnings: ['oversized']
---

<intent-contract>

## Intent

**Problem:** Tamanho de lote e modelo estão fixos em código. Nada impede configurar um lote fora da faixa 2–25 que AD-17 exige, e a validação precisa encerrar antes de qualquer chamada paga. O `README.md` ainda exporta `GEMINI_API_KEY`, nome não-canônico para o SDK.

**Approach:** Criar `plataforma/config.py` — módulo folha com defaults de módulo e uma função `carregar()` que popula o ambiente via `load_dotenv()`, lê `TAMANHO_LOTE` e `MODELO`, valida tipo e faixa, e devolve uma config congelada. Atualizar `.env.example`, `README.md` e a whitelist de imports da Story 1.1.

## Boundaries & Constraints

**Always:**
- Tudo em português: módulo, constante, função, docstring, mensagem de erro.
- `config.py` não importa nada de `plataforma/` e não importa `google.genai` — imports permitidos: `os`, `dotenv`, mais o que a estrutura congelada exigir (`typing` para `NamedTuple`).
- `load_dotenv()` e toda validação vivem **dentro** de `carregar()`. Escopo de módulo é inerte.
- `ValueError` nomeia a variável, o valor observado e a faixa `2` a `25`. Nunca deixar vazar `ValueError` cru do `int()`.
- `None`, `""` e só-espaços são tratados igual: variável não definida → default.
- Config devolvida é imutável (`NamedTuple` ou `dataclass(frozen=True)`), no padrão de congelamento de `catalogo.py`.
- Comentário explica o porquê e cita a fonte (`AD-17`, `NFR-1`, `classificador.py:23`).

**Block If:**
- Alguma AC exigir importar `google.genai`, instalar dependência nova ou tocar `pyproject.toml`.
- A suíte existente falhar por motivo não previsto na Task 4.

**Never:**
- Não ler, retornar ou armazenar a chave de API em lugar nenhum — quem lê é o SDK, do ambiente, dentro de `analisar_lote` (AD-7).
- Não expor concorrência: `max_concurrency` é inerte no v1 síncrono (AD-9).
- Não validar o valor de `MODELO` contra allowlist — congelaria um catálogo que envelhece.
- Não fundir lote residual de tamanho 1 — é `ingestao.py`, Story 1.3.
- Não usar `sys.exit` nem levantar em escopo de módulo.
- Não tocar `baseline.py`, `classificador.py` (inclusive a linha morta `:125`) nem `docs/`.
- Não criar `ingestao.py`, `analise.py`, `grafo.py`, `main.py` ou qualquer outro módulo.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Default | Nenhuma variável definida | `tamanho_lote=10`, `modelo="gemini-3.6-flash"` | Nenhum erro esperado |
| Valor válido | `TAMANHO_LOTE=10` | `tamanho_lote=10` | Nenhum erro esperado |
| Limites inclusivos | `TAMANHO_LOTE=2` / `=25` | Aceitos como estão | Nenhum erro esperado |
| Presente e vazio | `TAMANHO_LOTE=` / `MODELO=` / só-espaços | Default adotado, execução segue | Nenhum erro esperado |
| Fora da faixa | `TAMANHO_LOTE=1` / `=26` / `=-3` | — | `ValueError` nomeando variável, valor observado e faixa 2–25 |
| Não-inteiro | `TAMANHO_LOTE=abc` / `=7.5` | — | `ValueError` nomeando variável e valor; não o `ValueError` cru do `int()` |
| Modelo custom | `MODELO=outro-modelo` | `modelo="outro-modelo"`, sem validação | Nenhum erro esperado |
| Ambiente vence `.env` | Variável real definida e `.env` com outro valor | Vence a variável real (`override=False`) | Nenhum erro esperado |
| Import sob config inválida | `TAMANHO_LOTE=99`, `import plataforma.config` | Import conclui sem exceção | Nenhum erro esperado |

</intent-contract>

## Code Map

- `plataforma/config.py` — **NOVO**. Defaults, `carregar()`, validação de faixa e tipo.
- `plataforma/catalogo.py` — padrão a seguir: docstring de módulo, congelamento, `# ponytail:`.
- `tests/test_contrato.py:125-133` — `parametrize` da whitelist de imports; `config` precisa entrar ou o teste reprova assim que o módulo nascer.
- `tests/test_contrato.py:51-71` — `importados_por()`, inspeção por AST reutilizada pela whitelist.
- `tests/test_import_sem_credencial.py:6` — `MODULOS`; padrão de `monkeypatch.delenv`/`delitem`.
- `tests/test_config.py` — **NOVO**.
- `.env.example` — 3 linhas, **CRLF**, só nomes sem valores.
- `README.md:25` — `export GEMINI_API_KEY=...` a corrigir.
- `.venv/Lib/site-packages/dotenv/main.py` — `find_dotenv()` sobe a partir do arquivo que chama, **não** do cwd.

## Tasks & Acceptance

**Execution:**

- [x] `plataforma/config.py` — criar módulo com `TAMANHO_LOTE_PADRAO = 10`, `MODELO_PADRAO = "gemini-3.6-flash"`, `FAIXA_LOTE = (2, 25)` e `carregar() -> Config` — é o mecanismo único de configuração. Comentar: o pino do modelo (alias móvel invalida comparação de F1, padrão de `classificador.py:23`), o `10` como premissa de NFR-1 e não número medido, o `override=False` (ambiente real vence `.env`), e que a fusão do lote residual é de `ingestao.py`/Story 1.3.
- [x] `.env.example` — acrescentar `TAMANHO_LOTE=` e `MODELO=`, sem valor, cada um precedido de comentário com default e faixa (o valor não pode aparecer, por NFR-10). Escrever em **CRLF**: o arquivo é CRLF hoje e linha em LF cria terminação mista.
- [x] `README.md` — trocar `GEMINI_API_KEY` por `GOOGLE_API_KEY` na linha 25 e documentar `TAMANHO_LOTE` e `MODELO` com default e faixa.
- [x] `tests/test_contrato.py` — importar `config` e acrescentar `(config, {"os", "dotenv", "typing"})` ao `parametrize` de `test_modulos_folha_so_importam_o_que_a_story_permite`; ajustar a docstring, que hoje diz "nenhum de terceiro" e fica falsa com `dotenv`. A regra real é whitelist explícita por módulo. Ajustar o conjunto permitido ao que o módulo de fato importar.
- [x] `tests/test_config.py` — cobrir toda a I/O Matrix com `monkeypatch.setenv`/`delenv`. **Neutralizar o `.env` real** com fixture `autouse` que troca `config.load_dotenv` por no-op: `find_dotenv()` sobe a partir de `plataforma/config.py` até a raiz do projeto, então `monkeypatch.chdir(tmp_path)` **não** resolve. Escrever `2` e `25` à mão, sem importar `FAIXA_LOTE` — fonte duplicada deliberada, no padrão de `CAMPOS_ESPERADOS` (`tests/test_contrato.py:22-23`). Asserção sempre com mensagem prefixada pela AC e nomeando o valor observado.
- [x] `tests/test_import_sem_credencial.py` — acrescentar `"plataforma.config"` a `MODULOS`, para que AD-7 e AD-12 cubram o módulo novo.

**Acceptance Criteria:**

- Given `TAMANHO_LOTE=10` no ambiente, when `carregar()` roda, then `tamanho_lote` vale `10` sem que nenhuma constante do código tenha mudado (NFR-2).
- Given o módulo `plataforma/config.py` inspecionado, when se procura por leitura de credencial, then não há leitura, retorno nem armazenamento de `GOOGLE_API_KEY` ou `GEMINI_API_KEY` — só `load_dotenv()` populando o ambiente (NFR-10, AD-7).
- Given `.env.example`, when lido, then lista `GOOGLE_API_KEY`, `TAMANHO_LOTE` e `MODELO`, todos sem valor à direita do `=`, e o arquivo permanece integralmente em CRLF.
- Given `README.md`, when lido, then exporta `GOOGLE_API_KEY` e documenta `TAMANHO_LOTE` e `MODELO` com default e faixa.
- Given a suíte rodando sem `GOOGLE_API_KEY` e sem `GEMINI_API_KEY`, when `uv run pytest` roda, then tudo passa e nenhum módulo `google*` entra em `sys.modules` por causa de `plataforma.config` (AD-7, AD-12).
- Given `TAMANHO_LOTE=99` no ambiente, when `plataforma.config` é importado, then o import conclui sem exceção — validação nenhuma acontece em escopo de módulo (AC7 da story, AD-12).
- Given o objeto devolvido por `carregar()`, when se tenta atribuir a um campo, then a atribuição falha — a config é congelada.

## Spec Change Log

## Review Triage Log

### 2026-08-07 — Review pass

- intent_gap: 0
- bad_spec: 0
- patch: 12: (high 0, medium 4, low 8)
- defer: 1: (high 0, medium 0, low 1)
- reject: 6
- addressed_findings:
  - `[low]` `[patch]` `TAMANHO_LOTE` com mais de 4300 dígitos passava em `isdecimal()` e fazia `int()` levantar o `ValueError` cru que AC5 proíbe — comprimento conferido antes da conversão.
  - `[low]` `[patch]` Dígitos decimais não-ASCII (`١٠`) viravam `10` silenciosamente — `isascii()` somado a `isdecimal()`.
  - `[low]` `[patch]` `+10` era rejeitado, apesar de `int()` aceitá-lo — `removeprefix("+")` acrescentado.
  - `[low]` `[patch]` Mensagem única fundia tipo e faixa: `-3` recebia "informe um número inteiro", diagnóstico errado no caso mais provável — duas mensagens.
  - `[medium]` `[patch]` `test_valor_do_ambiente_e_adotado` usava `TAMANHO_LOTE=10`, igual ao default: não podia falhar. Trocado para `15`.
  - `[medium]` `[patch]` Nenhum teste apagava `TAMANHO_LOTE`/`MODELO` do ambiente real, e o README manda o operador fazer `export` — a suíte passaria ou falharia conforme a máquina. `delenv` na fixture `autouse`.
  - `[medium]` `[patch]` AC6/NFR-10 era o critério mais sensível e o único sem teste; a whitelist permite `os`, então uma leitura de credencial entraria sem reprovar nada. Criado `test_config_nunca_toca_na_credencial`.
  - `[medium]` `[patch]` Story `1-2-*.md` continuava `ready-for-dev`, com caixas desmarcadas e `Dev Agent Record` vazio; as duas perguntas abertas seguiam sem resposta registrada. Story fechada, decisões registradas, `sprint-status.yaml` atualizado.
  - `[low]` `[patch]` `test_ambiente_real_vence_o_env` só inspecionava `kwargs`; `override` é o quarto posicional de `load_dotenv` e escaparia. Passou a olhar os dois.
  - `[low]` `[patch]` Asserção morta depois do `pytest.raises` e `monkeypatch` recebido sem uso em três testes — removidos.
  - `[low]` `[patch]` `strip()` sobre valor real (`" 15 "`) não era testado: só o caso vazio quebraria se ele sumisse. Caso acrescentado.
  - `[low]` `[patch]` `README.md` prometia "encerra antes de qualquer chamada paga" sem registrar que nome de modelo inexistente só falha na primeira chamada. Ressalva acrescentada onde o operador lê.

## Design Notes

**Por que `ValueError` e não `sys.exit`:** o import de `config` precisa funcionar sob configuração inválida, senão a própria inspeção de imports que esta story pede fica impossível. O `main.py` de uma story futura traduz a exceção em saída de processo.

**A armadilha do `.env` na suíte:** `load_dotenv()` sem argumento chama `find_dotenv()`, que anda para cima **a partir do diretório do arquivo que chamou** (`plataforma/`), achando a raiz do projeto. Um `.env` real na máquina de quem roda a suíte quebraria o caso de default — e só na máquina dele. Trocar `config.load_dotenv` por no-op numa fixture `autouse` é a única neutralização que funciona.

**A divergência `GEMINI_API_KEY`/`GOOGLE_API_KEY` não é bug de código.** `google-genai 2.17.0` lê as duas em `_api_client.py:101-117`, com precedência de `GOOGLE_API_KEY` e fallback automático. `classificador.py:125` é código morto que reimplementa isso à mão. A dívida é só documental: corrigir o README e nada mais.

## Verification

**Commands:**
- `uv run pytest` — expected: toda a suíte verde, incluindo os testes novos de `test_config.py` e a whitelist estendida.
- `uv run python -c "import plataforma.config, sys; assert not [m for m in sys.modules if m.startswith('google')]"` — expected: sem saída e sem erro; nenhum módulo do SDK arrastado.

**Manual checks (if no CLI):**
- `git diff .env.example` mostrando as linhas novas com `^M` preservado (terminação CRLF uniforme).

## Auto Run Result

Status: done

**Mudança implementada.** `plataforma/config.py` passa a ser a fonte única de tamanho de
lote e modelo: defaults no código, sobrescrita por variável de ambiente ou `.env`, e faixa
de 2 a 25 validada dentro de `carregar()` — nunca em escopo de módulo, para que o import
continue inerte sob configuração inválida. A credencial não passa pelo módulo:
`load_dotenv()` popula o ambiente e o SDK a lê sozinho, dentro de `analisar_lote`.

**Arquivos.**

| Arquivo | O quê |
|---|---|
| `plataforma/config.py` | NOVO — defaults, `Config(NamedTuple)` congelada, `carregar()` com validação de tipo e faixa |
| `tests/test_config.py` | NOVO — 26 testes cobrindo a I/O Matrix, mais a varredura de credencial |
| `tests/test_contrato.py` | `config` na whitelist de imports (`os`, `typing`, `dotenv`); docstring reescrita — a regra é whitelist por módulo, não "nenhum de terceiro" |
| `tests/test_import_sem_credencial.py` | `plataforma.config` em `MODULOS`; teste renomeado, que agora cobre três módulos |
| `.env.example` | `TAMANHO_LOTE=` e `MODELO=` sem valor, com default e faixa em comentário; CRLF preservado |
| `README.md` | `GOOGLE_API_KEY` no lugar de `GEMINI_API_KEY`; seção "Configuração" com a ressalva sobre modelo não validado |

**Achados da revisão.** 12 patches aplicados (4 medium, 8 low), 1 deferido, 6 rejeitados.
Nenhum intent gap, nenhum defeito de spec. Os quatro medium eram testes que não podiam
falhar ou que dependiam do ambiente da máquina, e a ausência de teste para AC6.

**Verificação.**

- `uv run pytest` — 64 passed (38 antes desta story).
- `uv run python -c "import plataforma.config, sys; assert not [m for m in sys.modules if m.startswith('google')]"` — sem saída, sem erro.
- `.env.example` conferido byte a byte: CRLF uniforme, nenhum valor à direita de `=`.

**Riscos residuais.**

- `carregar()` ainda não tem consumidor. `classificador.py` segue com as constantes
  fixas, e nenhum entrypoint traduz o `ValueError` em saída de processo — é da Story 1.7.
  AC4 está provada no nível de biblioteca, não no caminho real do operador.
- Nome de modelo inexistente só falha na primeira chamada paga. Fechar isso exigiria
  consultar a API, que AD-7 proíbe daqui. Documentado no README e na docstring.
- A faixa `2..25` aparece em `FAIXA_LOTE`, no `.env.example` e no `README.md`. A
  duplicação nos testes é deliberada e comentada; a da documentação não tem amarra.
