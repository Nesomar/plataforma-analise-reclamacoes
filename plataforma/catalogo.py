"""Fonte única dos códigos de sinal, do grupo saturado e dos termos genéricos de produto.

As definições não são comentário: são dado que `analise.py` injeta no prompt. Definição
escrita com exemplo dentro do prompt é o fator de maior impacto medido na acurácia
(risk-signals.md), por isso o texto vive aqui e não espalhado em f-string de prompt.
Os pesos ficam em `pontuacao.py`, com estas mesmas strings como chave.
"""

import unicodedata
from types import MappingProxyType

# Saturado: um ou os dois códigos valem 3 pontos uma única vez. Ambos nomeiam a
# mesma coisa — o cliente anunciando que vai acionar seus direitos —, então somar
# duplicaria uma parcela só. Declarado como dado para pontuacao.py ler sem repetir a regra.
GRUPO_SINAL_A = ("ameaca_explicita", "lei_citada")

_CATALOGO = {
    # Texto de classificador.py:50-64, prosa validada contra o gabarito humano. Duas
    # cláusulas foram acrescentadas a partir de risk-signals.md:35, que é a fonte
    # canônica e é mais específica que o prompt original: "ou contra a oferta" e
    # "sem justificativa". Fora essas duas, o conteúdo é o que foi medido — inclusive
    # o SOMENTE, que é o operador de exclusividade da regra.
    "dinheiro_retido": {
        "definicao": (
            "Marque SOMENTE se a empresa está com dinheiro que deveria estar com o "
            "cliente. Casos que valem: estorno prometido e não feito; cobrança de algo "
            "que o cliente não contratou ou contra a oferta; conta, saldo ou valor "
            "bloqueado sem justificativa; produto pago e não entregue; produto pago que "
            "chegou quebrado ou defeituoso e a empresa se recusa a trocar, consertar ou "
            "devolver o dinheiro — não importa de quem a empresa diz que é a culpa, o "
            "cliente pagou e ficou sem produto e sem dinheiro; assinatura que o cliente "
            "tenta cancelar e segue sendo cobrada. "
            "NÃO vale para: serviço de má qualidade, lentidão, instabilidade, mau "
            "atendimento, atraso sem valor preso, produto danificado quando o cliente "
            "não pede dinheiro nem troca, propaganda enganosa sem cobrança indevida. "
            "O teste é simples: existe uma quantia do cliente parada na empresa agora, "
            "ou saindo do bolso dele agora?"
        ),
        "exemplo": "cancelei a compra há 40 dias e até hoje não recebi o estorno de R$ 890",
    },
    # Os quatro códigos abaixo têm descrição de uma linha em risk-signals.md e nada
    # mais. A definição reproduz essa linha; só o exemplo é escrito aqui. Restringir
    # o escopo por conta própria move M-1 sem medição — a definição vai para o prompt.
    "registro_contraditorio": {
        "definicao": (
            "O registro da empresa afirma um fato que o cliente contesta apresentando "
            "protocolo ou rastreio."
        ),
        "exemplo": "consta como entregue no dia 12, mas o rastreio BR8842 mostra devolvido ao remetente",
    },
    "dano_continuado": {
        "definicao": (
            "O prejuízo segue ocorrendo enquanto o caso não é resolvido — cobrança que "
            "se repete a cada ciclo, serviço pago e indisponível de forma contínua."
        ),
        "exemplo": "já é o terceiro mês que a mensalidade é debitada mesmo com o plano cancelado",
    },
    "prazo_estourado": {
        "definicao": "Prazo legal ou prometido pela própria empresa já vencido.",
        "exemplo": "prometeram solução em 5 dias úteis, já se passaram 21 dias e nada",
    },
    # Texto de classificador.py:69-73, incluindo a exclusão de retórica, que é parte
    # da regra medida e não acréscimo.
    "ameaca_explicita": {
        "definicao": (
            "O cliente anuncia que vai acionar seus direitos — processo, advogado, "
            "Procon, juizado, ação judicial. Indignação não conta: 'é um absurdo', "
            "'isso é fraude', 'exijo' são retórica, não anúncio de ação."
        ),
        "exemplo": "se não for resolvido em 5 dias vou procurar meus direitos no Procon",
    },
    "lei_citada": {
        "definicao": (
            "O cliente invoca norma de defesa do consumidor, artigo específico, ou pede "
            "ressarcimento em dobro."
        ),
        "exemplo": "pelo artigo 42 do CDC tenho direito à devolução em dobro do valor cobrado",
    },
}

# Só leitura: o conteúdo alimenta o prompt, e uma mutação em runtime alteraria a
# definição que decide a classificação sem deixar rastro no diff.
CATALOGO = MappingProxyType({k: MappingProxyType(v) for k, v in _CATALOGO.items()})

# ponytail: exatamente os quatro termos que a medição de 2026-08-06 encontrou (18 de
# 50 identificações caíram em substantivos que não nomeiam produto algum). A lista
# cresce por medição, não por palpite — cada termo acrescentado sem evidência infla
# CM-3 e muda um número que o PRD reporta.
TERMOS_GENERICOS = frozenset({"fatura", "compra", "produto", "serviço"})


def nao_nomeia_produto(produto: str | None) -> bool:
    """Responde CM-3: o campo não nomeia produto algum — nulo, vazio ou genérico.

    A regra de comparação vive junto da lista canônica porque `produto` vem do modelo
    em texto livre: sem uma normalização única, "Produto", "produtos" e a forma NFD de
    "serviço" escapam da lista e cada consumidor inventa a sua, movendo um número que
    o PRD reporta. Vazio e só-espaços contam como não nomeado — não são nulos nem
    genéricos, e sem isso escapariam das duas metades de CM-3.
    """
    if produto is None or not produto.strip():
        return True
    termo = unicodedata.normalize("NFC", produto).strip().lower()
    # ponytail: plural só por 's' final, que cobre os quatro termos medidos. Se a
    # lista crescer com plural irregular, trocar por lematização.
    return termo in TERMOS_GENERICOS or termo.rstrip("s") in TERMOS_GENERICOS
