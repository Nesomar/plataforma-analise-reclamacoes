"""Lê o CSV de reclamações e recusa base inválida antes de qualquer chamada paga.

Coluna ausente, `ID_Reclamacao` repetido ou CSV sem linha de dado levantam `ValueError`
nomeando a causa aqui — na leitura, não na fatura da API (FR-3). Fail-fast de coluna
acontece antes de ler qualquer linha: checar `fieldnames` primeiro evita gastar tempo
processando um arquivo que já se sabe inválido. `carregar` não fatia em lotes nem monta
`Send` — isso é da Story 1.6, que lê a base já validada por aqui.
"""

import csv
from datetime import datetime

from plataforma.estado import Reclamacao

# Ordem e nomes exatos do cabeçalho real de docs/reclamacoes_reclameaqui.csv, confirmados
# contra state-contract.md. `Descricao` mapeia para `texto` — não é 1:1 com o campo.
COLUNAS_ESPERADAS = ("ID_Reclamacao", "Data", "Empresa", "Titulo", "Descricao",
                     "Cidade_Estado", "Status")


def carregar(caminho: str) -> list[Reclamacao]:
    """Lê `caminho`, valida schema e unicidade de id, e devolve as reclamações tipadas.

    `utf-8-sig` porque o arquivo real carrega BOM — lendo com `utf-8` cru o BOM cola no
    nome da primeira coluna e o `KeyError` resultante não aponta para a causa real
    (state-contract.md). `Data` chega `DD/MM/AAAA` e sai ISO-8601, único lugar do
    pipeline onde esse formato de origem existe.
    """
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")

        # Checagem de coluna antes de iterar linha alguma: fail-fast, sem processar
        # nenhum dado de um arquivo que já se sabe com schema errado (FR-3).
        faltantes = set(COLUNAS_ESPERADAS) - set(leitor.fieldnames or ())
        if faltantes:
            raise ValueError(
                f"CSV {caminho!r} sem a(s) coluna(s) {sorted(faltantes)}; "
                f"esperado: {list(COLUNAS_ESPERADAS)}."
            )

        reclamacoes: list[Reclamacao] = []
        ids_vistos: set[str] = set()
        for linha in leitor:
            # Linha com menos campos que o cabeçalho: DictReader preenche a(s) coluna(s)
            # final(is) faltante(s) com None, e um None viraria valor de campo tipado
            # como str sem erro nenhum — ou um TypeError cru no strptime abaixo.
            if None in linha.values():
                raise ValueError(
                    f"CSV {caminho!r} tem linha com menos campos que as "
                    f"{len(COLUNAS_ESPERADAS)} colunas esperadas: {linha!r}."
                )
            id_reclamacao = linha["ID_Reclamacao"]
            # Reporta assim que repete, sem esperar o arquivo inteiro (AC3) — a
            # garantia de unicidade é do arquivo, não do sistema (state-contract.md).
            if id_reclamacao in ids_vistos:
                raise ValueError(
                    f"CSV {caminho!r} tem ID_Reclamacao {id_reclamacao!r} repetido."
                )
            ids_vistos.add(id_reclamacao)

            try:
                data_iso = datetime.strptime(linha["Data"], "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                # Renomeia o erro cru do stdlib com id da linha e valor observado —
                # sem isso a causa fica sem apontar para a linha (project-context.md).
                raise ValueError(
                    f"CSV {caminho!r}: ID_Reclamacao {id_reclamacao!r} tem Data "
                    f"{linha['Data']!r} fora do formato DD/MM/AAAA."
                ) from None

            reclamacoes.append(Reclamacao(
                id=id_reclamacao,
                data=data_iso,
                empresa=linha["Empresa"],
                titulo=linha["Titulo"],
                texto=linha["Descricao"],
                cidade_estado=linha["Cidade_Estado"],
                status=linha["Status"],
            ))

    if not reclamacoes:
        # Cabeçalho válido sem nenhuma linha de dado cai aqui, não em erro de coluna
        # (AC4, AD-13).
        raise ValueError(f"CSV {caminho!r} não tem nenhuma linha de dado.")

    return reclamacoes
