# Reconciliação de dados — PRD Plataforma de Análise de Reclamações

**Data:** 2026-08-06
**Alvo:** `_bmad-output/planning-artifacts/prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md`
**Inputs verificados:** `docs/reclamacoes_reclameaqui.csv`, `docs/gabarito.csv`, `docs/gabarito-v1.csv`, `baseline.py`, `classificador.py`, `.cache_analises.json`, `.gitignore`, `.env.example`, `git ls-files`

Tudo abaixo foi contado, não estimado. Leitura via `csv.DictReader(delimiter=";", encoding="utf-8-sig")`.

---

## 1. Afirmações numéricas do PRD

| # | Afirmação no PRD | Local | Real | Veredito |
|---|---|---|---|---|
| 1 | 50 reclamações | §1, NFR-1, M-3 | 50 linhas de dados, 50 `ID_Reclamacao` únicos | **Confirmado** |
| 2 | 14 empresas fictícias | §1, DG-1 | 14 valores distintos em `Empresa` | **Confirmado** |
| 3 | 30 textos distintos em 50 linhas | §1 | 30 strings distintas em `Descricao` | **Confirmado — mas enganoso, ver §4.1** |
| 4 | Gabarito v2: 19 de 50 marcadas | M-1, Q-7 | 19 `sim` / 50 | **Confirmado** |
| 5 | Gabarito v1: 18 marcações | Q-7 | 18 `sim` / 50; diverge da v2 em exatamente 1 item (`RA645276696`, `nao`→`sim`) | **Confirmado** |
| 6 | Marcação humana em 38% | Q-3 | 19/50 = 38,0% | **Confirmado** (abaixo do limiar 40% da CM-1) |
| 7 | Regra determinística: F1 0,86 | M-1 | `python baseline.py`: TP=16 FP=2 FN=3, precisão 89%, recall 84%, **F1 0,86** | **Confirmado** |
| 8 | Gemini 3.6 Flash: F1 0,86 | M-1 | Recalculado de `.cache_analises.json` (50 análises): TP=16 FP=2 FN=3, **F1 0,86** | **Confirmado** |
| 9 | Zero divergências item a item entre regra e LLM | M-1 | Comparação item a item dos 50 IDs: **0 divergências** | **Confirmado — mas ver §3.3, é consequência estrutural, não coincidência** |
| 10 | Status sozinho tem F1 0,42 | Q-6 | Não reproduzível: nenhum código no repositório calcula F1 de `Status` isolado. `baseline.py` só mede `categoria` (0,86) e `categoria + Status` (0,81) | **Não verificável com os artefatos atuais** |
| 11 | Gabarito se contradiz em ~3% dos casos de texto idêntico | M-1 | 1 grupo de descrição idêntica com rótulos opostos, em 30 descrições distintas = **3,3%**. Envolve 2 linhas (`RA497478786` sim / `RA406284028` nao), 4% da base | **Confirmado na leitura estrita — subestimado, ver §4.2** |
| 12 | Ameaça explícita: 0 de 50 | Q-4 | Cache do LLM: `ameaca_explicita` verdadeiro em 0/50. Regex independente (`procon\|advogad\|process\|juizad\|judicial\|justiça\|acionar`) sobre as 50 descrições: **0 ocorrências** | **Confirmado por duas vias** |
| 13 | Formato: separador `;`, UTF-8 com BOM, datas `DD/MM/AAAA` | FR-3 | Header abre com BOM (`﻿`), separador `;`, todas as 50 datas em `DD/MM/AAAA` | **Confirmado** |
| 14 | Base "distribuída em 2026" | §1 | 100% em 2026, mas só fev–ago: 02=4, 03=12, 04=7, 05=5, 06=12, 07=9, 08=1. Sem janeiro e sem set–dez | **Impreciso** — não é distribuição anual |
| 15 | Base contém "protocolo de atendimento, código de rastreio e referência a conta bancária" | §5 | Protocolos: 8 ocorrências de `Protocolo: NNNNNNNN`. Lote: 1 (`lote 47295260`). Conta bancária: menção textual ("Minha conta bancária foi bloqueada"), **sem número de conta**. Código de rastreio: **mencionado sem valor** ("o código de rastreio não atualiza") | **Parcialmente confirmado** — não há rastreio nem conta com valor real |
| 16 | Ausência de dado pessoal | DG-1 | Ver §2 | **Confirmado** |

### Contagens adicionais (não afirmadas pelo PRD)

- Colunas: `ID_Reclamacao;Data;Empresa;Titulo;Descricao;Cidade_Estado;Status` (7)
- Títulos distintos: **18** (valores canônicos)
- `Cidade_Estado` distintos: 16
- `Status`: `Respondida` 12, `Em réplica` 12, `Não respondida` 11, `Não resolvido` 9, `Resolvido` 6 — **5 valores, não binário**
- Gabarito (ambas versões): colunas `ID_Reclamacao;Empresa;Titulo;Status;fila_prioridade`; conjunto de IDs idêntico ao da base

---

## 2. Governança de dados — DG-1 verificado

Varredura por regex sobre `Titulo`, `Descricao`, `Cidade_Estado` e `Empresa` das 50 linhas, mais leitura integral das 30 descrições distintas.

| Categoria | Padrão | Ocorrências |
|---|---|---|
| CPF | `\d{3}\.?\d{3}\.?\d{3}-?\d{2}` | **0** |
| CNPJ | `\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}` | **0** |
| E-mail | `[\w.+-]+@[\w-]+\.[\w.]+` | **0** |
| Telefone | `\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}` | **0** |
| Cartão | 16 dígitos agrupados | **0** |
| Endereço | `rua\|avenida\|av.\|alameda\|travessa\|nº\|apto\|bairro` | **0** |
| URL / domínio | `https?://\|www\.` | **0** |
| Nome de pessoa | leitura integral das 30 descrições | **0** — nenhum antropônimo; os únicos papéis citados são genéricos ("a gerente", "o entregador", "meu cachorro") |

**Os 11 números longos são todos benignos e sintéticos.** Contexto extraído linha a linha:

- 8 protocolos de 8 dígitos, todos no template de cobrança indevida (`Protocolo: 13561597`, `60806024`, `38317637`, `66661351`, `99788677`, `41726318`, `88406989`) e no de plano de saúde (`Protocolo 95225343`, `10076758`, `43273328`)
- 1 número de lote de ração (`lote 47295260`)
- Nenhum deles casa com formato de CPF, conta, agência ou cartão. O falso positivo do padrão de CEP se explica: são 8 dígitos, mesmo comprimento de um CEP sem hífen, mas aparecem sempre precedidos da palavra "Protocolo" ou "lote"

Os `ID_Reclamacao` seguem `RA` + 9 dígitos (`RA249827706`), padrão de identificador público do ReclameAqui, sem conteúdo pessoal.

Empresas, todas fictícias e sem correspondente real conhecido: AéreoBrasil, Banco DinheiroFácil, ComidaRápida App, Estilo Calçados, Farmácia Saúde Online, Loja do Lar, MegaEletro, ModaWeb, PetShop AnimalFeliz, Provedor NetVeloz, SeguroTotal, Supermercado CompreBem, TechPrime Brasil, TeleCom Mais.

**Veredito DG-1: confirmado.** A base é sintética e segura para repositório público. A conclusão de Q-1 se sustenta.

### Dois itens da §5 que estão factualmente errados

- **DG-4 — "o arquivo de ambiente está no `.gitignore` desde o primeiro commit": FALSO.** `git ls-files` retorna **um único arquivo: `README.md`**. O `.gitignore` está untracked (`git status` o lista em `??`) e `git log -- .gitignore` é vazio — ele nunca esteve em commit nenhum. A regra está escrita e correta no arquivo (`.env`, `.env.*`, `!.env.example`, `*.key`), e `.env.example` não contém valor de chave, mas a afirmação histórica do PRD não se sustenta. Corrigir para "está no `.gitignore`" e commitá-lo.
- **DG-5 — "O README declara explicitamente que o corpus é sintético": inexequível hoje.** `README.md` é o único arquivo versionado e está **deletado no working tree** (`git status`: `D README.md`). Não há README para declarar coisa alguma. DG-5 é um requisito pendente, não um fato.

### Observação de escopo para DG-3

`.cache_analises.json` (12,4 KB, na raiz) armazena as citações literais extraídas das descrições. Ele está corretamente coberto pelo `.gitignore`, mas DG-3 fala só do relatório. Sobre base real, o cache herda os mesmos dados pessoais que o relatório e merece menção explícita em DG-3.

---

## 3. Requisitos versus código já implementado

Inventário: `baseline.py` (classificador determinístico por título + métrica) e `classificador.py` (Gemini em lote, validação de evidência, métrica comparativa). Nenhum dos dois gera relatório nem aceita argumento.

### 3.1 Requisitos funcionais

| Req | Estado | Evidência |
|---|---|---|
| **FR-1** CSV por argumento + HTML em caminho previsível | **Nenhuma contraparte** | Ambos usam caminho fixo `DOCS / "reclamacoes_reclameaqui.csv"`. Nenhum uso de `sys.argv` ou `argparse`. Nenhum HTML |
| **FR-2** Relatório final ao operador (lidas/analisadas/falhas/derrubadas) | **Parcial** | `classificador.py` imprime por lote (`lote n/N · X analisadas`), o total de derrubadas (`sinais derrubados por citação inválida: N`) e um `AVISO` de não analisadas. Falta a consolidação única no fim; "lidas" nunca é impresso pelo classificador |
| **FR-3** Rejeitar schema divergente / ID duplicado antes de qualquer chamada de LLM | **Só em teste, não em produção** | As validações existem apenas em `baseline.py::autoteste()` (asserts de `len == 50`, unicidade de ID, igualdade de conjunto base↔gabarito). O caminho real (`ler()` → `classifica()`) não valida nada: coluna ausente vira `KeyError` em runtime, ID duplicado é silenciosamente sobrescrito pelo dict de `analises` |
| **FR-4** Não sobrescrever relatório anterior | **Nenhuma contraparte / contrariado** | Não há relatório. E `CACHE.write_text(...)` sobrescreve o cache sem aviso |
| **FR-5** Sentimento, produto e sinais por reclamação | **Cumprido** | Schema `Analise` carrega `sentimento`, `produto`, `dinheiro_retido`, `ameaca_explicita`. 50/50 no cache |
| **FR-6** Todo sinal carrega citação literal | **Cumprido** | Campos `evidencia_dinheiro` / `evidencia_ameaca` no schema; instrução explícita ("Copie caractere por caractere"; "Nunca invente citação"). Reforçado por FR-7 |
| **FR-7** Verificar citação no original e derrubar o sinal | **Cumprido, é o ponto mais forte do código** | `valida_evidencia()` — determinístico, `citacao not in texto` derruba o sinal, zera o campo e incrementa o contador. Coberto por `autoteste()` que injeta citação falsa de propósito (exatamente o teste que a CM-2 pede). Verificação independente: 18 evidências no cache, **0 não literais** |
| **FR-8** Produto não identificável com rótulo próprio | **Parcial** | `produto: str \| None` e o prompt manda `null`. Mas `None` não é um rótulo, e nada agrega nem ranqueia ainda. 1 de 50 no cache |
| **FR-9** a **FR-14** Relatório HTML | **Nenhuma contraparte** | Não existe geração de relatório em lugar nenhum do repositório |

### 3.2 Requisitos não-funcionais

| Req | Estado | Evidência |
|---|---|---|
| **NFR-1** 2 min para 50 | **Não medido** | Nenhuma instrumentação de tempo. `TAMANHO_LOTE = 10` sobre 50 linhas dá 5 lotes, exatamente a premissa da `[ASSUMPTION]` |
| **NFR-2** Lote configurável sem alterar código | **Contrariado** | `TAMANHO_LOTE = 10` é constante de módulo. Mudar exige editar o arquivo — precisamente o que o requisito proíbe |
| **NFR-3** Cabe no tier gratuito | **Não medido, plausível** | 5 chamadas por execução limpa; o cache reduz reexecuções a 0 chamadas |
| **NFR-4** Não repetir chamada para a mesma reclamação | **Cumprido, com folga** | Os lotes são partição disjunta por fatiamento. O cache vai além e evita repetição **entre** execuções |
| **NFR-5** Falha isolada não interrompe as demais | **Parcial — a lacuna mais séria** | ID ausente na resposta é tolerado (`if a is None: continue`) e reportado. Mas **não há `try/except` em volta de `analisa_lote()`**: erro de rede, 429, timeout ou falha de parse propaga e mata a execução inteira, perdendo os lotes já processados (o cache só é escrito no fim). Contradiz diretamente a linha "Limite de taxa da API atingido → Aguarda e repete a chamada" da §6 — não há retry algum |
| **NFR-6** Faltantes por identificador, nunca por posição | **Cumprido exemplarmente** | `recebidas` é `{a.id: ...}`; `faltando` compara conjuntos de ID; a associação em `for r in lote` é sempre por `r["ID_Reclamacao"]`. Nenhum acesso posicional |
| **NFR-7** Mesmos identificadores entre execuções | **Cumprido por construção** | O ID vem da coluna `ID_Reclamacao` do arquivo, não é gerado. 50 únicos verificados |
| **NFR-8** HTML portátil | **Não aplicável ainda** | Não há HTML |
| **NFR-9** Chave em variável de ambiente | **Cumprido** | `load_dotenv()` + `os.environ`, fallback `GEMINI_API_KEY` → `GOOGLE_API_KEY`. Nenhuma credencial literal nos fontes. `.env.example` com valor vazio |

### 3.3 Contradições entre PRD e código

1. **A "vitória empatada" da M-1 é estrutural, não empírica.** `pontua()` calcula `3*dinheiro_retido + 3*ameaca_explicita` e corta em `>= 3`. Como `ameaca_explicita` é 0 em 50 linhas (§1, item 12), o score do LLM colapsa em um booleano sobre `dinheiro_retido` — e `dinheiro_retido` é justamente o conceito que `CATEGORIAS_DINHEIRO` codifica no baseline. As **0 divergências item a item não são um resultado, são uma tautologia**: dois classificadores binários do mesmo conceito sobre uma base de 18 formas canônicas. O PRD apresenta isso como medição comparativa; ele mede menos do que sugere.
2. **O baseline não é generalizável e o PRD trata os dois como equivalentes.** `prioriza()` faz match exato de `Titulo` contra um set de 6 strings. O próprio `classificador.py` documenta por que isso não vale ("O título desta base é canônico (18 valores fixos) e entrega a resposta; base real não tem isso") e se recusa a usar o título. O F1 0,86 do baseline tem teto igual a esta base. A §1 do PRD já diz que se deve "inferir produto do texto e nunca da empresa" — o mesmo raciocínio se aplica ao título e o PRD não o estende.
3. **§6 promete retry, o código não tem nenhum** (ver NFR-5).
4. **DG-4 e DG-5 são factualmente falsos** (ver §2).

---

## 4. Características dos dados que o PRD não menciona e que afetam requisitos

### 4.1 As descrições não são 30 textos — são 18 templates parametrizados

Normalizando todo número (`\d+([.,]\d+)?` → `N`), as 30 descrições distintas colapsam em **18 templates**. Distribuição: 5 templates com 1 ocorrência, 2 com 2, 7 com 3, 2 com 4, 1 com 5, 1 com 7.

Exemplo: as 7 linhas de cobrança indevida são a mesma frase, variando só o valor (`R$ 262,57`, `R$ 487,10`, `R$ 148,52`, `R$ 96,79`, `R$ 134,24`, `R$ 464,66`, `R$ 47,44`) e o protocolo. As 3 de internet variam só o plano (300/500/600 mega).

**Consequência.** A base tem 18 formas de descrição e 18 títulos canônicos. O aviso da §1 ("qualquer acurácia medida aqui superestima o desempenho sobre linguagem real") está **certo mas quantificado por baixo**: dizer "30 textos distintos" sugere metade da variação real. Trocar por "18 templates parametrizados, 30 strings distintas" torna o aviso proporcional ao problema.

### 4.2 O gabarito se contradiz muito mais do que 3%

- **Texto exatamente idêntico:** 1 grupo contraditório em 30 descrições distintas = 3,3% (é a leitura que sustenta o "cerca de 3%" do PRD). Par: `RA497478786` (sim) / `RA406284028` (nao) — descrição, título **e Status idênticos** (ambos `Resolvido`); as únicas diferenças são empresa, cidade e data, nenhuma delas informativa dado o pareamento ao acaso.
- **Template idêntico (só o valor em R$ muda):** **4 templates contraditórios, 15 das 50 linhas — 30% da base.**
  - Cobrança indevida (7 linhas): `RA702632297` nao, `RA184611066` sim, `RA709004943` sim, `RA740389325` nao, `RA621209849` sim, `RA278575192` sim, `RA611947770` sim
  - App travando (2): sim / nao
  - Plano de saúde (3): sim / nao / nao
  - Mensalidade aumentou (3): sim / nao / nao
- **Por título:** os mesmos 4 títulos apresentam rótulos divergentes.

**Consequência direta em M-1.** O teto de F1 alcançável é estrutural e bem abaixo de 1,0 — nenhum classificador que leia apenas o texto pode acertar 15 linhas cujo texto é indistinguível e cujos rótulos são opostos. O alvo de 0,85 é defensável, mas a justificativa "cerca de 3%" no PRD subdimensiona o motivo em uma ordem de grandeza. Vale registrar em M-1 os dois números.

### 4.3 Sentimento é constante — CAP-2/FR-5 não discriminam nada nesta base

Cache do LLM: **50 de 50 negativos**. Zero neutros, zero positivos. Uma base de reclamações não tem por que ter outra coisa.

**Consequência.** FR-5 pede sentimento e M-5 pede que o leitor saiba "como o cliente se sente com a marca". Sobre esta base a resposta é uma constante — a seção de percepção de marca do relatório será um bloco que diz "100% negativo" e não informa nada. Ou o eixo vira intensidade/gravidade em vez de polaridade, ou M-5 é invalidável aqui.

### 4.4 `Status` tem 5 valores e o código só olha um

`Respondida` 12, `Em réplica` 12, `Não respondida` 11, `Não resolvido` 9, `Resolvido` 6.

`baseline.py::prioriza()` e `classificador.py::pontua()` testam apenas `== "Respondida"`, como atenuante. As 20 linhas em `Não respondida` / `Não resolvido` — plausivelmente **agravantes** e o dobro do volume — não têm tratamento algum.

**Consequência em Q-6.** A questão foi fechada com "Status sozinho tem F1 0,42, entra como modificador negativo dentro da categoria certa". O modificador implementado é unidirecional e cobre 12 de 50 linhas. A hipótese que nunca foi testada é a simétrica (`Não resolvido`/`Não respondida` como modificador positivo, 20 linhas). Q-6 fechou antes de esgotar a coluna.

### 4.5 O produto é extraído, mas em rótulos genéricos demais para ranquear

Cache: 19 valores distintos de `produto`, e o topo é ocupado por termos que não são produto nenhum — `fatura` 7, `internet` 5, `compra` 4, `produto` 4, `conta bancária` 4, `serviço` 3, `aparelho` 3, `convênio` 3, `blusa` 3, e por aí. Apenas 1 é `None`.

**Consequência em FR-8, CM-3 e Q-2.** CM-3 mede "taxa de produto não identificado" e ficaria em 2% — verde. Mas o risco real do ranking (FR-12) não é o produto ausente, é o produto **identificado de forma inútil**: um ranking cujo primeiro lugar é "fatura" e cujo quarto é "produto" não ordena nada. Vale ou fixar um vocabulário fechado de produto no prompt, ou acrescentar uma contramétrica de rótulos genéricos.

### 4.6 O pareamento empresa↔reclamação ao acaso: confirmado

Amostras reais: `Supermercado CompreBem | Voo cancelado sem aviso prévio`; `Provedor NetVeloz | Voo cancelado sem aviso prévio`; `TechPrime Brasil | Plano de saúde negou meu exame`; `TeleCom Mais | Plano de saúde negou meu exame`. A §1 do PRD está correta e o `classificador.py` já respeita a regra (o prompt recebe só `Descricao`, nunca `Empresa`).

Nota adicional: como a empresa é ruído, qualquer agregação por empresa no relatório produzirá um ranking sem significado. O PRD não pede tal agregação — mas também não a proíbe explicitamente na §8.

### 4.7 Coluna morta

`Cidade_Estado` (16 valores) não é lida por nenhum código nem mencionada em nenhum requisito. Ou entra em algum lugar, ou vale declará-la fora de escopo para que a próxima pessoa não a descubra e presuma que foi esquecida.

### 4.8 O único sinal quantitativo real da base está sem uso

Dentro de cada template, a variação semântica é o valor em reais: R$ 47,44 a R$ 487,10 na cobrança indevida; R$ 111,15 a R$ 453,17 no aumento de mensalidade. É o único gradiente contínuo do corpus, e nem o baseline nem o prompt o extraem.

**Consequência.** É exatamente o insumo que a "fila por níveis" do roadmap precisaria, e a resposta natural à CM-1 se a ocupação da fila subir. Vale registrar em Q-3 que a via de desempate existe e está disponível.

---

## 5. Resumo de ações sugeridas ao PRD

| Item | Ação |
|---|---|
| §1 | Trocar "30 textos distintos" por "18 templates parametrizados (30 strings distintas)" |
| §1 | Ajustar "distribuídas em 2026" para "fev–ago de 2026" |
| M-1 | Registrar os dois números de contradição do gabarito: 3,3% em texto idêntico, **30% da base em template idêntico** |
| M-1 | Declarar que o empate regra↔LLM decorre de `ameaca_explicita = 0`, que reduz o score do LLM a um booleano sobre `dinheiro_retido` |
| Q-6 | Reabrir parcialmente: o modificador de `Status` cobre 12 linhas (`Respondida`) e ignora 20 (`Não resolvido`/`Não respondida`) |
| FR-5 / M-5 | Registrar que sentimento é 50/50 negativo e não discrimina nesta base |
| FR-8 / CM-3 / Q-2 | O risco do ranking é o rótulo genérico ("fatura", "produto", "compra"), não o rótulo ausente (1/50) |
| DG-4 | Corrigir: `.gitignore` está untracked; o único arquivo versionado é `README.md` |
| DG-5 | Reclassificar de fato para pendência: `README.md` está deletado no working tree |
| DG-3 | Estender a `.cache_analises.json`, que também herda citações literais |
| §5 | "código de rastreio" e "conta bancária" são mencionados no texto sem valor associado; ajustar a frase de abertura |
| NFR-2 | Contrariado hoje: `TAMANHO_LOTE` é constante de módulo |
| NFR-5 / §6 | Sem `try/except` e sem retry em `analisa_lote()`; a linha de rate limit da §6 não tem implementação |
| Q-3 | Registrar o valor em R$ como o gradiente disponível para a fila por níveis |
