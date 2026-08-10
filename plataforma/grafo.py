"""Monta o grafo do pipeline: carga, fan-out por lote, absorção de falha e escrita do relatório.

`Estado` não tem campo para o caminho do CSV nem do HTML de saída (Story 1.1 não
previu isso), então `construir_grafo` é fábrica — `caminho` e `caminho_saida` viram
closure dos nós `carregar` e `renderizar`, nunca campo de `Estado`. `Send("analisar_lote",
lote)` entrega a lista de `Reclamacao` crua como input do nó, sem envolver em dict: é o
que faz `analise.analisar_lote(lote) -> dict` (Story 1.5) encaixar sem adaptação nenhuma.

`_rotear_apos_conservacao` desvia para `END` quando `len(analises) == 0`, antes de
`pontuar`/`agregar`/`renderizar` — AD-13 proíbe escrever HTML sobre zero análises. É
função de módulo (não closure) para ser testável direto, sem `.invoke()`, mesmo padrão
de `_fatiar`/`_despachar`/`_verificar_conservacao`.

**Sem `retry_policy`/`error_handler` no `add_node` de `analisar_lote` — decisão
revisada em 2026-08-08.** A intenção original (AD-9: repetição declarada no `add_node`,
nó sem laço de repetição próprio) esbarrou num limite empírico do LangGraph: testado
contra `langgraph==1.2.10`, `error_handler` roda mas não impede a exceção original de
abortar `.invoke()` inteiro quando há mais de uma task concorrente no mesmo step — que é
exatamente o que o fan-out via `Send` produz (testado em 6 configurações, todas com o
mesmo resultado; só nó único sem concorrência funciona). `analisar_lote` (Story 1.5)
absorve a própria falha de transporte com retry manual e nunca levanta — ver a docstring
de `plataforma/analise.py` para o registro completo da investigação e da divergência
ratificada.
"""

from pathlib import Path

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from plataforma import agregacao, analise, config, ingestao, pontuacao, relatorio
from plataforma.config import FAIXA_LOTE
from plataforma.estado import Estado, Reclamacao

_, _TETO_LOTE = FAIXA_LOTE  # 25 — mesma fonte que valida tamanho_lote (Story 1.2)


def _fatiar(reclamacoes: list[Reclamacao], tamanho_lote: int) -> list[list[Reclamacao]]:
    """Fatia em blocos de `tamanho_lote`, fundindo um resíduo de 1 ao bloco anterior.

    A faixa de `tamanho_lote` (2 a 25) já foi validada em `config.carregar()`
    (Story 1.2), mas isso não impede um resto de 1: `50 % 7 == 1`, e `7` está dentro da
    faixa. Só o fatiamento enxerga quantas linhas o CSV tinha, por isso a fusão do
    resíduo mora aqui e não na validação de configuração (AD-17, segunda cláusula).

    A fusão simples (resíduo + último lote) só é segura se não estourar o teto de 25 —
    "a validação recai sobre os lotes emitidos, não sobre a variável" (AD-17). Com
    `tamanho_lote=25` e resíduo de 1, fundir sem checar produziria um lote de 26,
    violando o próprio teto que este AD existe para proteger. Quando fundir estouraria,
    empresta um item do lote anterior para o resíduo em vez de simplesmente somar —
    todo lote final fica em `[2, teto]`, nunca 1, nunca acima do teto.
    """
    lotes = [reclamacoes[i:i + tamanho_lote] for i in range(0, len(reclamacoes), tamanho_lote)]
    if len(lotes) > 1 and len(lotes[-1]) == 1:
        residual = lotes.pop()
        if len(lotes[-1]) + 1 <= _TETO_LOTE:
            lotes[-1] = lotes[-1] + residual
        else:
            emprestado = lotes[-1].pop()
            lotes.append([emprestado] + residual)
    return lotes


def _despachar(reclamacoes: list[Reclamacao], tamanho_lote: int) -> list[Send]:
    """Um `Send` por lote, cada um carregando a lista de `Reclamacao` crua (AD-8).

    Não `Send("analisar_lote", {"lote": lote})` — `analisar_lote(lote)` espera a lista
    direto, e envolver em dict quebraria a chamada.
    """
    return [Send("analisar_lote", lote) for lote in _fatiar(reclamacoes, tamanho_lote)]


def _verificar_conservacao(estado: Estado) -> dict:
    """Conservação após o fan-out (AD-6): lidas == analisadas + soma das falhas.

    Roda entre `analisar_lote` e `_rotear_apos_conservacao`.
    """
    lidas = len(estado["reclamacoes"])
    analisadas = len(estado["analises"])
    afetadas = sum(len(f["ids"]) for f in estado["falhas"])
    assert lidas == analisadas + afetadas, (
        f"AD-6: {lidas} lidas != {analisadas} analisadas + {afetadas} em falhas"
    )
    return {}


def _rotear_apos_conservacao(estado: Estado) -> str:
    """Desvia para `END` se `analises` está vazio (AD-13) — zero análises não gera HTML.

    Função de módulo, não closure: testável direto com um `Estado` fabricado à mão,
    sem `.invoke()`, mesmo padrão de `_fatiar`/`_despachar`/`_verificar_conservacao`.
    """
    return "pontuar" if estado["analises"] else END


def construir_grafo(caminho: str, caminho_saida: str) -> CompiledStateGraph:
    """Monta o grafo: `carregar -> Send*N -> analisar_lote -> _verificar_conservacao
    -> [_rotear_apos_conservacao] -> pontuar -> agregar -> renderizar -> END`, ou
    direto para `END` se zero análises (AD-13).

    Fábrica, não singleton: `caminho` e `caminho_saida` viram closure dos nós
    `carregar`/`renderizar`, porque `Estado` não tem campo para nenhum dos dois.
    Nenhum `.invoke()` acontece aqui — quem invoca é `main.py` (Story 1.7). `pontuar`
    (Story 2.1), `agregar` (Story 2.2) e `renderizar` (Story 2.6) não precisam de
    `retry_policy`/`error_handler`: são síncronos, determinísticos, sem chamada de
    rede — nada de transporte para absorver. Uma falha de disco em `renderizar`
    (`OSError`) propaga através de `.invoke()` até o `except Exception` genérico que
    `main.py` já tem, sem máquina de erro nova.
    """
    def carregar(estado: Estado) -> dict:
        return {"reclamacoes": ingestao.carregar(caminho)}

    def despachar(estado: Estado) -> list[Send]:
        return _despachar(estado["reclamacoes"], config.carregar().tamanho_lote)

    def renderizar(estado: Estado) -> dict:
        # Escreve num arquivo temporário e troca com Path.replace (atômico no mesmo
        # sistema de arquivos): uma falha no meio da escrita (disco cheio, permissão
        # revogada) não deixa um relatório truncado no caminho final — o arquivo
        # anterior (se houver) permanece intacto até a troca ter sucesso.
        html = relatorio.renderizar(estado)
        destino = Path(caminho_saida)
        provisorio = destino.with_name(destino.name + ".tmp")
        provisorio.write_text(html, encoding="utf-8")
        provisorio.replace(destino)
        return {"caminho_html": str(destino)}

    grafo = StateGraph(Estado)
    grafo.add_node("carregar", carregar)
    grafo.add_node("analisar_lote", analise.analisar_lote)
    grafo.add_node("_verificar_conservacao", _verificar_conservacao)
    grafo.add_node("pontuar", pontuacao.pontuar)
    grafo.add_node("agregar", agregacao.agregar)
    grafo.add_node("renderizar", renderizar)

    grafo.add_edge(START, "carregar")
    grafo.add_conditional_edges("carregar", despachar)
    grafo.add_edge("analisar_lote", "_verificar_conservacao")
    grafo.add_conditional_edges("_verificar_conservacao", _rotear_apos_conservacao)
    grafo.add_edge("pontuar", "agregar")
    grafo.add_edge("agregar", "renderizar")
    grafo.add_edge("renderizar", END)

    return grafo.compile()
