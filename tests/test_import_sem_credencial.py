"""Verificação executável de AD-7 e AD-12: os módulos folha vivem sem SDK e sem credencial."""

import importlib
import sys

MODULOS = ["plataforma.estado", "plataforma.catalogo", "plataforma.config",
           "plataforma.ingestao", "plataforma.evidencia", "plataforma.pontuacao",
           "plataforma.agregacao"]


def test_importa_sem_google_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    for nome in MODULOS:
        # delitem e não sys.modules.pop: o pop não é desfeito no teardown e deixaria
        # duas cópias do contrato na sessão, com os outros testes segurando a antiga.
        monkeypatch.delitem(sys.modules, nome, raising=False)
        modulo = importlib.import_module(nome)
        assert modulo.__name__ == nome, f"AD-12: importou {modulo.__name__} no lugar de {nome}"


def test_nenhum_modulo_folha_arrasta_o_sdk(monkeypatch):
    # AD-7: só analise.py pode importar google.genai, direta ou transitivamente.
    for nome in list(sys.modules):
        if nome.startswith(("google", "plataforma")):
            monkeypatch.delitem(sys.modules, nome, raising=False)
    for nome in MODULOS:
        importlib.import_module(nome)
    arrastados = [n for n in sys.modules if n.startswith("google")]
    assert not arrastados, f"AD-7: módulos folha arrastaram {arrastados}"
