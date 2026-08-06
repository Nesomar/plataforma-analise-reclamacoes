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

class Analise(TypedDict):
    id: str                                          # liga de volta — obrigatório
    sentimento: Literal["positivo", "neutro", "negativo"]
    produto: str | None
    sinal_a: bool
    sinal_b: list[str]                               # códigos do catálogo em risk-signals.md
    evidencia: list[str]                             # citações literais
    prazo_prometido_dias: int | None
    data_evento: str | None                          # ISO-8601 ou None

class Estado(TypedDict):
    reclamacoes: list[Reclamacao]
    analises: Annotated[list[Analise], add]          # acumula entre lotes
    scores: dict[str, int]                           # id -> score
    agregados: dict
    caminho_html: str
```

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

**`analises` acumula.** O redutor `add` permite que lotes sucessivos escrevam no mesmo estado sem sobrescrever.

## Ponto de extensão

O contrato acima é o que o v1 precisa deixar pronto para os itens de `roadmap.md`. Nada mais do roadmap precisa existir no v1 — mas nada dele funciona se o `id` não atravessar o estado.
