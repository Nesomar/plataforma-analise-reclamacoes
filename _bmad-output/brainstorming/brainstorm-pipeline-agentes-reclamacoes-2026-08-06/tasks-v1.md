# Task list — v1

Ordenada por dependência. Cada tarefa é pequena o bastante pra terminar numa sentada.

---

## Fundação

- [ ] **1. Ambiente** — venv, `langgraph`, `langchain-google-genai`, `pandas`, `pytest`. Chave do Google AI Studio em `.env`, `.env` no `.gitignore`.
- [ ] **2. Corpus de teste** — salvar as 5 reclamações da sessão como `dados/corpus.csv` com o schema fixo (`empresa`, `titulo`, `texto`, `data`). É o gabarito do projeto inteiro.
- [ ] **3. Contrato de state** — `schemas.py` com `Reclamacao`, `Analise`, `Estado`. **Fazer antes de qualquer outra coisa.** É o único item não-aditivo do v1.

## Determinístico primeiro (roda sem gastar token)

- [ ] **4. Nó `carregar`** — lê CSV, valida schema, gera `id` estável (`hash(texto)` truncado). Falha alto em coluna faltando.
- [ ] **5. Teste do `id`** — mesma entrada, duas execuções, mesmos `id`s.
- [ ] **6. Nó `pontuar`** — as 3 parcelas + aritmética de prazo. Puro, sem rede.
- [ ] **7. Teste do score contra o gabarito** — alimentar `Analise` montada à mão a partir das 5 reclamações e conferir que 2, 3 e 4 entram na fila. *Esse é o teste que importa.*
- [ ] **8. Nó `agregar`** — contagem por sentimento, ranking de produtos, fila ordenada.

## LLM

- [ ] **9. Prompt do analisador** — structured output, glossário explícito dos 5 tipos de sinal B com exemplo, citação obrigatória por sinal.
- [ ] **10. Nó `analisar_lotes`** — fatia em lotes de 10, chama Gemini, casa resposta **por `id`** (nunca por posição), registra `id` ausente sem quebrar.
- [ ] **11. Pós-validação de citação** — `if citacao not in texto_original: sinal = False`. Determinístico, roda depois de toda resposta do LLM.
- [ ] **12. Teste de lote incompleto** — simular resposta com 9 itens para lote de 10; nenhum `id` pode ser perdido ou trocado.
- [ ] **13. Rodar sobre o corpus real** — conferir sentimento e produto na mão nas 5. Ajustar o glossário do prompt, não o código.

## Grafo e saída

- [ ] **14. Montar o `StateGraph`** — `carregar → analisar_lotes → pontuar → agregar → renderizar`, linear.
- [ ] **15. Nó `renderizar`** — HTML único autocontido. Gráficos SVG inline ou matplotlib em base64. Zero CDN.
- [ ] **16. Fila com evidência visível** — cada item da fila mostra a citação que sustentou a classificação. Não é metadado, é conteúdo.
- [ ] **17. Nota no HTML sobre volume ≠ gravidade** — uma linha, no ranking de produtos.
- [ ] **18. `main.py`** — CLI: caminho do CSV entra, caminho do HTML sai.

## Fechamento

- [ ] **19. Rodar ponta a ponta** e abrir o HTML.
- [ ] **20. Anotar a calibragem** — qual `N` de lote aguentou, qual corte de score deu a fila menos inflacionada, o que o glossário precisou ganhar. Isso vira input do v2.

---

## Não fazer agora

Cascata Flash→Pro · cache · guard-rails · loop de crítica · checkpoint · front/upload · níveis de criticidade.

Revisitar **antes** do v2: a fila binária infla (3 de 5 no corpus). A troca por níveis com prazo — modelo de triagem de pronto-socorro — deve ser decidida antes de gastar tempo calibrando o corte atual.
