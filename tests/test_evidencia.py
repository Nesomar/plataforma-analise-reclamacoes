"""Cobre `verificar`: checagem individual (substring + piso de 5 palavras) e o
agrupamento por `codigo` que é o núcleo da story (AD-2).

Todo `texto` e `Sinal` é fabricado à mão neste arquivo — nunca lê
`docs/reclamacoes_reclameaqui.csv` nem chama o modelo (AD-12). O caso mais importante
é `test_uma_citacao_fabricada_derruba_o_par_do_mesmo_codigo`: prova que checagem por
`Sinal` isolado não basta, é preciso agrupar por código antes de decidir `valida`.
"""

from plataforma.estado import Sinal
from plataforma import evidencia

TEXTO = (
    "Cancelei a compra há 40 dias e até hoje não recebi o estorno de R$ 890 "
    "prometido pelo atendimento."
)


def sinal(codigo, citacao, valida=False):
    return Sinal(codigo=codigo, citacao=citacao, valida=valida)


def test_citacao_valida_substring_com_cinco_palavras_ou_mais_passa():
    sinais = [sinal("dinheiro_retido", "até hoje não recebi o estorno")]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert resultado[0]["valida"] is True, "AC1: citação real de 6 palavras reprovou"


def test_citacao_fabricada_nao_e_substring_reprova():
    sinais = [sinal("dinheiro_retido", "a empresa confessou fraude por escrito ontem")]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert resultado[0]["valida"] is False, "AC2: citação inventada não deveria passar"


def test_uma_citacao_fabricada_derruba_o_par_do_mesmo_codigo():
    # AD-2, o teste central desta story: dois Sinal do MESMO código, um com citação
    # real (passaria sozinho) e outro inventado. Os dois devem sair valida=False —
    # uma checagem por Sinal isolado, sem agrupar por código, deixaria o primeiro True
    # e quebraria só este teste, silenciosamente, com os outros cinco casos verdes.
    sinais = [
        sinal("dinheiro_retido", "até hoje não recebi o estorno"),
        sinal("dinheiro_retido", "a empresa confessou fraude por escrito ontem"),
    ]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert resultado[0]["valida"] is False, \
        "AD-2: citação real deveria cair junto por causa da par inventada no mesmo código"
    assert resultado[1]["valida"] is False, "AD-2: citação inventada não deveria passar"


def test_citacao_de_quatro_palavras_substring_valida_ainda_reprova():
    # Prova que o piso de palavras não é bypassável só por ser substring exata.
    sinais = [sinal("dinheiro_retido", "até hoje não recebi")]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert resultado[0]["valida"] is False, "AC3: citação de 4 palavras deveria reprovar"


def test_citacao_de_exatamente_cinco_palavras_passa_limite_inclusivo():
    sinais = [sinal("dinheiro_retido", "até hoje não recebi o")]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert resultado[0]["valida"] is True, "AC3: 5 palavras é o piso inclusivo, deveria passar"


def test_citacao_vazia_reprova_apesar_de_ser_substring_de_qualquer_texto():
    # "" in TEXTO é True — a checagem de substring sozinha deixaria passar. O piso de
    # palavras é quem reprova aqui, no mesmo lugar da checagem de substring (FR-6).
    sinais = [sinal("dinheiro_retido", "")]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert resultado[0]["valida"] is False, "AC4: citação vazia deveria reprovar"


def test_analise_fabricada_com_citacao_falsa_derruba_o_codigo_sem_rede():
    # CM-2: caso construído à mão para ameaca_explicita, dano_continuado e
    # registro_contraditorio, que a base real não exercita o suficiente — a suíte é a
    # única coisa que executa esses caminhos (project-context.md). Nenhum import de
    # google.genai neste arquivo nem em evidencia.py: não há como fazer chamada de rede.
    texto = (
        "Se não resolverem em 5 dias vou procurar meus direitos no Procon. Já é o "
        "terceiro mês que a mensalidade é debitada mesmo com o plano cancelado. Consta "
        "como entregue no dia 12, mas o rastreio BR8842 mostra devolvido ao remetente."
    )
    sinais = [
        sinal("ameaca_explicita", "vou procurar meus direitos no Procon"),
        sinal("dano_continuado", "o prejuízo nunca foi reconhecido pela diretoria"),  # fabricada
        sinal("registro_contraditorio", "Consta como entregue no dia 12"),
    ]
    resultado = evidencia.verificar(sinais, texto)
    por_codigo = {s["codigo"]: s["valida"] for s in resultado}
    assert por_codigo["ameaca_explicita"] is True, "citação real de ameaca_explicita reprovou"
    assert por_codigo["dano_continuado"] is False, \
        "CM-2: citação fabricada de dano_continuado deveria derrubar o código"
    assert por_codigo["registro_contraditorio"] is True, \
        "citação real de registro_contraditorio reprovou"


def test_grupo_intercalado_com_outro_codigo_ainda_derruba_junto():
    # Prova que o agrupamento é por dict (codigo -> valido), não por adjacência na
    # lista: um Sinal de outro código intercalado não deveria afetar o agrupamento.
    sinais = [
        sinal("dinheiro_retido", "até hoje não recebi o estorno"),
        sinal("prazo_estourado", "Cancelei a compra há 40 dias"),
        sinal("dinheiro_retido", "a empresa confessou fraude por escrito ontem"),
    ]
    resultado = evidencia.verificar(sinais, TEXTO)
    por_codigo = {s["codigo"]: s["valida"] for s in resultado}
    assert por_codigo["dinheiro_retido"] is False, \
        "AD-2: par intercalado por outro código ainda deveria cair junto"
    assert por_codigo["prazo_estourado"] is True, \
        "Sinal de outro código não deveria ser afetado pelo par que caiu"


def test_grupo_de_tres_com_uma_fabricada_derruba_as_tres():
    # AD-2 generaliza além de pares: qualquer tamanho de grupo cai junto se uma
    # citação falhar, não só o caso de dois testado acima.
    sinais = [
        sinal("dinheiro_retido", "até hoje não recebi o estorno"),
        sinal("dinheiro_retido", "quero meu dinheiro urgente"),
        sinal("dinheiro_retido", "a empresa confessou fraude por escrito ontem"),
    ]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert all(s["valida"] is False for s in resultado), \
        "AD-2: grupo de três com uma citação fabricada deveria cair inteiro"


def test_lista_vazia_de_sinais_devolve_lista_vazia():
    assert evidencia.verificar([], TEXTO) == []


def test_verificar_nao_muta_a_lista_recebida():
    original = [sinal("dinheiro_retido", "até hoje não recebi o estorno", valida=False)]
    copia_antes = dict(original[0])
    evidencia.verificar(original, TEXTO)
    assert original[0] == copia_antes, "verificar() não deveria mutar os Sinal recebidos"


def test_ordem_de_saida_e_a_mesma_da_entrada():
    sinais = [
        sinal("prazo_estourado", "prometeram solução em 5 dias úteis"),
        sinal("dinheiro_retido", "até hoje não recebi o estorno"),
    ]
    resultado = evidencia.verificar(sinais, TEXTO)
    assert [s["codigo"] for s in resultado] == ["prazo_estourado", "dinheiro_retido"], \
        "verificar() deveria preservar a ordem de entrada"
