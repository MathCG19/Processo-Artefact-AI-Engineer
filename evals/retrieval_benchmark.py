"""Compare embedding models (and retrieval modes) on the policy-retrieval question set.

    python evals/retrieval_benchmark.py
    python evals/retrieval_benchmark.py --models openai/text-embedding-3-small qwen/qwen3-embedding-8b

Metrics: hit@1, hit@3 (is a correct section in the top 3? -> what the agent sees with k=3) and MRR.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from emporio_agent.config import Settings
from emporio_agent.llm import embed_texts, make_client
from emporio_agent.policies import PolicyChunk, extract_markdown, split_into_chunks
from emporio_agent.textutils import tokens

EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_MODELS = [
    "openai/text-embedding-3-small",
    "openai/text-embedding-3-large",
    "qwen/qwen3-embedding-8b",
    "baai/bge-m3",
    "google/gemini-embedding-001",
]


# Hybrid retrieval was evaluated here and NOT adopted (it lowered hit@1); kept for reproducibility.
def bm25_scores(query: str, chunks: list[PolicyChunk], k1: float = 1.5, b: float = 0.75) -> np.ndarray:
    """Classic BM25 over accent-insensitive, lightly stemmed tokens."""
    docs = [tokens(c.embedding_text()) for c in chunks]
    avgdl = sum(len(d) for d in docs) / len(docs)
    df = Counter(t for d in docs for t in set(d))
    n = len(docs)
    scores = np.zeros(n, dtype=np.float32)
    for i, doc in enumerate(docs):
        tf = Counter(doc)
        for term in set(tokens(query)):
            if term in tf:
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                scores[i] += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * len(doc) / avgdl))
    return scores


def hybrid_scores(query: str, chunks: list[PolicyChunk], dense: np.ndarray, k: int = 60) -> np.ndarray:
    """Reciprocal Rank Fusion of dense (embeddings) and lexical (BM25) rankings.

    Embeddings capture paraphrases ("me arrependi" ~ "direito de arrependimento"); BM25 catches
    rare exact keywords ("endereço", "boquilha", "SEDEX") that the dense model may underweight.
    """
    lexical = bm25_scores(query, chunks)
    dense_rank = np.empty(len(chunks), dtype=int)
    dense_rank[np.argsort(-dense)] = np.arange(len(chunks))
    lexical_rank = np.empty(len(chunks), dtype=int)
    lexical_rank[np.argsort(-lexical)] = np.arange(len(chunks))
    fused = 1.0 / (k + dense_rank + 1)
    fused += np.where(lexical > 0, 1.0 / (k + lexical_rank + 1), 0.0)  # no lexical overlap -> no bonus
    return fused


def load_cases() -> list[dict]:
    return yaml.safe_load((EVALS_DIR / "retrieval_cases.yaml").read_text(encoding="utf-8"))


def evaluate(rankings: list[list[str]], cases: list[dict]) -> dict:
    hit1 = hit3 = rr = 0.0
    misses = []
    for ranking, case in zip(rankings, cases):
        expected = set(case["expected_sections"])
        hit1 += ranking[0] in expected
        hit3 += bool(set(ranking[:3]) & expected)
        rank = next((i + 1 for i, cid in enumerate(ranking) if cid in expected), None)
        rr += 1 / rank if rank else 0
        if not set(ranking[:3]) & expected:
            misses.append(case["question"])
    n = len(cases)
    return {"hit@1": hit1 / n, "hit@3": hit3 / n, "mrr": rr / n, "misses": misses}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    args = parser.parse_args()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    settings = Settings.from_env()
    client = make_client(settings)
    chunks = split_into_chunks(extract_markdown())
    cases = load_cases()
    questions = [c["question"] for c in cases]

    rows = []
    for model in args.models:
        try:
            doc_vecs = embed_texts(client, model, [c.embedding_text() for c in chunks])
            query_vecs = embed_texts(client, model, questions)
        except Exception as exc:
            print(f"{model}: falhou ({type(exc).__name__}: {str(exc)[:80]})")
            continue
        for mode in ("dense", "hybrid"):
            rankings = []
            for q, qv in zip(questions, query_vecs):
                dense = doc_vecs @ qv
                scores = dense if mode == "dense" else hybrid_scores(q, chunks, dense)
                rankings.append([chunks[i].id for i in np.argsort(-scores)])
            result = evaluate(rankings, cases)
            rows.append((model, mode, result))
            print(f"{model:35s} {mode:6s} hit@1={result['hit@1']:.0%} hit@3={result['hit@3']:.0%} "
                  f"mrr={result['mrr']:.2f} misses={result['misses']}")

    lines = [
        "# Benchmark de recuperação (políticas)",
        "",
        f"{len(cases)} perguntas no estilo do cliente ([retrieval_cases.yaml](retrieval_cases.yaml)), "
        f"{len(chunks)} trechos do manual. `dense` = só embeddings; `hybrid` = embeddings + BM25 (fusão por rank).",
        "",
        "| Modelo de embedding | Modo | hit@1 | hit@3 | MRR | Perguntas fora do top 3 |",
        "|---|---|---|---|---|---|",
    ]
    for model, mode, r in rows:
        lines.append(
            f"| `{model}` | {mode} | {r['hit@1']:.0%} | {r['hit@3']:.0%} | {r['mrr']:.2f} | {'; '.join(r['misses']) or '—'} |"
        )
    out = EVALS_DIR / "results" / "retrieval_benchmark.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nRelatório: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
