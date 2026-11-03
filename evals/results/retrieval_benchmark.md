# Benchmark de recuperação (políticas)

19 perguntas no estilo do cliente ([retrieval_cases.yaml](retrieval_cases.yaml)), 24 trechos do manual. `dense` = só embeddings; `hybrid` = embeddings + BM25 (fusão por rank).

| Modelo de embedding | Modo | hit@1 | hit@3 | MRR | Perguntas fora do top 3 |
|---|---|---|---|---|---|
| `openai/text-embedding-3-small` | dense | 74% | 89% | 0.83 | endereço da loja; onde fica a loja física? |
| `openai/text-embedding-3-small` | hybrid | 53% | 95% | 0.74 | onde fica a loja física? |
| `openai/text-embedding-3-large` | dense | 79% | 100% | 0.89 | — |
| `openai/text-embedding-3-large` | hybrid | 68% | 95% | 0.81 | onde fica a loja física? |
| `qwen/qwen3-embedding-8b` | dense | 68% | 100% | 0.83 | — |
| `qwen/qwen3-embedding-8b` | hybrid | 74% | 95% | 0.83 | onde fica a loja física? |
| `baai/bge-m3` | dense | 89% | 100% | 0.94 | — |
| `baai/bge-m3` | hybrid | 79% | 95% | 0.88 | onde fica a loja física? |
| `google/gemini-embedding-001` | dense | 74% | 100% | 0.86 | — |
| `google/gemini-embedding-001` | hybrid | 79% | 95% | 0.87 | onde fica a loja física? |
