"""Cobre `carregar`: caso feliz contra o CSV real, e os quatro caminhos de erro (AC1-AC5).

Erros usam CSV sintético escrito à mão em `tmp_path`, nunca editando
`docs/reclamacoes_reclameaqui.csv` — esse é o corpus de referência do caso feliz e de
M-1/M-2 no Épico 3 (AD-12, Dev Notes da story).
"""

import re

import pytest

from plataforma import ingestao

CSV_REAL = "docs/reclamacoes_reclameaqui.csv"

CABECALHO = "ID_Reclamacao;Data;Empresa;Titulo;Descricao;Cidade_Estado;Status"


def escrever(tmp_path, conteudo, nome="reclamacoes.csv"):
    caminho = tmp_path / nome
    # utf-8-sig: prova de que a leitura crua não é usada — se `carregar` lesse com
    # `utf-8`, o BOM colaria em "ID_Reclamacao" e o teste de coluna faltante do
    # cabeçalho real quebraria por um motivo errado.
    caminho.write_text(conteudo, encoding="utf-8-sig")
    return str(caminho)


def test_csv_real_produz_50_reclamacoes_sem_bom_e_com_data_iso(tmp_path):
    resultado = ingestao.carregar(CSV_REAL)
    assert len(resultado) == 50, f"AC1: carregar() devolveu {len(resultado)} itens"
    assert resultado[0]["id"] == "RA249827706", \
        f"AC1: primeiro id veio {resultado[0]['id']!r}"
    for reclamacao in resultado:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", reclamacao["data"]), \
            f"AC1: data {reclamacao['data']!r} não está em AAAA-MM-DD"


def test_execucoes_repetidas_produzem_o_mesmo_set_de_ids():
    primeira = {r["id"] for r in ingestao.carregar(CSV_REAL)}
    segunda = {r["id"] for r in ingestao.carregar(CSV_REAL)}
    assert primeira == segunda, "AC5: duas chamadas devolveram sets de id diferentes"


def test_coluna_faltante_levanta_nomeando_a_coluna(tmp_path):
    sem_cidade_estado = (
        "ID_Reclamacao;Data;Empresa;Titulo;Descricao;Status\n"
        "1;01/01/2026;Empresa X;Titulo;Descricao;Respondida\n"
    )
    caminho = escrever(tmp_path, sem_cidade_estado)
    with pytest.raises(ValueError, match="Cidade_Estado"):
        ingestao.carregar(caminho)


def test_id_duplicado_levanta_nomeando_o_id(tmp_path):
    conteudo = (
        CABECALHO + "\n"
        "ID-DUP;01/01/2026;Empresa X;Titulo 1;Descricao 1;SP;Respondida\n"
        "ID-OUTRO;02/01/2026;Empresa Y;Titulo 2;Descricao 2;RJ;Resolvido\n"
        "ID-DUP;03/01/2026;Empresa Z;Titulo 3;Descricao 3;MG;Em réplica\n"
    )
    caminho = escrever(tmp_path, conteudo)
    with pytest.raises(ValueError, match="ID-DUP"):
        ingestao.carregar(caminho)


def test_csv_sem_linha_de_dado_levanta_com_causa_nomeada(tmp_path):
    caminho = escrever(tmp_path, CABECALHO + "\n")
    with pytest.raises(ValueError, match="nenhuma linha de dado"):
        ingestao.carregar(caminho)


def test_data_malformada_levanta_nomeando_id_e_valor(tmp_path):
    conteudo = (
        CABECALHO + "\n"
        "1;2026-01-01;Empresa X;Titulo;Descricao;SP;Respondida\n"
    )
    caminho = escrever(tmp_path, conteudo)
    with pytest.raises(ValueError, match=r"ID_Reclamacao '1'.*2026-01-01"):
        ingestao.carregar(caminho)


def test_csv_vazio_sem_cabecalho_levanta(tmp_path):
    caminho = escrever(tmp_path, "")
    with pytest.raises(ValueError):
        ingestao.carregar(caminho)


def test_linha_com_menos_campos_que_o_cabecalho_levanta(tmp_path):
    conteudo = CABECALHO + "\n" + "1;01/01/2026;Empresa X;Titulo;Descricao\n"
    caminho = escrever(tmp_path, conteudo)
    with pytest.raises(ValueError, match="menos campos"):
        ingestao.carregar(caminho)
