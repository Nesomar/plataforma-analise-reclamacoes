# Diagramas de arquitetura

Companion de `SPEC.md`. Sustenta CAP-9.

## Grafo do v1

Divisão dos nós **por etapa do fluxo**. Linear; o roteamento condicional entra junto com a cascata, em `roadmap.md`.

```mermaid
flowchart LR
    A[carregar] --> B[analisar_lotes]
    B --> C[pontuar]
    C --> D[agregar]
    D --> E[renderizar]

    A -.->|determinístico| A
    B -.->|LLM| B
    C -.->|determinístico| C
    D -.->|determinístico| D
    E -.->|determinístico| E
```

| Nó | Tipo | Responsabilidade |
|---|---|---|
| `carregar` | determinístico | Lê o CSV, valida o schema fixo, atribui `id` estável. Falha explicitamente em coluna faltando. |
| `analisar_lotes` | **LLM** | Único nó que chama o modelo. Fatia em lotes, saída estruturada, casa resposta por `id`. |
| `pontuar` | determinístico | Aplica as três parcelas e a aritmética de prazo. Nenhuma chamada de rede. |
| `agregar` | determinístico | Contagens, ranking de produtos, distribuição de sentimento, ordenação da fila. |
| `renderizar` | determinístico | Escreve o arquivo HTML único. |

## Lote e escalada

O conflito estrutural: lote quer atomicidade, cascata quer granularidade. A resolução é o lote se desfazer na escalada — nunca chamada individual.

```mermaid
flowchart TD
    L[Lote de N reclamações] --> F[Modelo de triagem]
    F --> R{Roteador}
    R -->|não suspeitas| OK[Resultado aceito]
    R -->|suspeitas| S[Sublote remontado<br/>só com os suspeitos]
    S --> P[Modelo de confirmação]
    P --> M[Merge por id]
    OK --> M
    M --> OUT[Análises consolidadas]
```

**No v1 apenas o caminho superior existe** — um único modelo, sem roteador e sem sublote. O diagrama registra o desenho alvo para que o contrato de estado seja construído compatível com ele desde a primeira versão.

O merge final é sempre **por `id`**. É por isso que o identificador estável é o item não-aditivo do contrato.

## Fluxo da evidência

```mermaid
flowchart LR
    T[Texto original] --> M[Modelo]
    M -->|sinal + citação| V{citação é<br/>substring do texto?}
    V -->|sim| K[Sinal mantido]
    V -->|não| D[Sinal derrubado<br/>para falso]
    K --> SC[Score]
    K --> REL[Relatório:<br/>citação visível]
```

A verificação é determinística e roda depois de toda resposta do modelo. É a implementação de CAP-5 e a defesa primária contra falso positivo.
