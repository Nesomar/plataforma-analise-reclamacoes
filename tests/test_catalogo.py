"""Verifica que catalogo.py é a fonte única de códigos, grupo saturado e genéricos."""

from pathlib import Path

import pytest

from plataforma import catalogo

CODIGOS_ESPERADOS = {"dinheiro_retido", "registro_contraditorio", "dano_continuado",
                     "prazo_estourado", "ameaca_explicita", "lei_citada"}

PACOTE = Path(catalogo.__file__).parent


def test_seis_codigos_exatos():
    assert set(catalogo.CATALOGO) == CODIGOS_ESPERADOS, \
        f"AC5: catálogo declara {sorted(catalogo.CATALOGO)}"


def test_cada_codigo_tem_definicao_e_exemplo_escritos():
    for codigo, entrada in catalogo.CATALOGO.items():
        assert set(entrada) == {"definicao", "exemplo"}, \
            f"AC5: {codigo} tem chaves {sorted(entrada)}"
        for chave, texto in entrada.items():
            assert isinstance(texto, str) and texto.strip(), \
                f"AC5: {codigo}.{chave} não é texto escrito: {texto!r}"


def test_dinheiro_retido_cobre_as_seis_categorias_do_gabarito():
    definicao = catalogo.CATALOGO["dinheiro_retido"]["definicao"].lower()
    # Só a metade do que VALE: buscar na definição inteira deixaria o teste verde se
    # uma categoria fosse movida para a lista de exclusões, invertendo a regra.
    vale, _, nao_vale = definicao.partition("não vale para:")
    assert nao_vale, "AC5: a definição perdeu a lista de exclusões"
    for termo in ["estorno", "bloquead", "não entregue", "defeituoso",
                  "assinatura", "contratou"]:
        assert termo in vale, \
            f"AC5: '{termo}' não está entre as categorias que valem em dinheiro_retido"


def test_catalogo_e_somente_leitura():
    # O conteúdo vai para o prompt: mutação em runtime trocaria a definição que decide
    # a classificação sem aparecer em diff nenhum.
    with pytest.raises(TypeError):
        catalogo.CATALOGO["dinheiro_retido"] = {}
    with pytest.raises(TypeError):
        catalogo.CATALOGO["dinheiro_retido"]["definicao"] = "outra coisa"


def test_grupo_sinal_a_declarado_como_dado():
    assert set(catalogo.GRUPO_SINAL_A) == {"ameaca_explicita", "lei_citada"}, \
        f"AC5: grupo saturado é {catalogo.GRUPO_SINAL_A}"
    fora = set(catalogo.GRUPO_SINAL_A) - set(catalogo.CATALOGO)
    assert not fora, f"AC5: grupo saturado cita código fora do catálogo -> {sorted(fora)}"


def test_termos_genericos_sao_os_quatro_medidos():
    assert catalogo.TERMOS_GENERICOS == frozenset({"fatura", "compra", "produto", "serviço"}), \
        f"CM-3: lista de genéricos é {sorted(catalogo.TERMOS_GENERICOS)}"


@pytest.mark.parametrize("produto, esperado", [
    (None, True),
    ("", True),
    ("   ", True),
    ("fatura", True),
    ("Produto", True),          # o modelo escreve como quiser
    ("serviços", True),         # plural
    ("  Compra  ", True),
    ("serviço", True),
    ("cartão de crédito", False),
    ("plano de internet", False),
])
def test_nao_nomeia_produto_normaliza_antes_de_comparar(produto, esperado):
    assert catalogo.nao_nomeia_produto(produto) is esperado, \
        f"CM-3: {produto!r} classificado como {not esperado}"


def test_nenhum_outro_modulo_declara_codigo_de_sinal_como_literal():
    """AD-18: hoje é vacuamente verdadeiro, e é exatamente por isso que existe.

    Sem esta varredura o AC seguiria verde no dia em que pontuacao.py nascesse com a
    string repetida — que é o defeito que ela existe para pegar.
    """
    for arquivo in PACOTE.glob("*.py"):
        if arquivo.name == "catalogo.py":
            continue
        fonte = arquivo.read_text(encoding="utf-8")
        for codigo in CODIGOS_ESPERADOS:
            for literal in (f'"{codigo}"', f"'{codigo}'"):
                assert literal not in fonte, \
                    f"AD-18: {arquivo.name} declara o código {codigo} como literal"
