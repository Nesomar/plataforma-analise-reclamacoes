"""CLI do pipeline: roda o grafo sobre um CSV e imprime as quatro contagens do operador.

`analisar_lote` (Story 1.6) nunca deixa exceção escapar — toda falha de transporte,
inclusive credencial ausente, já chega aqui como `Falha` no estado final, nunca como
exceção que interrompeu o `invoke()` no meio. Isso é o que a Story 1.6 garante, mas o
`try/except` em `main()` continua sendo a rede de segurança real: se essa garantia
algum dia regredir, ou se `carregar`/`config` levantarem (os dois ainda são síncronos e
podem), este módulo converte em saída limpa de processo em vez de traceback cru.

Rode: `uv run python main.py <caminho-do-csv>`
"""

import sys

from plataforma import grafo
from plataforma.estado import Analise


def _ler_argumento(argv: list[str]) -> str:
    """Devolve o caminho do CSV ou levanta com a mensagem de uso (AC1)."""
    if len(argv) != 2:
        nome = argv[0] if argv else "main.py"
        raise SystemExit(f"uso: uv run python {nome} <caminho-do-csv>")
    return argv[1]


def _mensagem_zero_analises(falhas: list) -> str:
    """Monta a causa nomeada quando nenhuma reclamação foi analisada (AC5, AC6).

    `falhas` é garantidamente não-vazia quando esta função é chamada: AD-6
    (`_verificar_conservacao`) assegura `lidas == analisadas + afetadas`, e `lidas == 0`
    já teria encerrado em `ingestao.carregar` antes de chegar aqui — por isso nenhum
    fallback para lista vazia.
    """
    causas = sorted({f["causa"] for f in falhas})
    return (
        f"encerrado: nenhuma reclamação analisada — {len(falhas)} evento(s) de falha, "
        f"causa(s): {'; '.join(causas)}"
    )


def _contar_codigos_derrubados(analises: list[Analise]) -> int:
    """Códigos distintos derrubados, por reclamação, somados entre reclamações (AD-2).

    Não deduplica entre reclamações: se `dinheiro_retido` foi derrubado em 5
    reclamações diferentes, conta 5 — é a taxa que CM-2 mede, não um conjunto único de
    códigos ruins no catálogo.
    """
    total = 0
    for analise in analises:
        codigos_invalidos = {s["codigo"] for s in analise["sinais"] if not s["valida"]}
        total += len(codigos_invalidos)
    return total


def main() -> None:
    caminho = _ler_argumento(sys.argv)
    try:
        # Todo o cálculo das contagens fica dentro do try: se `invoke()` devolvesse um
        # estado incompleto (não deveria, mas nada garante isso em tempo de compilação
        # de um TypedDict), o acesso às chaves cairia no mesmo `except` em vez de
        # vazar um KeyError cru — mesma disciplina de nunca deixar traceback cru chegar
        # ao operador que o resto deste módulo já segue.
        estado = grafo.construir_grafo(caminho).invoke({})
        lidas = len(estado["reclamacoes"])
        analisadas = len(estado["analises"])
        falhas = estado["falhas"]
        nao_analisadas = sum(len(f["ids"]) for f in falhas)
        derrubados = _contar_codigos_derrubados(estado["analises"])
    except Exception as erro:
        # `ValueError` vem de config.py/ingestao.py (Stories 1.2/1.3). `FileNotFoundError`
        # vem de um caminho de CSV inexistente — o erro mais comum na prática, não só
        # "infraestrutura imprevista". `analisar_lote` (Story 1.6) nunca levanta, então
        # nada daqui vem de lá.
        raise SystemExit(f"encerrado: {erro}") from None

    if analisadas == 0:
        raise SystemExit(_mensagem_zero_analises(falhas))

    print(f"{'lidas':22} {lidas:>5}")
    print(f"{'analisadas':22} {analisadas:>5}")
    print(f"{'não analisadas':22} {nao_analisadas:>5}  ({len(falhas)} evento(s) de falha)")
    print(f"{'códigos derrubados':22} {derrubados:>5}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")  # SystemExit imprime aqui — os acentos das
    # mensagens de causa (config.py, ingestao.py) quebrariam sem isto no console do Windows
    main()
