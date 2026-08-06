---
title: Revisão adversarial — pares compatíveis com os ADs e incompatíveis entre si
type: review
method: construção de pares
created: 2026-08-06
target: ../ARCHITECTURE-SPINE.md
inputs:
  - ../../../../specs/spec-plataforma-analise-reclamacoes/SPEC.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/state-contract.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/risk-signals.md
  - ../../../../specs/spec-plataforma-analise-reclamacoes/roadmap.md
  - ../../../prds/prd-plataforma-analise-reclamacoes-2026-08-06/prd.md
also_read:
  - ./reconcile-spec.md
  - ./reconcile-prd.md
---

# Revisão adversarial — 12 buracos

## Método

Nenhum achado aqui é da forma *"a spine não diz X"*. Cada achado é um **par construído**:
duas unidades de implementação, um nível abaixo dos ADs, escritas por dois desenvolvedores
competentes que leram os 18 ADs e obedeceram todos ao pé da letra — e que, ao se
encontrarem no mesmo repositório, produzem um sistema que não funciona, ou funciona e
mente.

O critério de admissão é duro: se uma das duas unidades viola algum AD, o par é descartado
e o achado não entra. O que sobra são as regiões onde os 18 ADs deixam **liberdade de
grau suficiente para duas escolhas incompatíveis** — e é essa liberdade que precisa ser
fechada, não a competência dos desenvolvedores.

Os achados de `reconcile-spec.md` e `reconcile-prd.md` que a spine já absorveu (AD-13 a
AD-18, e o alargamento de AD-4) **não são repetidos**. Vários dos buracos abaixo são
consequência direta desses ADs novos: fechar uma porta moveu a ambiguidade para o cômodo
ao lado.

Severidade: **CRÍTICO** = o sistema mente sem sinal; **ALTO** = duas implementações
divergentes, com dano a métrica ou a requisito; **MÉDIO** = divergência com dano a custo,
teste ou manutenção.

| # | Buraco | Sev. | Fecha com |
|---|---|---|---|
| B-1 | Fabricação total lê como execução limpa; e "falha de conteúdo" tem duas leituras que diferem por um `AssertionError` | **CRÍTICO** | AD-19 + aperto em AD-5 |
| B-2 | Dois donos de `na_fila`: `pontuar` ou `agregar` | **ALTO** | AD-20 |
| B-3 | `agregados: dict` sem forma; o flag de degradado tem dois calculadores legítimos | **ALTO** | AD-21 |
| B-4 | AD-17 valida a variável, não o lote emitido: o último lote de tamanho 1 é a chamada individual proibida | **ALTO** | aperto em AD-17 |
| B-5 | AD-7 × AD-12: o cliente em escopo de módulo torna a suíte sem credencial impossível; AD-16 fica inverificável | **ALTO** | aperto em AD-7 + AD-12 |
| B-6 | `Sinal.valida = None` + fixture fabricada à mão: duas leituras dão pontuações opostas nas 3 parcelas que só o teste executa | **ALTO** | aperto no contrato de estado |
| B-7 | Produto genérico sem dono: a leitura do lado do prompt torna AD-14 insatisfazível | **ALTO** | AD-22 |
| B-8 | `Motivo.rotulo` sem vocabulário; o caminho `atributo` não tem catálogo nenhum | **ALTO** | aperto em AD-18 |
| B-9 | O `Send` de AD-8 precisa de um estado de lote que não existe; a leitura ingênua colide no redutor | **MÉDIO-ALTO** | AD-23 |
| B-10 | `Pontuacao` por `Analise` ou por `Reclamacao`: dois denominadores para CM-1 e NFR-6 | **MÉDIO** | aperto em AD-20 |
| B-11 | AD-13 não diz **como** encerra: exceção no filtro ou aresta condicional | **MÉDIO** | aperto em AD-13 |
| B-12 | `caminho_html` é entrada ou saída? `Estado` não tem `caminho_csv` nem `data_execucao` | **MÉDIO** | aperto em AD-15 |

---

## B-1 — A execução perfeitamente limpa sobre 100% de fabricação `[CRÍTICO]`

Este é o buraco pedido explicitamente: o estado em que AD-2, AD-5 e AD-13 mandam coisas
opostas. Ele tem duas metades, e a segunda é pior que a primeira.

### Metade 1 — o estado em que as três regras não se contradizem, e é isso o problema

Construa a execução: a API responde, todos os 50 itens voltam bem formados, casam por
`id`, trazem `sentimento`, `produto` e `sinais`. **Toda citação é fabricada** — o modelo
parafraseou em vez de copiar. É o modo de falha exato que CAP-5 existe para pegar e que
CM-2 existe para medir.

Percorra os ADs:

- **AD-2** derruba todos os códigos. Correto, é o que ele manda.
- **AD-5** não produz `Falha` nenhuma — não houve falha de lote, de transporte, nem de
  casamento. Correto.
- **AD-6**: `50 == 50 + 0`. Passa.
- **AD-13**: `len(analises) == 50`, não é zero. **Não dispara.**
- **NFR-6**: 0 reclamações não analisadas, 0% — relatório **não** marcado como degradado.
- **FR-2** reporta ao operador: *50 lidas, 50 analisadas, 0 não analisadas, N sinais
  derrubados.*

O relatório é escrito, tem aparência de execução impecável, e **toda a classificação de
risco que ele carrega foi apagada em silêncio**. A fila que sobra é montada só sobre
motivos de `origem == "atributo"` — o modificador de `Status`, que sozinho tem F1 0,41
(`risk-signals.md`). O gestor recebe uma fila cuja única regra validada evaporou, sem
nenhuma marca no arquivo.

Nenhum AD é violado. AD-13 protege contra *zero análises*; ninguém protege contra *zero
evidência sobrevivente*. A spine tem porta para o denominador vazio e não tem porta para
o numerador vazio.

O agravante está registrado no próprio PRD: CM-2 mediu **zero derrubadas em 50
reclamações**, e o PRD diz que *"o número bom aqui é indistinguível de mecanismo morto"*.
A contramétrica que detecta este cenário existe, foi declarada como a mais importante, e
**não governa nada** — nenhum AD a converte em comportamento. Ela é um número impresso no
terminal do operador, que a UJ-1 diz que a Marina lê de relance antes de anexar o arquivo
no e-mail.

### Metade 2 — o par que quebra

Agora as duas unidades. Ambas escrevem `evidencia.py` + o caminho de derrubada.

**Unidade A — derrubada é evento contábil, não falha.**

```python
# evidencia.py
def verificar(analise, texto):  # AD-1: roda antes do delta entrar no estado
    ...
    return analise_com_valida_preenchida, codigos_derrubados  # contador para FR-2
```
`analisar_lote` devolve `{"analises": [...]}`. Nenhuma `Falha`. Justificativa: AD-2 diz
que o código *"é ausente para efeito de pontuação"* — fala de pontuação, não de falha.
A reclamação foi analisada; ela tem sentimento, produto e `Analise`. **Obedece todos os
18 ADs.**

**Unidade B — derrubada é falha de conteúdo, e a convenção manda registrá-la.**

A tabela de Consistency Conventions diz, com todas as letras: *"Falha de conteúdo vira
`Falha` no estado e a execução segue."* Citação fabricada é falha de conteúdo — está na
tabela §6 do PRD como linha própria. Logo:

```python
# analise.py
if todos_os_codigos_derrubados(analise):
    falhas.append({"ids": [analise["id"]], "causa": "citacao_fabricada", "no": "analisar_lote"})
return {"analises": [analise], "falhas": falhas}
```
Justificativa: sem isso, NFR-6 nunca marca degradado num cenário que é a definição de
degradação, e FR-14 mente para o leitor. **Também obedece todos os 18 ADs** — AD-5 define
o formato de `Falha`, não o conjunto de causas que a produzem; `causa: str` é campo livre.

**Onde quebram ao se encontrar.** A Unidade B viola AD-6, e viola no pior lugar possível:

```
len(reclamacoes) == len(analises) + sum(len(f["ids"]) for f in falhas)
50               == 50            + 50
```

A reclamação está nos **dois** baldes ao mesmo tempo. A asserção de AD-6 estoura — depois
do gather, ou seja, **depois de 100% das chamadas pagas**. Dinheiro gasto, `AssertionError`,
nenhum relatório. E o modo de falha classificado pela convenção como *"de conteúdo, a
execução segue"* se comporta como *"de infraestrutura, encerra"*.

O par é vicioso porque as duas unidades estão certas em partes diferentes do mesmo
documento: A obedece AD-2 e AD-6, B obedece a convenção de erro e NFR-6. A spine responde
as duas coisas em lugares diferentes e nunca cruza as respostas.

### O que fecha

**AD-19 — Evidência derrubada é degradação, não silêncio, e nunca é `Falha`.**

- **Rule:** `falhas` tem exatamente um produtor e uma semântica: **ausência de `Analise`**.
  Nenhum outro caminho de código escreve em `falhas` — derrubada de evidência, produto
  nulo e sentimento improvável não são falhas, sob pena de AD-6 abortar a execução por
  falha de conteúdo. A derrubada de AD-2 é contabilizada em `agregados` e, acima de um
  limiar em `config.py` (default: **toda reclamação com sinal cujo total de códigos
  sobreviventes é zero** ultrapassando 20% das analisadas), o relatório é marcado como
  degradado pelo mesmo mecanismo de NFR-6, com causa distinta e nomeada. Zero código
  sobrevivente em 100% das reclamações encerra sem escrever, pela mesma porta de AD-13.
- **Prevents:** o relatório de aparência limpa sobre uma execução em que a única leitura
  validada do produto foi integralmente apagada — e o `AssertionError` de AD-6 disparado
  por uma falha que a convenção manda absorver.
- **Aperto correlato em AD-5:** acrescentar *"`falhas` é escrita apenas por
  `analisar_lote`, e apenas quando a reclamação termina sem `Analise`."*

---

## B-2 — Dois donos de `na_fila` `[ALTO]`

**Unidade A — o corte é da pontuação.**

```python
# pontuacao.py
def pontuar(estado):
    return {"pontuacoes": [
        {"id": a["id"], "pontos": p, "na_fila": p >= CORTE, "motivos": m}
        for a in estado["analises"] for p, m in [calcular(a, estado["reclamacoes"])]
    ]}
```
Justificativa: AD-4 define `Pontuacao = {id, pontos, na_fila, motivos}` e `pontuar` é
quem produz `Pontuacao`. O corte (≥ 3) é calibração de score, e score é de `pontuacao.py`.
**Obedece todos os 18 ADs.**

**Unidade B — o corte é da fila, e a fila é de `agregar`.**

O Structural Seed é literal: `pontuacao.py # nó pontuar — parcelas, modificador de Status,
motivos`. **`na_fila` não está nessa lista.** E `agregacao.py # nó agregar — ranking,
distribuição, **ordenação da fila**`. Quem ordena a fila decide quem está nela — é a mesma
operação. Logo:

```python
# pontuacao.py  → devolve na_fila=False, é campo de outro dono
# agregacao.py
fila = sorted([p for p in estado["pontuacoes"] if p["pontos"] >= CORTE],
              key=lambda p: -p["pontos"])
return {"agregados": {..., "fila": fila}}
```
**Também obedece todos os 18 ADs.** Nenhum AD nomeia o dono do corte; nenhum AD proíbe
`agregar` de filtrar; AD-4 fala sobre o que `renderizar` **não** faz, não sobre quem
decide.

**Onde quebram ao se encontrar.** Três colisões, em ordem de dano:

1. **A fila some.** Se `pontuacao.py` vem da Unidade B e o template vem da Unidade A
   (`{% for p in pontuacoes if p.na_fila %}`), a fila renderiza **vazia** — e a tabela §6
   do PRD diz que fila vazia é informação legítima, então nada acusa. FR-11 e a UJ-2
   inteira morrem em silêncio, sobre uma execução tecnicamente perfeita.
2. **`pontuacoes` ganha um segundo escritor.** Se a Unidade B decide preencher `na_fila`
   em vez de duplicar a fila em `agregados`, `agregar` precisa **reemitir `pontuacoes`
   inteiro** — a chave não tem redutor, então o delta substitui. Duas etapas escrevendo a
   mesma chave é exatamente o que o paradigma da spine (*"nenhuma etapa muta o estado que
   recebeu"*) existe para impedir, e nenhum AD o proíbe porque a proibição está na prosa
   do paradigma, não numa regra.
3. **M-1 mede outra coisa.** A medição de precisão ≥ 95% / recall ≥ 65% lê o conjunto
   marcado. Sob A ela lê `Pontuacao.na_fila`; sob B ela lê `agregados["fila"]`. O script
   que reproduz M-1 (hoje `baseline.py`/`classificador.py`, que a spine não governa) fica
   apontado para o campo errado e mede 0% de recall sem quebrar nada.

### O que fecha

**AD-20 — Cada chave do estado tem exatamente um escritor, nomeado.**

- **Rule:** `reclamacoes` ← `carregar`. `analises`/`falhas` ← `analisar_lote` (acumuladas).
  `pontuacoes` ← `pontuar`. `agregados` ← `agregar`. `caminho_html` ← `renderizar`.
  Nenhuma etapa emite delta para chave de outra etapa, nem para reordenar, nem para
  completar campo. `pontuar` é o dono do corte binário e de `na_fila`; `agregar` **ordena
  e conta, nunca decide pertencimento**. Os pesos (3/2/2/1), o modificador (−1) e o corte
  (≥ 3) vivem em `catalogo.py` ao lado dos códigos, com `risk-signals.md` declarado como
  fonte — se o corte e o código do sinal se separam, a calibração de 2026-08-06 vira
  irreproduzível.
- **Prevents:** a fila renderizada vazia sobre uma execução correta, e a substituição
  silenciosa de uma lista inteira do estado por um nó que só queria acrescentar um campo.

---

## B-3 — `agregados: dict` não tem forma, e o degradado tem dois calculadores `[ALTO]`

`Estado.agregados: dict`. Sem `TypedDict`, sem chaves declaradas, sem redutor, sem AD.
É a única estrutura do contrato que não tem forma — e é a que o template inteiro consome.

**Unidade A — `agregacao.py` é dono dos números do leitor.**

```python
return {"agregados": {
    "ranking": [{"produto": "fatura", "total": 8}, ...],
    "sentimento": {"negativo": 50},
    "total_lidas": 50, "total_analisadas": 45,
    "taxa_nao_analisada": 0.10, "degradado": False,
}}
```
Justificativa: AD-5 dá a `Falha` o bind `agregacao`, e o denominador de NFR-6 é um
agregado por natureza. **Obedece todos os 18 ADs.**

**Unidade B — `relatorio.py` calcula o degradado, porque AD-4 lhe deu `falhas`.**

AD-4, na redação atual: *"O nó `renderizar` lê `reclamacoes` para exibir (...) e `falhas`
para cumprir FR-14 e NFR-6, sem o que ele não tem como saber que a execução foi
degradada."* A regra **entrega a `renderizar` exatamente os dois insumos do cálculo** e
diz que ele precisa deles *para cumprir NFR-6*. A leitura natural:

```python
# relatorio.py
afetadas = sum(len(f["ids"]) for f in estado["falhas"])
ctx = {"degradado": afetadas / len(estado["reclamacoes"]) > 0.10, ...}
```
**Também obedece todos os 18 ADs.** A linha que AD-4 traça é *"nenhuma condicional do
template consulta `Reclamacao`"* — e aqui a condicional está em Python, e o que se
consulta é `falhas`. AD-4 é obedecido literalmente enquanto seu princípio (*quem decide
carrega a decisão*) é invertido.

**Onde quebram ao se encontrar.** Duas fontes para o mesmo número, e elas **divergem no
denominador**: A pode dividir por `total_analisadas` (45), B divide por `len(reclamacoes)`
(50) — 11,1% contra 10,0%, um lado do limiar de NFR-6 e o outro. O template recebe
`agregados["degradado"] = False` e a variável local `degradado = True` no mesmo contexto e
renderiza a que o autor do template lembrar. O limiar de 10% não está em `config.py` nem
declarado como constante em lugar nenhum, então ele aparece como literal em dois arquivos.

Colisão maior, e essa é estrutural: **nada declara as chaves de `agregados`.** A Unidade A
escreve `{"ranking": [{"produto":…, "total":…}]}`; o template da Unidade B itera
`{% for p in agregados.ranking %}{{ p.nome }} — {{ p.qtd }}`. Não há tipo, não há teste que
cruze os dois lados (AD-12 diz que a suíte é alimentada por `Analise` fabricada à mão — se
o teste de `renderizar` for alimentado por um `agregados` fabricado à mão, ele é fabricado
pelo autor do template e passa com a forma dele), e o erro só aparece ao abrir o HTML: o
Jinja2 com `autoescape` renderiza atributo inexistente como **string vazia**, sem levantar.
O ranking sai em branco e o relatório abre normalmente.

### O que fecha

**AD-21 — `agregados` é tipo, não dicionário.**

- **Rule:** `Agregados` é um `TypedDict` em `estado.py`, com as chaves que FR-13, FR-14,
  FR-15, NFR-6 e AD-14 exigem — `ranking`, `sentimento`, `total_lidas`,
  `total_analisadas`, `total_nao_analisadas`, `taxa_nao_analisada`, `degradado`,
  `fila`, `data_execucao`. `agregar` é o único que a preenche (AD-20); `renderizar` e o
  template apenas leem. O limiar de NFR-6 vive em `config.py`; **nenhum número de limiar
  aparece no template**. O teste de `renderizar` de AD-12 é alimentado pela saída real de
  `agregar`, não por um `agregados` fabricado à mão — fixture fabricada do lado do
  consumidor não testa o contrato, testa o consumidor contra si mesmo.
- **Prevents:** o ranking em branco num relatório que abre sem erro, e dois valores de
  `degradado` com denominadores diferentes no mesmo arquivo.

---

## B-4 — AD-17 valida a variável; o lote emitido escapa `[ALTO]`

AD-17 fecha as duas pontas nomeadas pelo SPEC com piso 2 e teto 25 em `tamanho_lote`.
O buraco está entre a variável e o `Send`.

**Unidade A — fatiamento por passo.** A forma canônica, que qualquer um escreve:

```python
lotes = [recs[i:i+tam] for i in range(0, len(recs), tam)]
```
`tam = 7`, 50 reclamações → 7 lotes de 7 e **um lote de 1**. `tam = 13` → 3 lotes de 13 e
um de 11 (ok). `tam = 7`, `tam = 24`, `tam = 16`… cada um deles produz um resto, e para
`tam` ∈ {7, 24, 49} sobre 50 linhas o resto é exatamente **1**.
**Obedece todos os 18 ADs** — `tamanho_lote = 7` passa na faixa [2, 25] de AD-17.

**Unidade B — fatiamento balanceado.**

```python
n_lotes = math.ceil(len(recs) / tam)
lotes = [recs[i::n_lotes] for i in range(n_lotes)]   # ou distribuição do resto
```
Nunca emite lote de 1 enquanto houver ≥ 2 reclamações. **Também obedece todos os 18 ADs.**

**Onde quebram ao se encontrar.** A Unidade A faz, com uma configuração válida, a
**chamada individual por reclamação** — que o SPEC lista como restrição explícita
(*"Chamada individual por reclamação é proibida"*) e que AD-17 declara no seu próprio
`Prevents` estar protegendo. A proibição foi movida da variável para o resto da divisão,
e o resto da divisão não tem guarda.

Não é hipotético: a Assumption do SPEC diz que o tamanho de lote *"é ponto de partida
arbitrário, a calibrar"*. Alguém **vai** varrer valores. E os dois lados divergem em algo
mais caro que estilo — o número de chamadas pagas contra o tier gratuito de NFR-3 difere
entre A e B para o mesmo `tamanho_lote`, então a medição de M-4 não é reproduzível entre
as duas implementações.

Segundo escape na mesma regra: **um CSV com 1 linha**. Passa em `ingestao.py` (schema
válido, unicidade trivial), não dispara AD-13 (há uma reclamação), e produz um `Send` de
tamanho 1 sob qualquer valor de `tamanho_lote`. AD-17 não alcança esse caso porque ele não
vem da configuração.

### O que fecha

**Aperto em AD-17:** *"a faixa [2, 25] vale para os lotes **efetivamente emitidos**, não
apenas para a variável. `carregar` distribui o resto de modo que nenhum `Send` carregue
menos de 2 reclamações. Base com menos de 2 reclamações encerra em `carregar`, pela mesma
porta de AD-13 — uma reclamação não é um lote."*

---

## B-5 — AD-7 × AD-12: a suíte sem credencial é impossível de escrever `[ALTO]`

A pergunta pedida: como o teste de `analise.py` é escrito sem violar um dos dois?

**Unidade A — `analise.py` idiomático.**

```python
# analise.py
from google import genai
cliente = genai.Client()          # lê GOOGLE_API_KEY do ambiente
def analisar_lote(estado): ...
```
Cliente em escopo de módulo é a forma que o SDK documenta e a que evita reconstruí-lo a
cada um dos N lotes do fan-out de AD-8. **Obedece AD-7** (é o único módulo que importa o
SDK), **obedece AD-9** (nenhum laço), **obedece AD-16** (empresa fora do payload).

**Unidade B — o teste que AD-16 exige.**

AD-16 diz que `empresa` fica fora do payload *"por construção — não por instrução no
prompt"*. Uma regra "por construção" só é regra se houver quem a verifique, e o único
lugar onde ela é verificável é a função que monta o payload:

```python
# tests/test_analise.py
from plataforma.analise import montar_payload
def test_empresa_nao_atravessa():
    assert "empresa" not in json.dumps(montar_payload([REC_FIXA]))
```
**Obedece AD-12** — nenhuma chamada de rede acontece. **Obedece AD-7** — o teste não
importa `google.genai`, importa `analise`.

**Onde quebram ao se encontrar.** `from plataforma.analise import montar_payload` executa
o módulo, que executa `genai.Client()`. Numa máquina sem `GOOGLE_API_KEY` — a máquina de
CI, a máquina do avaliador técnico que clonou o repositório, a máquina de qualquer um que
só quer rodar `pytest` — o **import levanta**, e a suíte inteira fica vermelha na coleta.
AD-12 promete que julgar é testável sem credencial; a Unidade A torna isso falso sem
violar nenhuma palavra de AD-7 nem de AD-12, porque nenhum dos dois fala sobre **quando** o
cliente é construído. "Nenhum teste faz chamada de rede" é obedecido: nenhuma chamada é
feita, o import é que morre antes.

Duas consequências além da suíte vermelha:

- **AD-16 fica sem verificação possível.** A lista de AD-12 é *"verificar, pontuar, agregar
  e renderizar"*. `analise` não está nela. Se o import de `analise` exige credencial, a
  regra mais concreta contra o ranking falso (a restrição que `reconcile-spec.md` marcou
  como a de justificativa mais forte do SPEC inteiro) não tem teste, e o desenvolvedor que
  acrescentar `"empresa": r["empresa"]` ao payload não encontra nada vermelho.
- **NFR-7 idem.** O casamento por `id` e o descarte do id inventado vivem em `analise.py`
  e caem no mesmo buraco. É a defesa contra *"o modo mais silencioso de corromper a base
  inteira"* (`state-contract.md`), e ela é a única lógica não trivial do sistema sem teste
  alcançável.

### O que fecha

**Aperto em AD-7:** *"o cliente do modelo é construído dentro de `analisar_lote`, nunca em
escopo de módulo, e a credencial é lida no momento da chamada. `import plataforma.analise`
é seguro e silencioso sem credencial — é o que torna AD-12 possível."*

**Aperto em AD-12:** *"as partes puras de `analise.py` — montagem do payload (AD-16),
casamento por `id` e descarte do id não pedido (NFR-7) — são funções separadas da chamada
e têm teste próprio. A ausência de `empresa` no payload é asserção, não intenção."*

Corolário barato que fecha a linha *"API sem credencial"* da §6 do PRD, hoje sustentada por
5 lotes esgotando `RetryPolicy` contra um 401: `main.py` verifica a presença da chave
antes de compilar o grafo.

---

## B-6 — `Sinal.valida = None` decide a pontuação das três parcelas que só o teste executa `[ALTO]`

O contrato declara `valida: bool | None  # None até a verificação rodar`. AD-1 garante que
a verificação roda dentro de `analisar_lote`, antes de o delta entrar no estado — logo
`None` **nunca chega em produção**. É exatamente por isso que ele é perigoso.

**Unidade A — `pontuacao.py` conservador.**

```python
pontos = sum(PESOS[s["codigo"]] for s in a["sinais"] if s["valida"])
```
`None` é falsy → sinal não pontua. Justificativa: na dúvida, não pontuar, porque falso
positivo custa mais. **Obedece todos os 18 ADs.**

**Unidade B — `pontuacao.py` que confia no invariante de AD-1.**

```python
pontos = sum(PESOS[s["codigo"]] for s in a["sinais"] if s["valida"] is not False)
```
Justificativa: AD-2 define a derrubada como um estado explícito (`valida == False`); `None`
significa *não avaliado*, e por AD-1 isso é impossível aqui, então tratar `None` como
derrubado seria esconder um bug em vez de expô-lo. **Também obedece todos os 18 ADs.**

**Onde quebram ao se encontrar.** AD-12 manda alimentar a suíte com *"`Analise` fabricada
à mão"*, e o contrato diz que `valida` nasce `None`. O autor da fixture escreve o que o
contrato manda:

```python
ANALISE_AMEACA = {"id": "X", "sentimento": "negativo", "produto": None,
                  "sinais": [{"codigo": "ameaca_explicita",
                              "citacao": "vou procurar meus direitos na justiça",
                              "valida": None}], ...}
```

Sob A: 0 pontos, não entra na fila, **o teste falha** — e o desenvolvedor "conserta"
pondo `valida: True` na fixture, o que significa que o teste passou a exercitar um caminho
que a verificação nunca produziu.
Sob B: 3 pontos, entra na fila, o teste passa.

E AD-12 é explícito sobre o que está em jogo: *"as três parcelas que a base não exercita
(ameaça explícita, dano continuado, registro contraditório) (…) **a suíte é a única coisa
que as executa**"*. As três parcelas cuja validade inteira repousa na suíte são as três em
que o resultado depende de qual leitura de `None` o autor escolheu. Em produção nada
diverge, então nada revela a escolha — até chegar a base real, que é o único cenário para
o qual essas parcelas existem.

### O que fecha

**Aperto no contrato de estado (`state-contract.md`) e em AD-1:** *"`Sinal.valida: bool`.
O tipo `None` desaparece. AD-1 já garante que nenhum `Sinal` existe antes da verificação —
manter um estado que o invariante torna inalcançável só cria duas leituras dele."*

Uma palavra a menos no contrato mata a classe inteira. Se houver razão para manter `None`,
ela precisa estar escrita, e `pontuacao.py` precisa levantar ao encontrá-lo, não escolher.

---

## B-7 — Produto genérico: a leitura do lado do prompt torna AD-14 insatisfazível `[ALTO]`

CM-3 conta duas coisas — produto nulo (1 de 50) e produto genérico (18 de 50) — e o PRD
registra que contar só a primeira *"media exatamente o caso que o modelo evita"*. Nenhum
AD nomeia quem decide o que é genérico.

**Unidade A — o prompt resolve.** `analise.py` instrui: *"se o texto só permitir um
substantivo genérico (fatura, compra, produto, serviço, pedido), devolva `null`"*.
`Analise.produto` fica `None` em ~38% dos casos; `agregacao` manda todos para a linha
`não identificado` de FR-8/FR-13. **Obedece todos os 18 ADs** — AD-18 governa códigos de
sinal, não vocabulário de produto; AD-16 só proíbe `empresa`.

**Unidade B — a agregação resolve.** O modelo devolve o que leu (`"fatura"`);
`agregacao.py` mantém `GENERICOS = {...}` e os colapsa no ranking. **Também obedece todos
os 18 ADs.**

**Onde quebram ao se encontrar.**

1. **A Unidade A destrói o insumo de CM-3 de forma irreversível.** Depois de `null`, o
   estado não distingue *"o modelo não achou nada"* de *"o modelo achou uma palavra que não
   nomeia produto"* — que é precisamente a distinção que o PRD reescreveu a contramétrica
   para expor. CM-3 passa a valer 38% sob as duas leituras, mas sob A ela é incalculável
   por componente e a informação *não voltou*.
2. **A Unidade A torna AD-14 insatisfazível.** AD-14 exige que o ranking carregue *"a
   ressalva do que o limita nesta base — sentimento constante e **produto genérico**"*,
   *"ao lado do gráfico"*. Sob A não existe nenhum produto genérico no estado — só
   `não identificado`. A ressalva vira uma frase fixa sem número, ou o template precisa
   afirmar 38% que ele não tem como calcular. **Um AD obedecido inviabiliza outro AD.**
3. **Se as duas forem implementadas** (um dev no prompt, outro na agregação — o caso mais
   provável, porque cada um acha que está resolvendo um problema diferente), o colapso
   acontece duas vezes e o ranking perde as duas classes de uma vez.

### O que fecha

**AD-22 — O estado guarda o que o modelo leu; a classificação de genérico é da agregação.**

- **Rule:** `Analise.produto` guarda o termo cru extraído do texto, sem normalização e sem
  substituição por `None` por julgamento de qualidade — `None` significa apenas *o modelo
  não devolveu nada*. A lista de termos genéricos vive em `catalogo.py`, ao lado dos
  códigos de sinal e pela mesma razão de AD-18 (fonte única, versionada, importada pelo
  prompt e pela agregação, nunca literal solto). `agregar` emite o ranking com **três
  classes distintas** — nomeado, genérico, não identificado — porque CM-3 mede as duas
  últimas separadamente e AD-14 exige nomear a genérica ao lado do gráfico.
- **Prevents:** o ranking cujo topo é `fatura` apresentado como leitura de produto, e a
  perda irreversível do insumo da única contramétrica que o PRD reescreveu por já ter
  medido a coisa errada uma vez.

---

## B-8 — `Motivo.rotulo` não tem vocabulário, e o caminho `atributo` não tem catálogo `[ALTO]`

`Motivo = {origem, rotulo, citacao}`. AD-18 fecha os **códigos de sinal** em `catalogo.py`
e proíbe literal solto em `analise.py`, `pontuacao.py` e no template. `rotulo` fica fora
dessa regra, e é o campo que o gestor lê.

**Unidade A — `rotulo` é o código.**

```python
Motivo(origem="sinal", rotulo=s["codigo"], citacao=s["citacao"])
```
O template renderiza `{{ motivo.rotulo }}` → o gestor lê **`cobranca_indevida`**.
Justificativa: AD-18 proíbe literal solto no template, então mapear código → texto humano
no template exigiria um dicionário de códigos **dentro** do template — proibido.
Traduzir é impossível, logo o código é o rótulo. **Obedece todos os 18 ADs**, e viola
FR-17 (*"legível em português do Brasil, incluindo rótulos"*) sem tocar em nenhum AD.

**Unidade B — `rotulo` é o texto humano.**

```python
Motivo(origem="sinal", rotulo=CATALOGO[s["codigo"]].rotulo_pt, citacao=s["citacao"])
```
Justificativa: FR-17 e a UJ-2 (*"o item do topo diz **cobrança indevida, valor
recorrente**"*). O texto vem de `catalogo.py`, então AD-18 é obedecido. **Também obedece
todos os 18 ADs**, e coloca texto de apresentação em Python, o que AD-10 empurra para o
template — mas AD-10 fala de *"texto de produto (FR-13, FR-16)"*, não de rótulo de motivo.

**Onde quebram ao se encontrar.**

- `agregacao.py` produz *"temas recorrentes"* (CAP-7) agrupando por `Motivo.rotulo`. Sob A,
  o agrupamento é estável. Sob B, ele agrupa por string de apresentação — e no instante em
  que alguém parametriza o rótulo (*"Cobrança indevida — 3 ocorrências"*, tentação óbvia
  para FR-12), cada motivo vira um tema de contagem 1 e a seção de temas se dissolve, sem
  erro.
- Os testes de AD-12 afirmam sobre `rotulo`. Sob A, `assert m["rotulo"] == "cobranca_indevida"`;
  sob B, o mesmo assert com acento e espaço. Trocar a implementação quebra a suíte por
  motivo cosmético, e trocar a suíte esconde a troca.

**O buraco maior, que nenhuma das duas unidades resolve:** `origem == "atributo"`. AD-3 diz
que ele *"vem de coluna do CSV"* e AD-18 cataloga só os códigos de sinal. **Não existe
vocabulário nenhum para o rótulo de atributo.** Um dev escreve `rotulo="Status"`; outro
`rotulo="Não respondida"`; outro `rotulo="status_respondida"`. Os três obedecem tudo. E o
motivo de atributo é o que FR-9 exige exibir para o item que entrou na fila **sem
citação** — o caminho que a regra vencedora de M-1 (*Categoria + `Status` ≠ Respondida*)
usa para todo item que ela marca.

### O que fecha

**Aperto em AD-18:** *"`catalogo.py` é a fonte única de **dois** vocabulários fechados: os
códigos de sinal e os códigos de atributo (`status_nao_respondida`, `status_nao_resolvido`,
`categoria_dinheiro_retido`, …), cada um com seu peso e seu rótulo em pt-BR.
`Motivo.rotulo` carrega sempre o **código**, nunca o texto — o texto é resolvido na
renderização por um filtro do `Environment` construído a partir de `catalogo.py`
(importado, não literal), o que satisfaz FR-17 sem pôr literal no template e sem pôr
apresentação em `pontuacao.py`. Agrupamento de tema é sempre por código."*

Isso também fecha, de graça, o problema dos **dois vocabulários** que `reconcile-spec.md`
registrou em 1.4 sem dono: a parcela `dinheiro retido` — a única validada, peso 3, a que
sozinha explica o gabarito — passa a existir como código de atributo com casa declarada,
em vez de flutuar entre o catálogo de sinais e a tabela de pesos de `risk-signals.md`.

---

## B-9 — O `Send` de AD-8 precisa de um estado que o contrato não tem `[MÉDIO-ALTO]`

AD-8: *"`carregar` emite um `Send` por lote para `analisar_lote`"*. Um `Send` carrega um
payload que vira a entrada do nó. O contrato de estado tem **um** `TypedDict` (`Estado`) e
nenhuma noção de estado de lote.

**Unidade A — estado de lote próprio.**

```python
class EstadoLote(TypedDict):
    lote: list[Reclamacao]
Send("analisar_lote", {"lote": recs[i:i+tam]})
```
`analisar_lote(entrada: EstadoLote) -> dict`. Funciona. `EstadoLote` mora em `estado.py`
ou em `analise.py` — nenhum AD diz. **Obedece todos os 18 ADs.**

**Unidade B — reaproveitar `Estado`, porque é o contrato canônico.**

```python
Send("analisar_lote", {**estado, "lote_atual": recs[i:i+tam]})
```
Justificativa: CAP-9 promete um *"estado compartilhado explícito"* e o contrato se declara
*"o contrato completo"*; inventar um segundo `TypedDict` fora dele parece a violação.
**Também obedece todos os 18 ADs** — nenhum proíbe.

**Onde quebram ao se encontrar.** A Unidade B despacha N execuções paralelas que carregam
`reclamacoes` no payload e escrevem, cada uma, na chave `lote_atual` — que não tem redutor.
Com concorrência 1 (o default de AD-9) isso passa despercebido; no dia em que a Q-8 do PRD
for respondida e a concorrência subir — que é o botão que AD-9 expõe de propósito — o
LangGraph levanta `InvalidUpdateError` em qualquer chave sem redutor escrita por dois
ramos no mesmo super-passo. O bug nasce ligado ao único parâmetro que a spine convida a
mexer, e a suíte de AD-12 não o alcança porque ela testa funções puras, não o grafo.

Correlato mais barato: `analisar_lote` da Unidade A recebe `EstadoLote` e **não tem acesso
a `reclamacoes`** — o que é bom (fan-out limpo) mas significa que o texto original usado
por `evidencia.py` para a verificação de substring precisa vir dentro do lote. Se vier só
o `id`, a verificação de AD-1 é impossível dentro do nó, e alguém a moverá para depois do
gather — quebrando AD-1 (*"a verificação roda antes de o delta entrar no estado"*) sem
perceber que a quebrou.

### O que fecha

**AD-23 — O payload do `Send` é declarado e mínimo.**

- **Rule:** `EstadoLote = {lote: list[Reclamacao]}` vive em `estado.py`. O `Send` carrega
  **apenas** o lote — nunca o estado inteiro, nunca uma chave de trabalho no `Estado`
  compartilhado. Toda chave do `Estado` escrita por mais de uma execução de nó tem
  redutor; chave sem redutor tem escritor único (AD-20). O lote carrega o `texto` completo
  de cada reclamação, porque a verificação de AD-1 acontece dentro do nó.
- **Prevents:** o `InvalidUpdateError` que aparece só quando a concorrência sobe — ou seja,
  no dia em que a Q-8 for medida —, e a verificação de evidência migrando para depois do
  gather por falta de texto no lote.

---

## B-10 — `Pontuacao` por `Analise` ou por `Reclamacao`: dois denominadores `[MÉDIO]`

**Unidade A:** `pontuar` itera `analises` → 45 `Pontuacao` para 50 reclamações lidas.
**Unidade B:** `pontuar` itera `reclamacoes` → 50 `Pontuacao`; as 5 sem `Analise` recebem
apenas motivos de `origem == "atributo"`, que estão disponíveis sem o modelo (o `Status`
vem do CSV). Justificativa de B: a reclamação não analisada não desaparece do relatório —
é honestidade, é o espírito de AD-5.

Ambas obedecem todos os 18 ADs. AD-6 fala de `analises`, nunca de `pontuacoes`; nenhum AD
declara a cardinalidade de `pontuacoes`.

**Onde quebram.** CM-1 (*taxa de ocupação da fila*) tem limiar de 40% e folga medida de
**dois pontos**. `19/45 = 42,2%` reprova; `19/50 = 38,0%` aprova. A mesma execução, o mesmo
código de pontuação, dois vereditos na contramétrica — decididos por quem escolheu o `for`.
E a Unidade B abre um caminho pior: uma reclamação **nunca analisada** pode acumular pontos
de atributo e entrar na fila, exibindo ao gestor um item de risco sobre um texto que o
sistema não leu.

### O que fecha

**Aperto em AD-20:** *"existe exatamente um `Pontuacao` por `Analise` — reclamação sem
`Analise` não é pontuada e aparece no relatório apenas na contagem de não analisadas
(FR-14/NFR-6). Todo denominador de contramétrica é declarado: CM-1 sobre analisadas,
NFR-6 sobre lidas."*

---

## B-11 — AD-13 diz que encerra, não diz como `[MÉDIO]`

**Unidade A — guarda em `pontuar`,** que é o primeiro nó depois do gather e onde AD-6 já
inspeciona:

```python
if not estado["analises"]:
    raise ErroDeExecucao("zero análises: " + causas(estado["falhas"]))
```
**Unidade B — aresta condicional em `grafo.py`,** que é a forma que o framework oferece:

```python
g.add_conditional_edges("gather", lambda s: END if not s["analises"] else "pontuar")
```

Ambas obedecem todos os 18 ADs.

**Onde quebram.**

- Sob A, `pontuar` deixa de ser a *"função pura sobre estruturas do estado"* que AD-12
  declara: ela ganha um caminho de aborto, e a suíte precisa afirmar sobre exceção. E
  `main.py` tem de capturar uma exceção que atravessa o `invoke()` do LangGraph.
- Sob B, o grafo **termina normalmente** com `caminho_html` vazio e nenhum erro. `main.py`,
  seguindo FR-1 (*"o caminho final é impresso ao encerrar"*), imprime uma string vazia e
  sai com código 0. A execução que a §6 do PRD manda *"encerrar com a causa nomeada"*
  encerra em silêncio e com sucesso aparente — o que é o mesmo defeito que AD-13 existe
  para impedir, deslocado do arquivo para o código de saída.

Os dois contratos de saída são mutuamente exclusivos e `main.py` só pode ser escrito para
um deles. O mesmo vale para a porta gêmea de AD-13 (*CSV vazio encerra em `carregar`*) e
para a linha *"API indisponível"* da §6.

### O que fecha

**Aperto em AD-13:** *"o encerramento é uma aresta condicional para `END` em `grafo.py`;
nenhum filtro levanta exceção para controlar fluxo, porque isso os tiraria da pureza que
AD-12 exige. `main.py` é o único lugar que decide código de saída e mensagem, lendo
`analises`, `falhas` e `caminho_html`; `caminho_html` vazio significa nada escrito e
encerra com código não-zero e a causa nomeada."*

---

## B-12 — `caminho_html` é entrada ou saída, e `Estado` não tem com que derivá-lo `[MÉDIO]`

FR-1 manda o nome ser `relatorio-` + nome do CSV + data (AD-15). FR-4 manda checar
colisão. `Estado` tem `caminho_html: str` e **não tem `caminho_csv` nem `data_execucao`**.

**Unidade A — `main.py` deriva e semeia.** Checa a colisão de FR-4 antes de compilar o
grafo (milissegundos, zero chamada paga) e passa `caminho_html` no estado inicial.
`renderizar` escreve onde mandaram. **Obedece todos os 18 ADs.**

**Unidade B — `renderizar` deriva,** porque `caminho_html` está no `Estado` e todo campo
do `Estado` é produzido por um nó. **Obedece todos os 18 ADs** — até tentar escrever o
código: `renderizar` não tem o nome do CSV nem a data. O dev então acrescenta os dois ao
`Estado`, alterando o contrato que se declara *"a única parte do v1 que não é aditiva"*,
por um requisito de nomenclatura.

**Onde quebram.** Sob A, `caminho_html` é o único campo do estado que é **entrada**, e ele
fica preenchido mesmo quando AD-13 aborta e nada foi escrito — `main.py` imprime, por
FR-1, o caminho de um arquivo que não existe. Sob B, FR-4 só é verificado no último nó, ou
seja, **depois de gastar a execução inteira contra o tier gratuito de NFR-3** — e a
convenção que manda falhar *"antes de qualquer chamada paga"* é obedecida para o CSV de
entrada e ignorada para o arquivo de saída.

### O que fecha

**Aperto em AD-15:** *"o caminho de saída é derivado e verificado em `main.py`, antes de
compilar o grafo — FR-4 aborta em milissegundos, não depois do gather. `data_execucao`
entra no `Estado` como entrada (ela também é exigida por FR-14 e é a peça que falta para a
reclassificação por espera do roadmap). `caminho_html` é **saída**: só é preenchido depois
de a escrita concluir, e `main.py` trata vazio como nada escrito."*

---

## O padrão

Doze pares, e onze deles caem em três famílias:

1. **Chave de estado sem forma ou sem dono declarado** — B-2, B-3, B-6, B-9, B-10, B-12.
   `analises` e `falhas` têm redutor e semântica; `pontuacoes`, `agregados`,
   `caminho_html` e o payload do `Send` têm nome e nada mais. A metade do contrato que
   recebeu atenção é impecável; a outra metade é um `dict`.
2. **Vocabulário sem catálogo** — B-7, B-8. AD-18 resolveu isso para os códigos de sinal e
   provou que a solução é barata. Os outros três vocabulários do domínio — rótulos de
   atributo, termos genéricos de produto, causas de `Falha` — continuam como strings livres
   no meio do estado.
3. **Regra sem mecanismo** — B-1, B-4, B-5, B-11. AD-13 diz que encerra sem dizer como;
   AD-17 valida a variável e não o lote; AD-16 é *"por construção"* sem construção que a
   verifique; AD-2 derruba sem que ninguém se importe com o total derrubado. São regras
   corretas cuja tradução para código admite mais de uma forma, e as formas divergem.

É o mesmo padrão que `reconcile-spec.md` já tinha nomeado — *a spine é forte onde a
fronteira é de código e fina onde a regra é de conteúdo* — deslocado um nível abaixo:
agora a spine é forte onde a fronteira é de **módulo** (AD-7, AD-10, AD-11, AD-18 são
excelentes e mecanicamente verificáveis) e fina onde a fronteira é de **chave de estado**.

Cinco ADs novos (AD-19 a AD-23) e sete apertos fecham os doze. Nenhum deles custa mais que
um parágrafo, e três deles — `valida: bool` em vez de `bool | None`, `Agregados` como
`TypedDict`, cliente construído dentro da função — custam uma linha de código cada.
