# Plataforma de Análise de Reclamações

Pipeline multi-agente (LangGraph sobre Gemini) que lê uma base de reclamações de consumidor em texto livre e devolve três leituras: uma fila de prioridade com a evidência à vista, um ranking de produtos, e a percepção do cliente sobre a marca.

Projeto de estudo. O objetivo declarado é dominar arquitetura de pipeline multi-agente; o problema foi escolhido por ser real o bastante para que o aprendizado seja real.

## Os dados são sintéticos

`docs/reclamacoes_reclameaqui.csv` contém **50 reclamações sintéticas** sobre **14 empresas fictícias**, geradas para este projeto. Validado em 2026-08-06: nenhum nome de pessoa, nenhum CPF, nenhum endereço, nenhum telefone; protocolos e identificadores são aleatórios.

Nenhuma base real de reclamações entra neste repositório, nem relatório gerado a partir de uma. Um relatório produzido sobre base real herda os dados pessoais das citações literais que exibe e deve ser tratado como documento restrito.

## O resultado que vale a pena registrar

Sobre esta base, o classificador com LLM **empata** com uma regra determinística de seis strings: F1 0,86 para ambos, zero divergências nas 50 reclamações.

Duas leituras, ambas verdadeiras. O LLM se validou — reconstruiu a categorização inteira lendo apenas o texto livre, sem nunca ver o título canônico que a regra consome de graça. E o LLM não se paga aqui — reproduzir um `set` de seis strings é custo sem retorno.

`baseline.py` existe para tornar esse empate mensurável em vez de opinável.

## Rodar

```bash
uv sync
export GEMINI_API_KEY=...   # veja .env.example
uv run python baseline.py       # linha de base determinística
uv run python classificador.py  # classificador com Gemini
```

## Documentos

| Documento | O que carrega |
|---|---|
| `_bmad-output/specs/spec-plataforma-analise-reclamacoes/SPEC.md` | Capacidades, restrições, não-objetivos |
| `.../risk-signals.md` | Sinais de risco e a calibragem contra o gabarito humano |
| `.../state-contract.md` | Contrato de estado do grafo |
| `_bmad-output/planning-artifacts/prds/` | PRD: usuários, métricas, governança de dados, comportamento em falha |
