import os
from pathlib import Path

import pytest
import yaml

from emporio_agent.config import PROJECT_ROOT
from emporio_agent.policies import extract_markdown, split_into_chunks

RETRIEVAL_CASES = yaml.safe_load((PROJECT_ROOT / "evals" / "retrieval_cases.yaml").read_text(encoding="utf-8"))


def test_pdf_is_split_by_manual_sections():
    chunks = split_into_chunks(extract_markdown())
    ids = [c.id for c in chunks]
    for expected in ["2", "3.1", "4.1", "4.4", "5.2", "6.2", "8.3", "9"]:
        assert expected in ids
    # Page headers/footers are removed and tables are linearized into "column: value" lines.
    joined = "\n".join(c.text for c in chunks)
    assert "Página 3" not in joined
    assert "- Endereço: Rua 14 de Maio, 3200" in joined
    assert "- PIX — Condições: Pagamento à vista; Observações: 5% de desconto" in joined
    assert "- Sábado: 09:00 às 13:00" in joined


@pytest.mark.network
@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY") and not Path(PROJECT_ROOT / ".env").exists(), reason="sem chave"
)
def test_retrieval_hit_rate():
    from emporio_agent.config import Settings
    from emporio_agent.llm import embed_texts, make_client
    from emporio_agent.policies import PolicyIndex

    settings = Settings.from_env()
    client = make_client(settings)
    index = PolicyIndex.build_or_load(lambda t: embed_texts(client, settings.embedding_model, t), settings.embedding_model)

    misses = []
    for case in RETRIEVAL_CASES:
        top = [chunk.id for chunk, _ in index.search(case["question"], k=3)]
        if not set(top) & set(case["expected_sections"]):
            misses.append((case["question"], top))
    # The agent sees the top 3 sections, so every question must have its answer there.
    assert not misses, misses
