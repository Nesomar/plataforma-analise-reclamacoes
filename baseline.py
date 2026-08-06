"""Linha de base determinística — classifica pela categoria do título, sem LLM.

É a barra que o pipeline com Gemini precisa superar para justificar existir.
Rode direto: `python baseline.py`
"""

import csv
import sys
from pathlib import Path

DOCS = Path(__file__).parent / "docs"

# Categorias em que a empresa está com dinheiro do cliente.
# Extraídas do gabarito humano (docs/gabarito.csv), não escolhidas a priori.
# ponytail: match exato de título — teto é esta base; texto livre real exigiria o LLM.
CATEGORIAS_DINHEIRO = {
    "Demora no estorno do cancelamento",
    "Bloqueio de conta sem justificativa",
    "Cobrança indevida no cartão de crédito",
    "Produto não entregue e passou do prazo",
    "Produto veio com defeito e não trocam",
    # incluída na revisão do gabarito v2: cliente segue sendo cobrado por
    # assinatura que tenta cancelar — é dinheiro saindo agora
    "Não consigo cancelar assinatura",
}


def ler(caminho):
    """CSV do projeto: separador ';' e BOM UTF-8."""
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def prioriza(reclamacao, filtrar_respondida=False):
    """True se a reclamação entra na fila de prioridade.

    filtrar_respondida ativa o modificador de Status: dentro da categoria certa,
    'Respondida' derruba a prioridade. Zera o falso positivo, custa recall.
    """
    if reclamacao["Titulo"] not in CATEGORIAS_DINHEIRO:
        return False
    return not (filtrar_respondida and reclamacao["Status"] == "Respondida")


def avalia(reclamacoes, gabarito, filtrar_respondida=False):
    esperado = {g["ID_Reclamacao"]: g["fila_prioridade"] == "sim" for g in gabarito}
    tp = fp = fn = 0
    for r in reclamacoes:
        previu = prioriza(r, filtrar_respondida)
        real = esperado[r["ID_Reclamacao"]]
        tp += previu and real
        fp += previu and not real
        fn += not previu and real
    precisao = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precisao": precisao, "recall": recall, "f1": f1}


def main():
    reclamacoes = ler(DOCS / "reclamacoes_reclameaqui.csv")
    gabarito = ler(DOCS / "gabarito.csv")
    marcadas = sum(g["fila_prioridade"] == "sim" for g in gabarito)
    print(f"{len(reclamacoes)} reclamações · {marcadas} na fila do gabarito "
          f"({marcadas / len(reclamacoes):.0%})\n")

    for rotulo, filtro in [("categoria", False), ("categoria + Status", True)]:
        m = avalia(reclamacoes, gabarito, filtro)
        print(f"{rotulo:20} TP={m['tp']:2} FP={m['fp']:2} FN={m['fn']:2}  "
              f"precisão={m['precisao']:.0%}  recall={m['recall']:.0%}  F1={m['f1']:.2f}")

    print("\nM-1 do PRD: precisão ≥ 95% com recall ≥ 65%. Só 'categoria + Status' atende.")


def autoteste():
    reclamacoes = ler(DOCS / "reclamacoes_reclameaqui.csv")
    gabarito = ler(DOCS / "gabarito.csv")

    assert len(reclamacoes) == len(gabarito) == 50
    ids = [r["ID_Reclamacao"] for r in reclamacoes]
    assert len(set(ids)) == 50, "ID_Reclamacao precisa ser único"
    assert {g["ID_Reclamacao"] for g in gabarito} == set(ids), "gabarito e base divergem"

    base = avalia(reclamacoes, gabarito)
    filtrado = avalia(reclamacoes, gabarito, filtrar_respondida=True)

    # M-1 do PRD: precisão ≥ 95% com piso de recall em 65%. Assimétrica de
    # propósito — falso positivo custa mais que falso negativo, e F1 (simétrico)
    # reprovava justamente a regra que não erra.
    assert filtrado["precisao"] >= 0.95, f"M-1: precisão {filtrado['precisao']:.1%}"
    assert filtrado["recall"] >= 0.65, f"M-1: recall {filtrado['recall']:.1%}"
    assert not base["precisao"] >= 0.95, "a regra sem filtro de Status não deveria atender M-1"
    assert filtrado["recall"] < base["recall"], "o filtro deveria custar recall"

    print("autoteste ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # console do Windows não é UTF-8 por padrão
    autoteste()
    print()
    main()
