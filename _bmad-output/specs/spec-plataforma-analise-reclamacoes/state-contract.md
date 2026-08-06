# Contrato de estado

Companion de `SPEC.md`. Sustenta CAP-1, CAP-5 e CAP-9.

Esta é a **única parte do v1 que não é aditiva**. Cache, cascata e checkpoint — todos deferidos — precisam saber de qual reclamação estão falando. Errar aqui converte cada um deles de plugin em reescrita.

## Estruturas

```python
from typing import TypedDict, Literal, Annotated
from operator import add

class Reclamacao(TypedDict):
    id: str            # ID_Reclamacao do CSV — já único na origem
    data: str          # ISO-8601, convertido de DD/MM/AAAA
    empresa: str
    titulo: str
    texto: str         # coluna Descricao do CSV
    cidade_estado: str
    status: Literal["Respondida", "Não respondida",
                    "Resolvido", "Não resolvido", "Em réplica"]

class Sinal(TypedDict):
    codigo: str                                      # catálogo em risk-signals.md
    citacao: str                                     # literal, piso de 5 palavras
    valida: bool                                     # default False — não verificado
                                                     # é indistinguível de reprovado

class Analise(TypedDict):
    id: str                                          # liga de volta — obrigatório
    sentimento: Literal["positivo", "neutro", "negativo"]
    produto: str | None
    sinais: list[Sinal]                              # par indivisível código↔citação
    prazo_prometido_dias: int | None
    data_evento: str | None                          # ISO-8601 ou None

class Falha(TypedDict):
    ids: list[str]                                   # reclamações que ficaram sem análise
    causa: str
    no: str

class Motivo(TypedDict):
    origem: Literal["sinal", "atributo"]
    rotulo: str
    citacao: str | None                              # não-nula sse origem == "sinal"

class Pontuacao(TypedDict):
    id: str
    pontos: int
    na_fila: bool
    motivos: list[Motivo]                            # o que o relatório exibe

class Estado(TypedDict):
    reclamacoes: list[Reclamacao]
    analises: Annotated[list[Analise], add]          # acumula entre execuções de lote
    falhas: Annotated[list[Falha], add]              # acumula entre execuções de lote
    pontuacoes: list[Pontuacao]
    agregados: Agregados                             # TypedDict, nunca dict cru
    caminho_html: str
```

> **Revisado em 2026-08-06 pela spine de arquitetura.** `sinal_b: list[str]` + `evidencia: list[str]` eram listas paralelas sem ligação entre si — FR-7 exige derrubar o sinal que a citação falsa sustentava, e com listas paralelas isso é indeterminável. `sinal_a: bool` desapareceu como campo próprio: ameaça explícita é um código do catálogo como qualquer outro, e tratá-la à parte duplicava a regra da evidência. `scores: dict[str, int]` não tinha onde carregar o motivo que FR-12 manda exibir. Ver AD-1, AD-3, AD-4 e AD-5 em `ARCHITECTURE-SPINE.md`.

## Formato do arquivo de origem

Validado contra `docs/reclamacoes_reclameaqui.csv` em 2026-08-06.

| Característica | Valor |
|---|---|
| Separador | `;` |
| Codificação | UTF-8 **com BOM** — ler com `utf-8-sig`, senão o nome da primeira coluna vem com `﻿` colado |
| Aspas | ausentes; nenhum campo contém o separador |
| Colunas | `ID_Reclamacao`, `Data`, `Empresa`, `Titulo`, `Descricao`, `Cidade_Estado`, `Status` |
| Formato de data | `DD/MM/AAAA` |

## Regras

**Identificador vem da origem.** O CSV já traz `ID_Reclamacao` único em 50 de 50 linhas. Adotar esse identificador em vez de derivar hash — mas **validar unicidade na ingestão** e falhar se houver colisão, porque a garantia é do arquivo, não do sistema.

**Casamento por `id`, nunca por posição.** Se o modelo devolver dezenove itens para um lote de vinte, a etapa de análise detecta qual faltou e registra a falha. Assumir alinhamento posicional é o modo mais silencioso de corromper a base inteira.

**`evidencia` é campo de primeira classe, não metadado.** Ele atravessa o estado até o relatório e aparece na saída visível ao gestor.

**`analises` e `falhas` acumulam.** O redutor `add` permite que execuções paralelas de lote escrevam no mesmo estado sem sobrescrever. A partir da spine, cada lote é uma **execução de nó** despachada por `Send`, não uma iteração dentro de um nó — o redutor deixa de ser decoração e vira a mecânica do merge.

**Conservação.** `len(reclamacoes) == len(analises) + sum(len(f["ids"]) for f in falhas)`, verificado após o gather e antes de `pontuar`. Sem essa asserção, uma reclamação que evapora entre lotes é indistinguível de uma que nunca entrou.

**Zero análises encerra sem escrever.** Falha absorvida não é permissão para produzir relatório sobre nada. Ver AD-13.

## Ponto de extensão

O contrato acima é o que o v1 precisa deixar pronto para os itens de `roadmap.md`. Nada mais do roadmap precisa existir no v1 — mas nada dele funciona se o `id` não atravessar o estado.
