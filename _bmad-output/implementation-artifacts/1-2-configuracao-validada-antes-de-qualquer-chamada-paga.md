# Story 1.2: Configuração validada antes de qualquer chamada paga

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a operador,
I want tamanho de lote e modelo configuráveis por variável de ambiente com faixa validada,
so that eu calibre a execução sem tocar código e sem conseguir configurar uma execução que o SPEC proíbe.

## Acceptance Criteria

**AC1 — Valor de ambiente é adotado sem alteração de código (NFR-2)**

**Given** `TAMANHO_LOTE=10` no ambiente ou no `.env`
**When** `carregar()` é chamada
**Then** `tamanho_lote` vale `10`
**And** nenhuma constante do código precisou mudar

**AC2 — Sem variável definida, os defaults do código valem e a execução segue**

**Given** nenhuma variável de ambiente definida e nenhum `.env`
**When** `carregar()` é chamada
**Then** `tamanho_lote` vale `10` e `modelo` vale `"gemini-3.6-flash"`
**And** nenhuma exceção é levantada

**AC3 — Variável presente e vazia é tratada como não definida**

**Given** `TAMANHO_LOTE=` (presente, sem valor) — o estado exato de quem copiou `.env.example` para `.env`
**When** `carregar()` é chamada
**Then** o default é adotado e a execução segue
**And** o mesmo vale para `MODELO=`

**AC4 — Fora da faixa encerra antes de qualquer chamada paga (AD-17)**

**Given** `TAMANHO_LOTE=1` ou `TAMANHO_LOTE=26`
**When** `carregar()` é chamada
**Then** ela levanta `ValueError` cuja mensagem nomeia **o valor observado** e **a faixa permitida de 2 a 25**
**And** nenhuma chamada ao modelo é feita — `carregar()` não tem como fazer uma, por AC7

**AC5 — Valor não-inteiro cai pela mesma porta**

**Given** `TAMANHO_LOTE=abc` ou `TAMANHO_LOTE=7.5`
**When** `carregar()` é chamada
**Then** ela levanta `ValueError` nomeando o valor observado
**And** a mensagem não é um `ValueError` cru do `int()` — precisa dizer qual variável e qual valor

**AC6 — Credencial só de variável de ambiente, e nunca vira valor Python (NFR-10)**

**Given** o módulo `plataforma/config.py`
**When** ele é inspecionado
**Then** ele chama `load_dotenv()` para popular o ambiente
**And** **não lê, não retorna e não armazena** a chave de API — quem a lê é o SDK, direto do ambiente, dentro de `analisar_lote` (AD-7)
**And** `.env.example` lista `GOOGLE_API_KEY`, `TAMANHO_LOTE` e `MODELO`, todos sem valor
**And** `README.md` exporta `GOOGLE_API_KEY`, não `GEMINI_API_KEY`

**AC7 — Importável e validável sem credencial e sem rede (AD-7, AD-12)**

**Given** a suíte de testes
**When** ela roda sem `GOOGLE_API_KEY` e sem `GEMINI_API_KEY` definidas
**Then** importar `plataforma.config` funciona e `carregar()` devolve os defaults
**And** os imports de `config.py` não alcançam `google.genai`, direta nem transitivamente
**And** nenhuma validação acontece em escopo de módulo — importar `config` com `TAMANHO_LOTE=99` **não** pode levantar

## Tasks / Subtasks

- [x] **Task 1 — Criar `plataforma/config.py`** (AC: 1, 2, 3, 4, 5, 6, 7)
  - [x] Declarar os defaults como constantes de módulo: `TAMANHO_LOTE_PADRAO = 10`, `MODELO_PADRAO = "gemini-3.6-flash"`, `FAIXA_LOTE = (2, 25)`
  - [x] Comentar o pino do modelo no padrão de `classificador.py:23` — alias móvel invalida comparação de F1 entre execuções
  - [x] Comentar que `10` é a premissa de NFR-1 (5 chamadas × lote 10 sobre 50 linhas), **não** um número medido
  - [x] Escrever `carregar()` devolvendo um `Config` (`NamedTuple` ou `dataclass(frozen=True)`) com `tamanho_lote: int` e `modelo: str`
  - [x] `load_dotenv()` **dentro** de `carregar()`, nunca em escopo de módulo — AC7 exige que o import seja inerte
  - [x] Manter `override=False` (o default) e comentar por quê: ambiente real vence `.env`, preservando o `export` documentado no README
  - [x] Ler com `os.environ.get(...)` e tratar `None` **e** string vazia/só-espaços como não definido (AC3)
  - [x] Validar a faixa e o tipo, levantando `ValueError` com mensagem que nomeia variável, valor observado e faixa
  - [x] **Não** expor concorrência (ver *Fora de escopo, com motivo*)
  - [x] **Não** ler a chave de API em lugar nenhum do módulo

- [x] **Task 2 — Atualizar `.env.example`** (AC: 6)
  - [x] Acrescentar `TAMANHO_LOTE=` e `MODELO=`, ambos sem valor à direita do `=`
  - [x] Comentar acima de cada um o default e a faixa, já que o valor não pode aparecer
  - [x] **Preservar CRLF** — o arquivo está em CRLF hoje; escrever linha nova em LF cria terminação mista

- [x] **Task 3 — Corrigir `README.md`** (AC: 6)
  - [x] Linha 25: trocar `export GEMINI_API_KEY=...` por `export GOOGLE_API_KEY=...`
  - [x] Documentar `TAMANHO_LOTE` e `MODELO` como configuráveis, com default e faixa
  - [x] **Não** tocar em `classificador.py` — ver *Não tocar*

- [x] **Task 4 — Estender o teste de whitelist de imports** (AC: 7)
  - [x] Em `tests/test_contrato.py`, acrescentar `(config, {"os", "dotenv"})` ao `parametrize` de `test_modulos_folha_so_importam_o_que_a_story_permite`
  - [x] Ajustar a docstring do teste: hoje diz "nenhum de terceiro", e `dotenv` é terceiro. A regra real é whitelist explícita por módulo — reescrever para isso
  - [x] Importar `config` no topo de `test_contrato.py` junto de `estado` e `catalogo`

- [x] **Task 5 — Criar `tests/test_config.py`** (AC: 1, 2, 3, 4, 5, 7)
  - [x] `monkeypatch.setenv` / `delenv` para cada caso — é o primeiro uso de `setenv` no repositório
  - [x] **Neutralizar o `.env` real em todo teste**: se existir um `.env` na raiz da máquina de quem roda, `load_dotenv()` o lê e o teste de default falha. Usar `monkeypatch.chdir(tmp_path)` ou passar por cima do carregamento — decidir e comentar a escolha
  - [x] Casos de faixa: `1` e `26` levantam; `2` e `25` passam (os limites são inclusivos)
  - [x] Casos de tipo: `abc`, `7.5`, `-3` levantam com mensagem nomeando o valor
  - [x] Casos de vazio: `TAMANHO_LOTE=` e `MODELO=` adotam o default
  - [x] Um teste que asserta que **importar** `config` com `TAMANHO_LOTE=99` não levanta (AC7)
  - [x] Um teste que asserta que a mensagem de erro contém `"2"` e `"25"` e o valor observado
  - [x] Escrever `2` e `25` **à mão** no teste, não importar `FAIXA_LOTE` — a fonte duplicada é deliberada, no padrão de `CAMPOS_ESPERADOS` em `tests/test_contrato.py:22-23`
  - [x] Rodar `uv run pytest` e confirmar verde

## Dev Notes

### O que esta story NÃO faz — leia antes de codar

**A fusão do lote residual de 1 não é desta story.** AD-17 diz duas coisas na mesma regra, e só a primeira é sua:

| Cláusula de AD-17 | Onde vive | Story |
|---|---|---|
| "piso 2 e teto 25, **verificados na carga da configuração**" | `config.py` | **1.2 — esta** |
| "a validação recai sobre os lotes emitidos, não sobre a variável" | — | declara que a faixa é insuficiente sozinha |
| "um lote residual de tamanho 1 é fundido ao anterior" | `ingestao.py` | 1.3 |
| "**quem fatia é `carregar`**, no mesmo lugar que emite os `Send`" | `ingestao.py` | 1.3 |

É estruturalmente impossível fazer a fusão aqui: na carga da configuração o CSV ainda não foi lido, então o resto da divisão não existe. `tamanho_lote = 7` sobre 50 linhas está **dentro** da faixa e ainda assim deixa um lote de 1 — a defesa é em duas camadas, em dois módulos, em duas stories. Vale um comentário no código apontando a divisão, senão parece esquecimento.
[Source: ARCHITECTURE-SPINE.md#AD-17, epics.md#Story 1.3]

### Decisões tomadas nesta story por ausência de fonte

Sete pontos não têm cobertura em PRD, SPEC, spine ou épicos. Foram decididos por restrição executável, não por preferência. **Implementar como está aqui**; se discordar, é conversa antes de codar, não durante.

**1. Default de lote = `10`.** Único número rastreável: NFR-1 é derivado de "5 chamadas em lote de 10" sobre 50 reclamações, e `classificador.py:24` já usa 10. Nenhum documento o declara como default e **não existe medição** de limite de contexto ou taxa de resposta incompleta por tamanho de lote. Comentar no código que é premissa de NFR-1, não número aferido.
[Source: prd.md#NFR-1, classificador.py:24, SPEC.md#Assumptions]

**2. Nome da variável do modelo = `MODELO`.** Não existe em documento nenhum — esta story o batiza. Escolhido por simetria com `TAMANHO_LOTE`, que as ACs já fixam: ambos em português, sem prefixo. *(Ver pergunta 1 ao final.)*

**3. Encerramento por `ValueError` levantado em `carregar()`, nunca `sys.exit` e nunca em escopo de módulo.** AC7 e AD-12 exigem que importar `config` funcione sob configuração inválida — `sys.exit` ou `raise` no import tornaria o módulo não-importável e quebraria a inspeção de imports que a própria story pede. O `main.py` da story futura traduz a exceção em saída de processo com a mensagem na tela. A spine não decide o mecanismo; decide só a categoria (falha de infraestrutura encerra sem escrever relatório).
[Source: ARCHITECTURE-SPINE.md#Convenções, prd.md:135]

**4. Valor presente e vazio = não definido.** Forçado por NFR-10: `.env.example` lista nomes **sem valores**, então quem o copia para `.env` fica com `TAMANHO_LOTE=`. Se vazio fosse erro, o fluxo documentado no próprio repositório quebraria na primeira execução. Tratar `None`, `""` e só-espaços igual.

**5. `config.py` não lê a chave de API.** Ele chama `load_dotenv()` para popular o ambiente e para por aí. O SDK lê `GOOGLE_API_KEY` sozinho, do ambiente, dentro de `analisar_lote` (AD-7). Assim a credencial nunca vira valor Python, nunca entra num objeto de config e nunca aparece num `repr` acidental. Também não valida presença da chave: a suíte precisa rodar sem ela, e ausência de credencial é falha em tempo de execução (PRD:143), de outra story.

**6. Sem validação do valor de `MODELO`.** Nenhum documento pede allowlist, e inventar uma congela o catálogo de modelos numa constante que envelhece. `MODELO=lixo` falha na primeira chamada paga — inconsistente com "encerrar antes de gastar", mas fechar isso exigiria consultar a API, que AD-7 proíbe aqui. Registrado como lacuna conhecida, não como defeito.

**7. Ordem entre validar config e ler o CSV: config primeiro.** Não está escrita em lugar nenhum. Config é mais barato e não depende de arquivo. Fora do escopo desta story (é do `main.py`/`grafo`), registrado para quem montar o entrypoint.

### A armadilha da credencial — o que ela realmente é

`project-context.md:99` registra a divergência `GEMINI_API_KEY` vs `GOOGLE_API_KEY` como dívida a resolver aqui. **A investigação do SDK instalado mudou o diagnóstico:**

`google-genai 2.17.0`, em `_api_client.py:101-117`, tem `get_env_api_key()` que lê **as duas**, com `GOOGLE_API_KEY` tendo precedência e fallback automático para `GEMINI_API_KEY`, emitindo um warning quando ambas existem.

Consequência: **`classificador.py:125` é código morto** — reimplementa à mão exatamente o que o SDK já faz. Não há bug funcional; nada quebra hoje. A dívida real é só documental: `README.md:25` exporta o nome não-canônico.

Portanto esta story **corrige o README e nada mais** nesse assunto. Não "consertar" `classificador.py`.

### O que a Story 1.1 estabeleceu e este módulo deve seguir

`config.py` é o terceiro módulo de `plataforma/`. Os dois primeiros fixaram o padrão:

- **Docstring de módulo:** uma linha de propósito terminada em ponto, linha em branco, parágrafo justificando a escolha não-óbvia. Sem lista de funções, sem `Args/Returns`. **Sem a linha `Rode:`** — essa é só de módulo executável, e `config.py` não é um.
- **Comentário explica o porquê e cita a fonte** (`AD-17`, `NFR-1`, `classificador.py:23`). Nunca o quê.
- **`# ponytail:`** para simplificação deliberada, sempre com o teto nomeado e o caminho de upgrade. Dois exemplos em `catalogo.py:85-88` e `104-105`.
- **Tudo em português:** módulo, constante, função, parâmetro, docstring, mensagem de erro.
- **Type hint só na assinatura de função pública.** Constantes não são anotadas.
- **Imutabilidade como defesa:** `catalogo.py` congela com `MappingProxyType`, `frozenset` e tupla. Se a config virar um objeto, congelar — `NamedTuple` ou `dataclass(frozen=True)`.
- **`config.py` não importa nada de `plataforma/`.** Ele é folha de origem: será importado por `analise`, `grafo` e `ingestao`, e não importa ninguém.
[Source: plataforma/estado.py, plataforma/catalogo.py, project-context.md]

### O padrão de teste que já existe — e o que vai quebrar

**Asserção sempre com mensagem que nomeia o valor observado**, prefixada pelo requisito que ela defende (`AC1:`, `AD-7:`, `CM-3:`). Nunca `assert x == y` pelado.

**`monkeypatch` com razão escrita.** `tests/test_import_sem_credencial.py` usa `delenv` das duas variáveis de credencial e `delitem` em `sys.modules` — com comentário explicando por que `delitem` e não `pop`. Esta story introduz o primeiro `setenv` do repositório.

**Verificação de import por AST.** `tests/test_contrato.py:51-71` tem `importados_por(modulo)`, que anda a árvore inteira e pega `ast.Import`, `ast.ImportFrom` (marcando relativo como `"."` via `no.level`) e `importlib.import_module`. Substituiu uma varredura textual que deixava `from . import catalogo` passar.

**⚠️ `config.py` vai reprovar nesse teste no minuto em que nascer.** A whitelist de `test_modulos_folha_so_importam_o_que_a_story_permite` (`tests/test_contrato.py:125-133`) lista stdlib **e** terceiros — só passa o que está escrito. Precisa da linha nova, e a docstring "nenhum de terceiro" fica falsa quando `dotenv` entrar. **Isto é Task 4, não é opcional.**

**Varredura preventiva já cobre o arquivo novo.** `tests/test_catalogo.py:79-92` faz `PACOTE.glob("*.py")` e falha se qualquer módulo que não seja `catalogo.py` contiver um código de sinal como literal. `config.py` passa por ela automaticamente — não é risco aqui, mas saiba que existe.

**Fonte duplicada de propósito.** `tests/test_contrato.py:22-23` explica: um teste que lê os campos do próprio módulo sob teste não detecta valor renomeado. Escreva `2` e `25` à mão em `test_config.py`.

**Sem mocks do SDK.** O repositório não tem essa camada e `project-context.md:73` proíbe criá-la. Nada aqui precisa dela.
[Source: tests/test_contrato.py, tests/test_catalogo.py, tests/test_import_sem_credencial.py]

### A armadilha de teste que vai custar tempo se você não souber

`load_dotenv()` lê o `.env` do diretório de trabalho. **Se a máquina de quem roda a suíte tiver um `.env` na raiz do projeto com `TAMANHO_LOTE` definido, o teste de default (AC2) falha** — e falha só na máquina dele, o que é o pior modo de falha possível.

Hoje não existe `.env` no working tree, mas ele está no `.gitignore` e é esperado que exista em uso real. Decidir e comentar a estratégia: `monkeypatch.chdir(tmp_path)` antes de chamar `carregar()`, ou um parâmetro que desligue o carregamento no teste. **Não deixar implícito.**

### Fora de escopo, com motivo

**Concorrência não é exposta.** O seed estrutural manda `config.py` carregar "lote, concorrência, modelo" (`ARCHITECTURE-SPINE.md:248`), mas AD-9 (`:84`) declara que `max_concurrency` "só é honrado pelo executor assíncrono, e o v1 invoca de forma síncrona". Nenhuma AC desta story menciona concorrência. Expor um botão que não move nada é pior que não expor — a story fica do lado do invariante.

**O limiar de 10% de NFR-6 não entra aqui.** Está sem dono declarado, mas AD-22 põe os números em `agregar`. Não adotar por iniciativa.

**Cache não entra.** Cache de chamadas é non-goal do v1 (`SPEC.md:79`). O `.cache_analises.json` da raiz é de `classificador.py`, ferramenta de medição, não recurso do pipeline.

### Dívidas conhecidas que esta story não fecha

- **`config` não alcança `ingestao` no diagrama de dependência.** A spine desenha só `config -.-> analise` e `config -.-> grafo`, mas AD-17 manda `carregar` (que é `ingestao.py`) fatiar. Aberto desde a reconciliação spec/spine, não endereçado. A Story 1.3 vai criar essa aresta.
- **Base com menos de 2 reclamações.** Um CSV de 1 linha produz um `Send` de tamanho 1 sob qualquer `tamanho_lote` válido. A revisão adversarial propôs uma cláusula em AD-17 para isso; o texto final não a absorveu. Dívida de `ingestao.py`.
- **Modelo configurável sem rastro na saída.** FR-2 e FR-14 listam quatro números e o modelo não é um deles. Se o operador troca o modelo, o relatório não registra qual rodou. Ponta solta reconhecida.

### Estrutura de arquivos

```text
plataforma/
  config.py           # NOVO — defaults, carregar(), validação de faixa
.env.example          # UPDATE — acrescentar TAMANHO_LOTE e MODELO, sem valores (CRLF!)
README.md             # UPDATE — GOOGLE_API_KEY no lugar de GEMINI_API_KEY
tests/
  test_config.py      # NOVO
  test_contrato.py    # UPDATE — whitelist de imports ganha config
```

**Não criar nesta story:** `ingestao.py`, `analise.py`, `evidencia.py`, `pontuacao.py`, `agregacao.py`, `relatorio.py`, `grafo.py`, `main.py`, `templates/`.

**Não tocar:** `baseline.py`, `classificador.py`, `docs/`. São medição preexistente e a Story 3.1 depende deles intactos — inclusive a linha morta de `classificador.py:125`.

### Bibliotecas e versões

| Item | Versão | Nesta story |
|---|---|---|
| `python-dotenv` | `1.2.2` — **já declarado e travado** | sim, é o mecanismo único |
| `pytest` | `9.1.1` | já em `[dependency-groups] dev` |
| `langgraph` | `1.2.10` | não |
| `jinja2` | `3.1.6` | não |
| `google-genai` | `2.17.0` | **não** — AD-7 proíbe importá-lo daqui |

**Nada a instalar.** Nenhum `uv sync`, nenhuma linha nova em `pyproject.toml`. `load_dotenv(override=False)` é o default da 1.2.2 e é o comportamento correto: variável real de ambiente vence o `.env`.

### Conformidade com a arquitetura

| Invariante | Como esta story o honra |
|---|---|
| **AD-7** | `config.py` não importa `google.genai`; a chave nem passa por ele |
| **AD-12** | Import e `carregar()` funcionam sem credencial e sem rede |
| **AD-17** | Faixa 2–25 verificada na carga, encerrando antes de qualquer chamada paga |
| **AD-9** | Concorrência **não** é exposta — seria botão inerte no v1 síncrono |
| **NFR-2** | Lote configurável por ambiente, sem tocar código |
| **NFR-10** | Credencial só de ambiente; `.env.example` só com nomes |

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2] — ACs originais
- [Source: .../ARCHITECTURE-SPINE.md#AD-7, AD-9, AD-12, AD-17] — invariantes; AD-17 divide a validação entre duas stories
- [Source: .../ARCHITECTURE-SPINE.md:202-203] — convenções de configuração e credencial
- [Source: .../ARCHITECTURE-SPINE.md:248,254] — seed estrutural de `config.py` e `.env.example`
- [Source: .../prd.md#NFR-1, NFR-2, NFR-3, NFR-10, DG-4] — requisitos; NFR-1 é a origem rastreável do default 10
- [Source: .../prd.md:135-146] — comportamento em falha; config inválida não está na tabela
- [Source: .../SPEC.md:68,83,94] — chamada individual proibida, base inteira num prompt é non-goal, tamanho de lote é ponto de partida arbitrário
- [Source: .env.example, README.md:25] — a divergência documental a corrigir
- [Source: .venv/.../google/genai/_api_client.py:101-117] — o SDK já faz o fallback; `classificador.py:125` é código morto
- [Source: plataforma/estado.py, plataforma/catalogo.py] — padrão de módulo da Story 1.1
- [Source: tests/test_contrato.py:51-71,125-133] — `importados_por` e a whitelist que precisa da linha nova
- [Source: _bmad-output/project-context.md] — convenções e armadilhas do repositório

### Perguntas para o Neo — não bloqueiam a implementação

1. **`MODELO` como nome da variável de ambiente, ou prefixado?** Nenhum documento a nomeia. Escolhi `MODELO` por simetria com `TAMANHO_LOTE`. `MODELO` é genérico o bastante para colidir com outra coisa no ambiente de alguém; `GEMINI_MODELO` ou `MODELO_LLM` seriam mais seguros e menos simétricos.
2. **`config.py` deve avisar quando `MODELO` difere do default?** O modelo está pinado de propósito e trocá-lo invalida a comparação de F1 que M-1 reporta. Um aviso na tela ao usar modelo não-padrão custa duas linhas e evita medição silenciosamente incomparável. Nenhum requisito pede.

## Dev Agent Record

### Agent Model Used

claude-opus-5, via o workflow `bmad-dev-auto`. Spec derivado:
`spec-1-2-configuracao-validada-antes-de-qualquer-chamada-paga.md`.

### Debug Log References

- `uv run pytest` — 64 passed (eram 38 antes desta story).
- `uv run python -c "import plataforma.config, sys; assert not [m for m in sys.modules if m.startswith('google')]"` — sem saída, sem erro.

### Completion Notes List

**Correção às Dev Notes: `monkeypatch.chdir(tmp_path)` não neutraliza o `.env`.** Verificado
no `dotenv` instalado (`.venv/Lib/site-packages/dotenv/main.py`): `find_dotenv()` sobe a
partir do diretório do **arquivo que chamou** (`plataforma/`), não do cwd — acha a raiz do
projeto de qualquer diretório de trabalho. A neutralização é uma fixture `autouse` que
troca `config.load_dotenv` por no-op, e que também apaga `TAMANHO_LOTE` e `MODELO` do
ambiente real (o README manda o operador fazer `export`).

**Respostas às duas perguntas abertas:**

1. **Nome da variável do modelo:** adotado `MODELO`, como a story propôs. Reversível numa
   linha se colidir com algo no ambiente de alguém.
2. **Aviso ao usar modelo não-padrão:** não implementado. Nenhum requisito pede, e a
   observabilidade do projeto é a saída do operador ao encerrar, que ainda não existe. A
   ressalva foi para o `README.md`, onde o operador lê antes de trocar.

**Validação de tipo por `isascii() and isdecimal()`, não `try/except int()`.** Três
armadilhas fechadas, todas verificadas: `"²"` passa em `isdecimal()` e faria `int()`
levantar o erro cru que AC5 proíbe; `"١٠"` passa e viraria `10` sem o operador reconhecer
o valor; e acima de 4300 dígitos o próprio `int()` levanta `ValueError` sobre limite de
conversão, sem nomear variável nem faixa — por isso o comprimento é conferido antes da
conversão.

**Duas mensagens de erro, não uma.** Tipo inválido e faixa estourada têm diagnósticos
diferentes: quem escreveu `TAMANHO_LOTE=-3` informou um inteiro, e mandá-lo "informar um
número inteiro" seria diagnóstico errado no caso mais provável.

**`test_config_nunca_toca_na_credencial`.** AC6 era o critério mais sensível do lote e o
único sem teste: a whitelist de imports permite `os`, então um
`os.environ.get("GOOGLE_API_KEY")` entraria em `config.py` sem reprovar nada. O teste
varre a fonte do módulo e confere os campos de `Config`.

**Divergência documental resolvida como a story mandou:** só o `README.md` foi corrigido.
`classificador.py:125` continua intacto — é código morto (o SDK já faz o fallback em
`_api_client.py:101-117`) e a Story 3.1 depende do arquivo como está.

### File List

**Novos**
- `plataforma/config.py`
- `tests/test_config.py`

**Modificados**
- `.env.example` — `TAMANHO_LOTE=` e `MODELO=` sem valor, CRLF preservado
- `README.md` — `GOOGLE_API_KEY` no lugar de `GEMINI_API_KEY`; seção "Configuração"
- `tests/test_contrato.py` — `config` na whitelist de imports; docstring reescrita
- `tests/test_import_sem_credencial.py` — `plataforma.config` em `MODULOS`
