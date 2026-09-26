"""Cobre a carga de configuração: defaults, faixa, tipo e inércia do import.

Todo teste roda com `config.load_dotenv` trocado por no-op e com `TAMANHO_LOTE` e
`MODELO` apagados do ambiente. As duas coisas são necessárias e por motivos diferentes:
`monkeypatch.chdir` não neutraliza o `.env` porque `find_dotenv()` sobe a partir do
diretório do arquivo que chamou — `plataforma/` —, achando a raiz do projeto de qualquer
diretório de trabalho; e o README manda o operador fazer `export TAMANHO_LOTE`, então
sem o `delenv` a suíte passa ou falha conforme a máquina de quem roda.

Os limites `2` e `25` são escritos à mão, sem importar `FAIXA_LOTE`: fonte duplicada de
propósito, no padrão de `CAMPOS_ESPERADOS` (tests/test_contrato.py:22-23) — um teste que
lê a faixa do módulo sob teste não detecta faixa alterada.
"""

import importlib
import sys
from pathlib import Path

import pytest

from plataforma import config


@pytest.fixture(autouse=True)
def ambiente_limpo(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.delenv("TAMANHO_LOTE", raising=False)
    monkeypatch.delenv("MODELO", raising=False)


def test_valor_do_ambiente_e_adotado_sem_alterar_codigo(monkeypatch):
    # 15 e não 10: com o valor igual ao default, um `carregar()` que ignorasse o
    # ambiente por completo passaria neste teste.
    monkeypatch.setenv("TAMANHO_LOTE", "15")
    carregada = config.carregar()
    assert carregada.tamanho_lote == 15, \
        f"AC1: tamanho_lote veio {carregada.tamanho_lote} com TAMANHO_LOTE=15"


def test_sem_variavel_definida_valem_os_defaults():
    carregada = config.carregar()
    assert carregada == (10, "gemini-3.6-flash"), f"AC2: defaults vieram {carregada}"


@pytest.mark.parametrize("vazio", ["", "   "])
def test_variavel_presente_e_vazia_cai_no_default(monkeypatch, vazio):
    monkeypatch.setenv("TAMANHO_LOTE", vazio)
    monkeypatch.setenv("MODELO", vazio)
    carregada = config.carregar()
    assert carregada == (10, "gemini-3.6-flash"), \
        f"AC3: com valor {vazio!r} veio {carregada}"


@pytest.mark.parametrize("limite", [2, 25])
def test_limites_da_faixa_sao_inclusivos(monkeypatch, limite):
    monkeypatch.setenv("TAMANHO_LOTE", str(limite))
    assert config.carregar().tamanho_lote == limite, \
        f"AC4: limite {limite} deveria ser aceito"


@pytest.mark.parametrize("com_espaco, esperado", [(" 15 ", 15), ("\t7\n", 7)])
def test_espaco_em_volta_do_valor_nao_atrapalha(monkeypatch, com_espaco, esperado):
    # Sem o strip, só o caso vazio quebraria — e " 15 " viraria erro de tipo.
    monkeypatch.setenv("TAMANHO_LOTE", com_espaco)
    assert config.carregar().tamanho_lote == esperado, \
        f"AC3: {com_espaco!r} deveria virar {esperado}"


@pytest.mark.parametrize("fora", ["1", "26", "-3", "0", "9" * 5000])
def test_fora_da_faixa_levanta_nomeando_valor_e_faixa(monkeypatch, fora):
    # "9" * 5000 é o caso do limite de 4300 dígitos do int(): sem a guarda de
    # comprimento, o ValueError vem do próprio int() e não nomeia variável nem faixa.
    monkeypatch.setenv("TAMANHO_LOTE", fora)
    with pytest.raises(ValueError) as erro:
        config.carregar()
    mensagem = str(erro.value)
    for esperado in ("TAMANHO_LOTE", "2", "25"):
        assert esperado in mensagem, f"AC4: mensagem {mensagem!r} não cita {esperado!r}"
    assert fora in mensagem, f"AC4: mensagem {mensagem[:120]!r} não cita o valor observado"


@pytest.mark.parametrize("invalido", ["abc", "7.5", "--3", "dez", "²", "١٠"])
def test_nao_inteiro_cai_pela_mesma_porta(monkeypatch, invalido):
    # "²" e "١٠" passam em isdecimal(): o primeiro faria int() levantar o erro cru que
    # AC5 proíbe, o segundo entraria como 10 sem o operador reconhecer o que digitou.
    monkeypatch.setenv("TAMANHO_LOTE", invalido)
    with pytest.raises(ValueError) as erro:
        config.carregar()
    mensagem = str(erro.value)
    assert "TAMANHO_LOTE" in mensagem and invalido in mensagem, \
        f"AC5: mensagem {mensagem!r} não nomeia a variável e o valor {invalido!r}"


@pytest.mark.parametrize("sinal", ["+10", "10"])
def test_sinal_positivo_explicito_e_aceito(monkeypatch, sinal):
    monkeypatch.setenv("TAMANHO_LOTE", sinal)
    assert config.carregar().tamanho_lote == 10, f"AC1: {sinal!r} deveria virar 10"


def test_modelo_custom_passa_sem_validacao(monkeypatch):
    monkeypatch.setenv("MODELO", "outro-modelo")
    assert config.carregar().modelo == "outro-modelo", \
        f"AC6: modelo veio {config.carregar().modelo}"


def test_ambiente_real_vence_o_env(monkeypatch):
    # A precedência é do dotenv, não deste módulo: o que cabe verificar é que `carregar`
    # não pede override. Posicional e nomeado são olhados porque `override` é o quarto
    # parâmetro posicional de load_dotenv — checar só kwargs deixaria a porta aberta.
    chamadas = []
    monkeypatch.setattr(config, "load_dotenv",
                        lambda *args, **kwargs: chamadas.append((args, kwargs)))
    config.carregar()
    assert chamadas, "AC1: carregar() não chamou load_dotenv"
    args, kwargs = chamadas[0]
    assert not any(args) and not kwargs.get("override"), \
        f"AC1: carregar() chamou load_dotenv com {args}, {kwargs}"


def test_config_nunca_toca_na_credencial():
    # NFR-10 e AD-7: a chave nunca vira valor Python. Sem esta varredura, um
    # `os.environ.get("GOOGLE_API_KEY")` entraria em config.py sem reprovar nada — a
    # whitelist de imports de test_contrato.py já permite `os`.
    fonte = Path(config.__file__).read_text(encoding="utf-8")
    for nome in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "api_key"):
        assert nome not in fonte, f"NFR-10: config.py cita {nome}"
    assert config.Config._fields == ("tamanho_lote", "modelo"), \
        f"AD-7: Config carrega {config.Config._fields}"


def test_config_devolvida_e_congelada():
    carregada = config.carregar()
    with pytest.raises(AttributeError):
        carregada.tamanho_lote = 3


def test_import_sob_configuracao_invalida_nao_levanta(monkeypatch):
    monkeypatch.setenv("TAMANHO_LOTE", "99")
    # delitem e não sys.modules.pop: o pop não é desfeito no teardown e deixaria duas
    # cópias do módulo na sessão, com os outros testes segurando a antiga.
    monkeypatch.delitem(sys.modules, "plataforma.config", raising=False)
    reimportado = importlib.import_module("plataforma.config")
    assert reimportado.__name__ == "plataforma.config", \
        f"AC7: import com TAMANHO_LOTE=99 devolveu {reimportado}"
