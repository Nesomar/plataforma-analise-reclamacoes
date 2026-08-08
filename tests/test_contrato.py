"""Verifica a forma do contrato de estado por introspecção.

Duas escolhas deliberadas, ambas por causa de regressões que passariam despercebidas:
o conjunto de campos é comparado contra `__required_keys__`, não contra
`get_type_hints`, porque este último apaga `NotRequired` e deixa um campo opcional
indistinguível de obrigatório; e as estruturas são descobertas do módulo, não listadas
à mão, para que um `TypedDict` novo reintroduzindo `evidencia` seja inspecionado em vez
de escapar da varredura.
"""

import ast
from operator import add
from pathlib import Path
from typing import get_args, get_type_hints

import pytest

from plataforma import catalogo, config, estado

CAMPOS_PROIBIDOS = {"sinal_a", "sinal_b", "evidencia"}

# Fonte independente do contrato: duplicada de propósito. Um teste que lesse os campos
# do próprio módulo sob teste não poderia detectar campo renomeado, a mais ou a menos.
CAMPOS_ESPERADOS = {
    "Reclamacao": {"id", "data", "empresa", "titulo", "texto", "cidade_estado", "status"},
    "Sinal": {"codigo", "citacao", "valida"},
    "Analise": {"id", "sentimento", "produto", "sinais", "prazo_prometido_dias",
                "data_evento"},
    "Falha": {"ids", "causa", "no"},
    "Motivo": {"origem", "rotulo", "citacao"},
    "Pontuacao": {"id", "pontos", "na_fila", "motivos"},
    "ItemRanking": {"rotulo", "total", "generico"},
    "DistribuicaoSentimento": {"positivo", "neutro", "negativo"},
    "Agregados": {"data_execucao", "lidas", "analisadas", "nao_analisadas",
                  "eventos_falha", "codigos_propostos", "codigos_derrubados", "fila",
                  "total_na_fila", "ocupacao_fila", "taxa_produto_nao_nomeado",
                  "ranking_produtos", "distribuicao_sentimento", "degradado",
                  "motivo_degradacao"},
    "Estado": {"reclamacoes", "analises", "falhas", "pontuacoes", "agregados",
               "caminho_html"},
}


def typed_dicts_de(modulo):
    """Descobre os TypedDict declarados no módulo, em vez de confiar numa lista fixa."""
    return {nome: obj for nome in dir(modulo)
            if isinstance(obj := getattr(modulo, nome), type)
            and hasattr(obj, "__required_keys__")}


def importados_por(modulo):
    """Todos os módulos importados, inclusive dentro de função e por import relativo.

    Percorre a AST porque a varredura textual que isto substitui só enxergava linha
    começando em coluna 0 e contendo a substring "plataforma": `from . import catalogo`
    passava por ela, verificado na prática.
    """
    arvore = ast.parse(Path(modulo.__file__).read_text(encoding="utf-8"))
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(alias.name.split(".")[0] for alias in no.names)
        elif isinstance(no, ast.ImportFrom):
            # level > 0 é import relativo: `from . import x` não nomeia o pacote.
            nomes.add("." if no.level else (no.module or "").split(".")[0])
        elif isinstance(no, ast.Call):
            alvo = getattr(no.func, "attr", None) or getattr(no.func, "id", None)
            if alvo == "import_module" and no.args:
                valor = getattr(no.args[0], "value", "")
                nomes.add(str(valor).split(".")[0])
    return nomes


def test_estruturas_declaradas_sao_exatamente_as_do_contrato():
    encontradas = set(typed_dicts_de(estado))
    assert encontradas == set(CAMPOS_ESPERADOS), \
        f"AC1: estado.py declara {sorted(encontradas)}"


@pytest.mark.parametrize("nome", sorted(CAMPOS_ESPERADOS))
def test_campos_exatos_e_todos_obrigatorios(nome):
    estrutura = getattr(estado, nome)
    # __required_keys__ e não get_type_hints: com NotRequired[bool] o segundo devolve
    # bool e a asserção passaria, que é justamente o buraco que AD-20 fecha.
    assert estrutura.__required_keys__ == frozenset(CAMPOS_ESPERADOS[nome]), \
        f"AC1: {nome} tem campos obrigatórios {sorted(estrutura.__required_keys__)}"
    assert not estrutura.__optional_keys__, \
        f"AC1: {nome} tem campo opcional {sorted(estrutura.__optional_keys__)}"


def test_campos_proibidos_ausentes_de_toda_estrutura_declarada():
    for nome, estrutura in typed_dicts_de(estado).items():
        intruso = set(estrutura.__annotations__) & CAMPOS_PROIBIDOS
        assert not intruso, f"AD-1: {nome} carrega campo proibido {sorted(intruso)}"


def test_sinal_e_par_indivisivel():
    campos = get_type_hints(estado.Sinal)
    assert campos["valida"] is bool, \
        f"AD-20: Sinal.valida é {campos['valida']}, deve ser bool puro"


def test_analises_e_falhas_acumulam_pelo_redutor_add():
    campos = get_type_hints(estado.Estado, include_extras=True)
    for chave, tipo_item in [("analises", estado.Analise), ("falhas", estado.Falha)]:
        args = get_args(campos[chave])
        assert args == (list[tipo_item], add), \
            f"AD-8: Estado.{chave} anotado como {campos[chave]}"


def test_agregados_e_tipado_nao_dict_cru():
    campos = get_type_hints(estado.Estado)
    assert campos["agregados"] is estado.Agregados, \
        f"AD-20: Estado.agregados é {campos['agregados']}"


def test_motivo_carrega_proveniencia():
    campos = get_type_hints(estado.Motivo)
    assert get_args(campos["origem"]) == ("sinal", "atributo"), \
        f"AD-3: Motivo.origem admite {get_args(campos['origem'])}"
    assert campos["citacao"] == (str | None), \
        f"AD-3: Motivo.citacao é {campos['citacao']}"


@pytest.mark.parametrize("modulo, permitidos", [
    (estado, {"typing", "operator"}),
    (catalogo, {"unicodedata", "types"}),
    (config, {"os", "typing", "dotenv"}),
])
def test_modulos_folha_so_importam_o_que_a_story_permite(modulo, permitidos):
    """AC1, AC5 e AD-7: nenhum import de plataforma/, e de terceiro só o que está aqui.

    A whitelist é explícita por módulo, não uma regra genérica contra terceiros:
    `config` importa `dotenv`, que é o mecanismo único de configuração. Qualquer import
    fora da lista do próprio módulo reprova — inclusive `google`, que é o ponto.
    """
    intrusos = importados_por(modulo) - permitidos
    assert not intrusos, \
        f"{modulo.__name__} importa {sorted(intrusos)}; permitido: {sorted(permitidos)}"
