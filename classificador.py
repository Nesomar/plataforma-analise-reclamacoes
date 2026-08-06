"""Classificador com Gemini — mede se o LLM supera a linha de base determinística.

Diferença deliberada em relação a baseline.py: o modelo vê **apenas o texto livre**
da reclamação, nunca o título. O título desta base é canônico (18 valores fixos) e
entrega a resposta; base real não tem isso. Ganhar sem o título é ganhar de verdade.

Rode: `python classificador.py`
"""

import csv
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from baseline import DOCS, avalia, ler

MODELO = "gemini-3.6-flash"  # pinado de propósito: alias móvel invalida comparação de F1
TAMANHO_LOTE = 10
CACHE = Path(__file__).parent / ".cache_analises.json"


class Analise(BaseModel):
    id: str
    sentimento: str  # positivo | neutro | negativo
    produto: str | None
    dinheiro_retido: bool
    evidencia_dinheiro: str | None
    ameaca_explicita: bool
    evidencia_ameaca: str | None


class Lote(BaseModel):
    analises: list[Analise]


INSTRUCAO = """Você analisa reclamações de consumidores brasileiros.

Para cada reclamação, devolva:

- sentimento: "positivo", "neutro" ou "negativo".
- produto: o produto ou serviço mencionado no texto, em uma ou duas palavras.
  null se o texto não permitir identificar.

- dinheiro_retido: true SOMENTE se a empresa está com dinheiro que deveria estar
  com o cliente. Casos que valem:
    * estorno prometido e não feito;
    * cobrança de algo que o cliente não contratou;
    * conta, saldo ou valor bloqueado;
    * produto pago e não entregue;
    * produto pago que chegou quebrado ou defeituoso e a empresa se recusa a
      trocar, consertar ou devolver o dinheiro — não importa de quem a empresa
      diz que é a culpa, o cliente pagou e ficou sem produto e sem dinheiro;
    * assinatura que o cliente tenta cancelar e segue sendo cobrada.
  NÃO vale para: serviço de má qualidade, lentidão, instabilidade, mau
  atendimento, atraso sem valor preso, produto danificado quando o cliente não
  pede dinheiro nem troca, propaganda enganosa sem cobrança indevida.
  O teste é simples: existe uma quantia do cliente parada na empresa agora, ou
  saindo do bolso dele agora?

- evidencia_dinheiro: o trecho LITERAL do texto que sustenta dinheiro_retido.
  Copie caractere por caractere do original. null quando dinheiro_retido for false.

- ameaca_explicita: true SOMENTE se o cliente anuncia que vai acionar seus
  direitos — processo, advogado, Procon, juizado, ação judicial.
  Indignação não conta: "é um absurdo", "isso é fraude", "exijo" são retórica,
  não anúncio de ação.

- evidencia_ameaca: trecho LITERAL que sustenta ameaca_explicita, ou null.

Nunca invente citação. Se não houver trecho literal que sustente o sinal,
marque o sinal como false."""


def analisa_lote(cliente, reclamacoes):
    entrada = [{"id": r["ID_Reclamacao"], "texto": r["Descricao"]} for r in reclamacoes]
    resposta = cliente.models.generate_content(
        model=MODELO,
        contents=json.dumps(entrada, ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCAO,
            response_mime_type="application/json",
            response_schema=Lote,
            temperature=0,
        ),
    )
    return {a.id: a.model_dump() for a in resposta.parsed.analises}


def valida_evidencia(analise, texto):
    """Derruba o sinal cuja citação não existe no texto original. Determinístico."""
    derrubados = 0
    for sinal, campo in [("dinheiro_retido", "evidencia_dinheiro"),
                         ("ameaca_explicita", "evidencia_ameaca")]:
        if not analise[sinal]:
            continue
        citacao = (analise[campo] or "").strip()
        if not citacao or citacao not in texto:
            analise[sinal] = False
            analise[campo] = None
            derrubados += 1
    return derrubados


def pontua(analise, reclamacao, filtrar_respondida=False):
    score = 3 * analise["dinheiro_retido"] + 3 * analise["ameaca_explicita"]
    if filtrar_respondida and reclamacao["Status"] == "Respondida":
        score -= 1
    return score


def classifica(reclamacoes, usar_cache=True):
    if usar_cache and CACHE.exists():
        analises = json.loads(CACHE.read_text(encoding="utf-8"))
        if set(analises) == {r["ID_Reclamacao"] for r in reclamacoes}:
            print(f"cache: {len(analises)} análises reaproveitadas (0 chamadas)")
            return analises, 0

    load_dotenv()
    os.environ.setdefault("GOOGLE_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    cliente = genai.Client()

    analises, derrubados = {}, 0
    lotes = [reclamacoes[i:i + TAMANHO_LOTE] for i in range(0, len(reclamacoes), TAMANHO_LOTE)]
    for n, lote in enumerate(lotes, 1):
        recebidas = analisa_lote(cliente, lote)
        faltando = [r["ID_Reclamacao"] for r in lote if r["ID_Reclamacao"] not in recebidas]
        if faltando:
            print(f"  lote {n}: {len(faltando)} id(s) sem resposta -> {faltando}")
        for r in lote:
            a = recebidas.get(r["ID_Reclamacao"])
            if a is None:
                continue
            derrubados += valida_evidencia(a, r["Descricao"])
            analises[r["ID_Reclamacao"]] = a
        print(f"  lote {n}/{len(lotes)} · {len(analises)} analisadas")

    print(f"sinais derrubados por citação inválida: {derrubados}")
    CACHE.write_text(json.dumps(analises, ensure_ascii=False, indent=1), encoding="utf-8")
    return analises, derrubados


def main():
    reclamacoes = ler(DOCS / "reclamacoes_reclameaqui.csv")
    gabarito = ler(DOCS / "gabarito.csv")
    analises, _ = classifica(reclamacoes)

    faltando = [r for r in reclamacoes if r["ID_Reclamacao"] not in analises]
    if faltando:
        print(f"\nAVISO: {len(faltando)} reclamações sem análise, contadas como fora da fila")

    print(f"\n{'regra':22} {'TP':>3} {'FP':>3} {'FN':>3}  precisão  recall    F1")
    for rotulo, filtro in [("LLM", False), ("LLM + Status", True)]:
        previsto = {r["ID_Reclamacao"]:
                    r["ID_Reclamacao"] in analises
                    and pontua(analises[r["ID_Reclamacao"]], r, filtro) >= 3
                    for r in reclamacoes}
        m = mede(previsto, gabarito)
        print(f"{rotulo:22} {m['tp']:3} {m['fp']:3} {m['fn']:3}  "
              f"{m['precisao']:7.0%}  {m['recall']:6.0%}  {m['f1']:.2f}")

    for rotulo, filtro in [("baseline", False), ("baseline + Status", True)]:
        m = avalia(reclamacoes, gabarito, filtro)
        print(f"{rotulo:22} {m['tp']:3} {m['fp']:3} {m['fn']:3}  "
              f"{m['precisao']:7.0%}  {m['recall']:6.0%}  {m['f1']:.2f}")

    ameacas = sum(a["ameaca_explicita"] for a in analises.values())
    sem_produto = sum(a["produto"] is None for a in analises.values())
    sent = {}
    for a in analises.values():
        sent[a["sentimento"]] = sent.get(a["sentimento"], 0) + 1
    print(f"\nameaça explícita: {ameacas}/{len(analises)}  ·  "
          f"sem produto: {sem_produto}  ·  sentimento: {sent}")


def mede(previsto, gabarito):
    esperado = {g["ID_Reclamacao"]: g["fila_prioridade"] == "sim" for g in gabarito}
    tp = sum(1 for i, p in previsto.items() if p and esperado[i])
    fp = sum(1 for i, p in previsto.items() if p and not esperado[i])
    fn = sum(1 for i, p in previsto.items() if not p and esperado[i])
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precisao": pr, "recall": rc,
            "f1": 2 * pr * rc / (pr + rc) if pr + rc else 0.0}


def autoteste():
    a = {"dinheiro_retido": True, "evidencia_dinheiro": "não estornaram",
         "ameaca_explicita": True, "evidencia_ameaca": "vou processar"}
    assert valida_evidencia(a, "eles não estornaram nada") == 1
    assert a["dinheiro_retido"] is True, "citação existente deve sobreviver"
    assert a["ameaca_explicita"] is False, "citação inventada deve cair"
    assert a["evidencia_ameaca"] is None
    print("autoteste ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    autoteste()
    main()
