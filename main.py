"""CLI do pipeline: roda o grafo sobre um CSV, escreve o relatório e imprime as quatro
contagens do operador mais o caminho final do arquivo.

`analisar_lote` (Story 1.6) nunca deixa exceção escapar — toda falha de transporte,
inclusive credencial ausente, já chega aqui como `Falha` no estado final, nunca como
exceção que interrompeu o `invoke()` no meio. Isso é o que a Story 1.6 garante, mas o
`try/except` em `main()` continua sendo a rede de segurança real: se essa garantia
algum dia regredir, ou se `carregar`/`config`/`renderizar` levantarem (todos ainda são
síncronos e podem), este módulo converte em saída limpa de processo em vez de traceback
cru.

O cheque de arquivo de saída existente (FR-4) roda **antes** de `.invoke()` — o nome do
arquivo (`relatorio-<csv>-<data-de-hoje>.html`) é 100% calculável sem ler uma linha do
CSV, então a mesma disciplina de "validar antes de gastar" que `config.py`/`ingestao.py`
já aplicam vale aqui: por que gastar uma chamada paga para só então descobrir que o
arquivo de saída já existe?

Rode: `uv run python main.py <caminho-do-csv> [--sobrescrever]`
"""

import datetime
import sys
from pathlib import Path

from plataforma import grafo
from plataforma.estado import Analise

_FLAG_SOBRESCREVER = "--sobrescrever"


def _ler_argumento(argv: list[str]) -> tuple[str, bool]:
    """Devolve `(caminho_csv, sobrescrever)` ou levanta com a mensagem de uso (AC1, FR-4)."""
    nome = argv[0] if argv else "main.py"
    uso = f"uso: uv run python {nome} <caminho-do-csv> [{_FLAG_SOBRESCREVER}]"
    if len(argv) == 2 and argv[1] != _FLAG_SOBRESCREVER:
        return argv[1], False
    if len(argv) == 3 and argv[2] == _FLAG_SOBRESCREVER:
        return argv[1], True
    raise SystemExit(uso)


def _nome_saida(caminho_csv: str) -> Path:
    """`relatorio-<nome-do-csv>-<data-ISO>.html`, ao lado do CSV de entrada (AD-15).

    Data em ISO (`AAAA-MM-DD`), nunca no formato pt-BR de `relatorio._data_br`
    (`DD/MM/AAAA`) — a barra quebraria o caminho do arquivo.
    """
    origem = Path(caminho_csv)
    data = datetime.date.today().isoformat()
    return origem.with_name(f"relatorio-{origem.stem}-{data}.html")


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
    caminho, sobrescrever = _ler_argumento(sys.argv)
    try:
        # _nome_saida e o cheque de existência entram no try também: um caminho de CSV
        # degenerado (ex.: terminando em separador) levantaria ValueError cru de
        # Path.with_name antes desta correção — mesma disciplina de nunca deixar
        # traceback cru chegar ao operador que o resto deste módulo já segue. Todo o
        # cálculo das contagens também fica dentro do try: se `invoke()` devolvesse um
        # estado incompleto (não deveria, mas nada garante isso em tempo de compilação
        # de um TypedDict), o acesso às chaves cairia no mesmo `except` em vez de
        # vazar um KeyError cru.
        caminho_saida = _nome_saida(caminho)
        if caminho_saida.exists() and not sobrescrever:
            raise SystemExit(f"encerrado: arquivo de saída já existe: {caminho_saida}")
        estado = grafo.construir_grafo(caminho, str(caminho_saida)).invoke({})
        lidas = len(estado["reclamacoes"])
        analisadas = len(estado["analises"])
        falhas = estado["falhas"]
        nao_analisadas = sum(len(f["ids"]) for f in falhas)
        derrubados = _contar_codigos_derrubados(estado["analises"])
    except Exception as erro:
        # `ValueError` vem de config.py/ingestao.py (Stories 1.2/1.3). `FileNotFoundError`
        # vem de um caminho de CSV inexistente — o erro mais comum na prática, não só
        # "infraestrutura imprevista". `analisar_lote` (Story 1.6) nunca levanta, então
        # nada daqui vem de lá. `OSError` de `renderizar` (disco cheio, permissão) cai
        # aqui também — mesma rede de segurança, sem máquina de erro nova (Story 2.6).
        raise SystemExit(f"encerrado: {erro}") from None

    if analisadas == 0:
        raise SystemExit(_mensagem_zero_analises(falhas))

    print(f"{'lidas':22} {lidas:>5}")
    print(f"{'analisadas':22} {analisadas:>5}")
    print(f"{'não analisadas':22} {nao_analisadas:>5}  ({len(falhas)} evento(s) de falha)")
    print(f"{'códigos derrubados':22} {derrubados:>5}")
    print(f"{'arquivo gerado':22} {estado['caminho_html']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")  # SystemExit imprime aqui — os acentos das
    # mensagens de causa (config.py, ingestao.py) quebrariam sem isto no console do Windows
    main()
