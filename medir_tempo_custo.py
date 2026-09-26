"""Mede tempo e custo de uma execução real do pipeline de `plataforma/` (Story 3.2).

O pipeline de `plataforma/` não tem cache — `ARCHITECTURE-SPINE.md` lista cache em
"Deferred". Q-8/AC1 falam do cache de `classificador.py` (`.cache_analises.json`), um
script diferente; não há nada para desligar aqui. `main()` exige `GOOGLE_API_KEY` real,
rede, e gasta crédito — mesma natureza da AC7 manual da Story 1.7. Não é `tests/test_*.py`
(AD-12); segue o padrão de `medir_fila.py`/`baseline.py`/`classificador.py`.

Rode: `uv run python medir_tempo_custo.py`
"""

import os
import sys
import tempfile
import time

from plataforma import analise, config, grafo

TETO_TEMPO_S = 120


def main() -> None:
    caminho_csv = "docs/reclamacoes_reclameaqui.csv"
    if not os.path.exists(caminho_csv):
        raise SystemExit(f"encerrado: {caminho_csv} não encontrado — rode a partir da raiz do repositório")

    analise.resetar_metricas()
    descritor, caminho_saida = tempfile.mkstemp(suffix=".html")
    os.close(descritor)
    try:
        inicio = time.perf_counter()
        estado = grafo.construir_grafo(caminho_csv, caminho_saida).invoke({})
        tempo_total = time.perf_counter() - inicio

        dentro_do_teto = tempo_total <= TETO_TEMPO_S
        print(f"Tempo total: {tempo_total:.1f}s  "
              f"{'DENTRO' if dentro_do_teto else 'ACIMA'} do teto de {TETO_TEMPO_S}s")

        metricas = analise.ler_metricas()
        tokens_total = metricas["tokens_entrada"] + metricas["tokens_saida"]
        print(f"Chamadas ao modelo: {metricas['chamadas']}  "
              f"tokens entrada={metricas['tokens_entrada']} "
              f"saída={metricas['tokens_saida']} total={tokens_total}")

        if "reclamacoes" not in estado:
            raise SystemExit("encerrado: estado sem 'reclamacoes' — pipeline não completou como esperado")

        lotes_esperados = len(grafo._despachar(estado["reclamacoes"], config.carregar().tamanho_lote))
        igual = lotes_esperados == metricas["chamadas"]
        print(f"Lotes emitidos: {lotes_esperados}  "
              f"{'IGUAL' if igual else 'DIVERGENTE'} às chamadas reais "
              f"({metricas['chamadas']}) — divergência indica retry de transporte (AD-9)")

        print("Nota: confira tokens/chamadas acima contra o tier gratuito vigente da API "
              "do Gemini — preço e limite não são dado deste repositório e mudam sem aviso.")
    finally:
        try:
            if os.path.exists(caminho_saida):
                os.remove(caminho_saida)
        except OSError as erro:
            print(f"aviso: não foi possível remover o arquivo temporário {caminho_saida}: {erro}")


def autoteste():
    analise.resetar_metricas()
    assert analise.ler_metricas() == {"chamadas": 0, "tokens_entrada": 0, "tokens_saida": 0}

    analise._metricas["chamadas"] += 1
    analise._metricas["tokens_entrada"] += 10
    lida = analise.ler_metricas()
    assert lida == {"chamadas": 1, "tokens_entrada": 10, "tokens_saida": 0}
    lida["chamadas"] = 99  # mutar a cópia não pode afetar o original
    assert analise.ler_metricas()["chamadas"] == 1, "ler_metricas precisa devolver cópia, não referência"

    analise.resetar_metricas()
    assert analise.ler_metricas() == {"chamadas": 0, "tokens_entrada": 0, "tokens_saida": 0}

    print("autoteste ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    autoteste()
    main()
