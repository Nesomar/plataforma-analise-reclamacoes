"""Configuração da execução — tamanho de lote e modelo — validada antes de gastar.

Toda leitura e toda validação vivem dentro de `carregar()`, nunca em escopo de módulo:
importar este arquivo precisa funcionar sob configuração inválida, senão a inspeção de
imports que AD-12 exige ficaria impossível de fazer justamente quando ela mais importa.
Quem traduz o `ValueError` em saída de processo é o entrypoint. A chave de API não passa
por aqui: `load_dotenv()` popula o ambiente e o SDK a lê sozinho, dentro de
`analisar_lote` (AD-7, NFR-10) — assim a credencial nunca vira valor Python.
"""

import os
from typing import NamedTuple

from dotenv import load_dotenv

# Premissa de NFR-1 (5 chamadas em lote de 10 sobre 50 reclamações), não número medido:
# não há medição de limite de contexto nem de resposta incompleta por tamanho de lote.
TAMANHO_LOTE_PADRAO = 10

# Pinado de propósito: alias móvel invalida comparação de F1 entre execuções — mesmo
# motivo registrado em classificador.py:23.
MODELO_PADRAO = "gemini-3.6-flash"

# AD-17, primeira cláusula: piso 2 e teto 25, inclusivos, verificados na carga da
# configuração. A segunda cláusula — fundir lote residual de tamanho 1 — é de
# `ingestao.py` (Story 1.3) e não cabe aqui: na carga o CSV ainda não foi lido, então o
# resto da divisão não existe. `tamanho_lote = 7` sobre 50 linhas passa por esta faixa e
# ainda deixa um lote de 1; a defesa é em duas camadas, em dois módulos.
FAIXA_LOTE = (2, 25)


class Config(NamedTuple):
    """Configuração congelada da execução.

    Congelada porque é lida por vários nós do grafo: um deles reatribuindo `tamanho_lote`
    mudaria o fatiamento já validado sem deixar rastro. Não carrega concorrência — AD-9
    declara `max_concurrency` inerte no v1 síncrono, e botão que não move nada é pior que
    botão ausente. Não carrega credencial, por AD-7.
    """

    tamanho_lote: int
    modelo: str


def _do_ambiente(nome):
    """Devolve o valor da variável, ou `None` quando ela não diz nada.

    `None`, `""` e só-espaços são o mesmo caso: quem copia `.env.example` para `.env`
    fica com `TAMANHO_LOTE=`, e NFR-10 obriga o exemplo a listar nomes sem valores. Se
    vazio fosse erro, o fluxo documentado no próprio repositório quebraria na primeira
    execução.
    """
    valor = os.environ.get(nome)
    return valor.strip() if valor and valor.strip() else None


def carregar() -> Config:
    """Lê o ambiente, valida a faixa do lote e devolve a configuração congelada.

    Levanta `ValueError` nomeando variável, valor observado e faixa quando o tamanho de
    lote não serve — encerrando antes de qualquer chamada paga (AD-17). O valor de
    `MODELO` não é validado contra allowlist: congelaria um catálogo de modelos que
    envelhece. `MODELO=lixo` só falha na primeira chamada — lacuna conhecida, fechá-la
    exigiria consultar a API, que AD-7 proíbe daqui.
    """
    # override=False é o default e é o comportamento correto: variável real de ambiente
    # vence o .env, preservando o `export` documentado no README.
    load_dotenv(override=False)

    modelo = _do_ambiente("MODELO") or MODELO_PADRAO
    bruto = _do_ambiente("TAMANHO_LOTE")
    if bruto is None:
        return Config(TAMANHO_LOTE_PADRAO, modelo)

    minimo, maximo = FAIXA_LOTE
    # `int(bruto)` cru diria "invalid literal for int()" sem nomear a variável nem a
    # faixa. `isascii` junto de `isdecimal` porque o segundo sozinho aceita "²", que
    # `int()` recusa e devolveria o erro cru pela porta dos fundos, e "١٠", que ele
    # aceitaria como 10 sem o operador reconhecer o valor que digitou.
    limpo = bruto.removeprefix("-").removeprefix("+")
    if not (limpo.isascii() and limpo.isdecimal()):
        raise ValueError(
            f"TAMANHO_LOTE={bruto!r} não é um número inteiro: "
            f"informe um valor de {minimo} a {maximo}."
        )
    # Comprimento antes da conversão: acima de 4300 dígitos o próprio `int()` levanta
    # ValueError sobre limite de conversão, e ele também não nomeia variável nem faixa.
    # Nenhum valor dentro da faixa tem mais dígitos que o teto, então o `and` corta
    # antes de converter. Faixa em mensagem própria: quem escreveu -3 informou um
    # inteiro, e mandá-lo "informar um número inteiro" é diagnóstico errado.
    if not (len(limpo) <= len(str(maximo)) and minimo <= int(bruto) <= maximo):
        raise ValueError(
            f"TAMANHO_LOTE={bruto!r} fora da faixa permitida de {minimo} a {maximo}."
        )
    return Config(int(bruto), modelo)
