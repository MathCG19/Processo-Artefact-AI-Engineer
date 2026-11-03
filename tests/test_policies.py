import os

import pytest

from emporio_agent.policies import extract_markdown, split_into_chunks

# Customer-style questions -> sections that contain the answer (any of them counts as a hit).
RETRIEVAL_CASES = [
    ("que horas a loja abre no sábado?", {"2"}),
    ("qual o endereço de vocês?", {"1.2", "0"}),
    ("aceitam pix? tem desconto?", {"3"}),
    ("posso parcelar em 10 vezes no cartão?", {"3.1", "3"}),
    ("me arrependi da compra, posso devolver?", {"4.1"}),
    ("meu violão chegou com defeito, e agora?", {"4.2", "8.1"}),
    ("quero trocar por outra cor", {"4.3"}),
    ("posso trocar a boquilha do saxofone?", {"4.4"}),
    ("quanto custa o frete aqui em Campo Grande?", {"5.1"}),
    ("vocês entregam em Dourados? demora quanto?", {"5.2"}),
    ("como faço pra rastrear meu pedido?", {"5.3"}),
    ("quando vai ter black friday?", {"6.1"}),
    ("o desconto do pix vale junto com a promoção?", {"6.2"}),
    ("qual a garantia dos instrumentos?", {"8.1", "8.2"}),
    ("vocês compartilham meus dados pessoais?", {"9"}),
    ("qual o número do whatsapp?", {"7.1", "1.2", "0"}),
]


def test_pdf_is_split_by_manual_sections():
    chunks = split_into_chunks(extract_markdown())
    ids = [c.id for c in chunks]
    for expected in ["2", "3.1", "4.1", "4.4", "5.2", "6.2", "8.3", "9"]:
        assert expected in ids
    # Page headers/footers are removed and tables survive as Markdown.
    joined = "\n".join(c.text for c in chunks)
    assert "Página 3" not in joined
    assert "|PIX|Pagamento à vista|" in joined


@pytest.mark.network
@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY") and not os.path.exists(".env"), reason="sem chave")
def test_retrieval_hit_rate():
    from emporio_agent.config import Settings
    from emporio_agent.llm import embed_texts, make_client
    from emporio_agent.policies import PolicyIndex

    settings = Settings.from_env()
    client = make_client(settings)
    index = PolicyIndex.build_or_load(lambda t: embed_texts(client, settings.embedding_model, t), settings.embedding_model)

    hits_at_1 = hits_at_3 = 0
    misses = []
    for question, expected in RETRIEVAL_CASES:
        top = [chunk.id for chunk, _ in index.search(question, k=3)]
        hits_at_1 += top[0] in expected
        hits_at_3 += bool(set(top) & expected)
        if not set(top) & expected:
            misses.append((question, top))
    n = len(RETRIEVAL_CASES)
    print(f"\nhit@1={hits_at_1}/{n}  hit@3={hits_at_3}/{n}  misses={misses}")
    assert hits_at_3 / n >= 0.9, misses
