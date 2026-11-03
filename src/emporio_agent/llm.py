"""OpenRouter access through the OpenAI-compatible SDK (chat + embeddings)."""

from __future__ import annotations

import numpy as np
from openai import OpenAI

from .config import Settings


def make_client(settings: Settings) -> OpenAI:
    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=60,
        max_retries=3,  # SDK retries 429/5xx with exponential backoff
        default_headers={"X-Title": "Emporio da Musica - Agente de Atendimento"},
    )


def embed_texts(client: OpenAI, model: str, texts: list[str]) -> np.ndarray:
    """Return L2-normalized embeddings (so cosine similarity is a dot product)."""
    response = client.embeddings.create(model=model, input=texts)
    vectors = np.array(
        [item.embedding for item in sorted(response.data, key=lambda d: d.index)], dtype=np.float32
    )
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def usage_cost(usage) -> float:
    """OpenRouter adds the request cost (USD) to the usage object."""
    if usage is None:
        return 0.0
    extra = getattr(usage, "model_extra", None) or {}
    return float(extra.get("cost") or getattr(usage, "cost", 0) or 0)
