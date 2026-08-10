"""Mede a fila que o pipeline de `plataforma/` realmente produz contra `docs/gabarito.csv`.

Não importa `baseline.py` nem `classificador.py`: M-1 exige provar o pipeline de
`plataforma/`, não reexecutar um script de medição de fase anterior que responde uma
pergunta diferente ("o LLM cru supera a linha de base?"). A fórmula de precisão/recall
é curta o bastante para duplicar sem acoplar os dois scripts.

`main()` exige `GOOGLE_API_KEY` real, rede, e gasta crédito — mesma natureza da AC7
manual da Story 1.7. Não é `tests/test_*.py` porque nenhum teste da suíte pode fazer
chamada de rede (AD-12); segue o mesmo padrão de `baseline.py`/`classificador.py`:
`autoteste()` cobre as funções puras sem rede, chamado no `if __name__ == "__main__":`.

Rode: `uv run python medir_fila.py`
"""

import csv
import os
import sys
import tempfile

from plataforma import grafo
from plataforma.estado import Pontuacao, Reclamacao
from plataforma.evidencia import _passa_checagem_individual

LIMIAR_PRECISAO = 0.95
LIMIAR_RECALL = 0.65
LIMIAR_OCUPACAO_FILA = 0.40

CAMINHO_CSV = "docs/reclamacoes_reclameaqui.csv"
CAMINHO_GABARITO = "docs/gabarito.csv"


def ler_gabarito(caminho: str) -> list[dict]:
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def comparar(pontuacoes: list[Pontuacao], gabarito: list[dict]) -> dict:
    """M-1: precisão/recall da fila do pipeline contra o gabarito, casamento por id.

    O universo de ids é o **gabarito** (Achado de revisão): um id do gabarito nunca
    analisado (`na_fila` ausente de `previsto`) conta como "fora da fila" — se o
    gabarito esperava `sim`, isso é um FN de verdade, não um id que desaparece da
    contagem. Sem isso, `nao_analisadas > 0` inflaria recall/precisão silenciosamente.
    """
    esperado = {
        linha["ID_Reclamacao"]: linha["fila_prioridade"].strip().lower() == "sim"
        for linha in gabarito
    }
    previsto = {p["id"]: p["na_fila"] for p in pontuacoes}

    tp = fp = fn = 0
    falsos_positivos, falsos_negativos = [], []
    for id_, espera_fila in esperado.items():
        prevista_fila = previsto.get(id_, False)
        if prevista_fila and espera_fila:
            tp += 1
        elif prevista_fila and not espera_fila:
            fp += 1
            falsos_positivos.append(id_)
        elif not prevista_fila and espera_fila:
            fn += 1
            falsos_negativos.append(id_)

    precisao = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "precisao": precisao, "recall": recall,
        "falsos_positivos": sorted(falsos_positivos),
        "falsos_negativos": sorted(falsos_negativos),
    }


def verificar_citacoes(pontuacoes: list[Pontuacao], reclamacoes_por_id: dict[str, Reclamacao]) -> tuple[int, int]:
    """M-2: (total, válidas) — reaproveita a regra de evidencia.py, não a reimplementa."""
    total = validas = 0
    for pontuacao in pontuacoes:
        texto = reclamacoes_por_id[pontuacao["id"]]["texto"]
        for motivo in pontuacao["motivos"]:
            if motivo["origem"] != "sinal":
                continue
            total += 1
            if _passa_checagem_individual(motivo["citacao"], texto):
                validas += 1
    return total, validas


def main() -> None:
    for caminho in (CAMINHO_CSV, CAMINHO_GABARITO):
        if not os.path.exists(caminho):
            raise SystemExit(
                f"encerrado: {caminho} não encontrado — rode a partir da raiz do repositório"
            )

    descritor, caminho_saida = tempfile.mkstemp(suffix=".html")
    os.close(descritor)
    try:
        estado = grafo.construir_grafo(CAMINHO_CSV, caminho_saida).invoke({})

        if not estado["analises"]:
            raise SystemExit(
                "encerrado: nenhuma reclamação analisada — medição não pode ser feita"
            )

        gabarito = ler_gabarito(CAMINHO_GABARITO)
        reclamacoes_por_id = {r["id"]: r for r in estado["reclamacoes"]}

        m1 = comparar(estado["pontuacoes"], gabarito)
        passou = m1["precisao"] >= LIMIAR_PRECISAO and m1["recall"] >= LIMIAR_RECALL
        print(f"M-1: TP={m1['tp']} FP={m1['fp']} FN={m1['fn']}  "
              f"precisão={m1['precisao']:.0%}  recall={m1['recall']:.0%}  "
              f"{'PASSOU' if passou else 'NÃO PASSOU'} "
              f"(critério: precisão≥{LIMIAR_PRECISAO:.0%}, recall≥{LIMIAR_RECALL:.0%})")
        if m1["falsos_positivos"]:
            print(f"  falsos positivos: {m1['falsos_positivos']}")
        if m1["falsos_negativos"]:
            print(f"  falsos negativos: {m1['falsos_negativos']}")

        agregados = estado["agregados"]
        ocupacao = agregados["ocupacao_fila"]
        alerta = (f" — ALERTA: fila deixou de ordenar (>{LIMIAR_OCUPACAO_FILA:.0%})"
                  if ocupacao > LIMIAR_OCUPACAO_FILA else "")
        print(f"CM-1: ocupação da fila = {ocupacao:.0%}{alerta}")

        propostos, derrubados = agregados["codigos_propostos"], agregados["codigos_derrubados"]
        nota_cm2 = (" — zero constante é indistinguível de mecanismo morto"
                    if propostos and derrubados == 0 else "")
        taxa_cm2 = derrubados / propostos if propostos else 0.0
        print(f"CM-2: códigos derrubados = {derrubados}/{propostos} ({taxa_cm2:.0%}){nota_cm2}")

        print(f"CM-3: taxa de produto não nomeado = {agregados['taxa_produto_nao_nomeado']:.0%}")
        print(f"CM-4: não analisadas = {agregados['nao_analisadas']}")

        total, validas = verificar_citacoes(estado["pontuacoes"], reclamacoes_por_id)
        print(f"M-2: citações válidas = {validas}/{total}")
    finally:
        # Resíduo da execução real, não o entregável do operador (Story 2.6) — não fica
        # órfão no diretório temporário do SO.
        if os.path.exists(caminho_saida):
            os.remove(caminho_saida)


def autoteste():
    pontuacoes = [
        Pontuacao(id="R1", pontos=3, na_fila=True, motivos=[]),   # TP
        Pontuacao(id="R2", pontos=3, na_fila=True, motivos=[]),   # FP
        Pontuacao(id="R3", pontos=0, na_fila=False, motivos=[]),  # FN
        Pontuacao(id="R4", pontos=0, na_fila=False, motivos=[]),  # TN
        # R5 nunca aparece em `pontuacoes` — simula reclamação não analisada
        # (nao_analisadas > 0). O gabarito esperava fila; sem o fix, isso sumia da
        # contagem de FN em vez de contar como erro (achado de revisão).
    ]
    gabarito = [
        {"ID_Reclamacao": "R1", "fila_prioridade": "sim"},
        {"ID_Reclamacao": "R2", "fila_prioridade": "nao"},
        {"ID_Reclamacao": "R3", "fila_prioridade": "sim"},
        {"ID_Reclamacao": "R4", "fila_prioridade": "nao"},
        {"ID_Reclamacao": "R5", "fila_prioridade": "sim"},
    ]
    m = comparar(pontuacoes, gabarito)
    assert (m["tp"], m["fp"], m["fn"]) == (1, 1, 2)
    assert m["precisao"] == 0.5
    assert m["recall"] == 1 / 3
    assert m["falsos_positivos"] == ["R2"]
    assert m["falsos_negativos"] == ["R3", "R5"], \
        "id nunca analisado (R5) precisa contar como falso negativo, não desaparecer"

    reclamacao = Reclamacao(id="R1", data="2026-01-01", empresa="E", titulo="T",
                             texto="o produto chegou quebrado e ninguém resolveu nada",
                             cidade_estado="SP", status="Não respondida")
    valida = Pontuacao(id="R1", pontos=3, na_fila=True, motivos=[
        {"origem": "sinal", "citacao": "o produto chegou quebrado e ninguém resolveu", "rotulo": "dinheiro_retido"},
        {"origem": "atributo", "citacao": None, "rotulo": "Status: Respondida (-1)"},
    ])
    invalida = Pontuacao(id="R1", pontos=3, na_fila=True, motivos=[
        {"origem": "sinal", "citacao": "frase que não está no texto original", "rotulo": "dinheiro_retido"},
    ])
    total, validas = verificar_citacoes([valida], {"R1": reclamacao})
    assert (total, validas) == (1, 1), "motivo de origem atributo não deveria contar em M-2"
    total, validas = verificar_citacoes([invalida], {"R1": reclamacao})
    assert (total, validas) == (1, 0), "verificar_citacoes precisa detectar citação inventada"

    print("autoteste ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    autoteste()
    main()
