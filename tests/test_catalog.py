from emporio_agent.catalog import catalog_overview, get_product_details, search_products


def ids(result):
    return [p["product_id"] for p in result["produtos"]]


def test_browse_violoes_up_to_1000_lists_only_sellable_items(data):
    result = search_products(data, category="Violões", max_price=1000)
    found = ids(result)
    assert len(found) == 12
    assert 96 not in found    # out of stock
    assert 113 not in found   # discontinued
    prices = [p["preco_final"] for p in result["produtos"]]
    assert prices == sorted(prices)


def test_named_lookup_is_typo_and_format_tolerant(data):
    for query in ["Takamine GD20", "takamine gd-20", "takamini GD 20"]:
        assert ids(search_products(data, query=query)) == [95], query


def test_named_lookup_shows_unavailable_products_with_status(data):
    result = search_products(data, query="Giannini GF-3D")
    assert ids(result) == [96]
    assert result["produtos"][0]["disponibilidade"].startswith("esgotado")


def test_price_filter_uses_promotional_price(data):
    # Ohana CK-20 costs 549 but has an active 20% promotion -> 439.20
    result = search_products(data, category="Ukuleles", max_price=450)
    item = next(p for p in result["produtos"] if p["product_id"] == 121)
    assert item["promocao_ativa"] == {"nome": "Desconto Exclusivo", "desconto_percentual": 20, "preco_promocional": 439.2}


def test_unknown_items_return_empty_instead_of_guessing(data):
    assert search_products(data, query="saxofone")["produtos"] == []
    assert "erro" in search_products(data, category="Drones")
    # A real category with no products returns an explicit empty result.
    empty = search_products(data, category="sopro")
    assert empty["produtos"] == [] and "Não invente" in empty["observacao"]


def test_details_offer_alternatives_when_unavailable(data):
    details = get_product_details(data, 96)
    alternatives = details["alternativas_disponiveis"]
    assert alternatives and all(a["disponibilidade"] == "disponível" for a in alternatives)
    assert all(a["categoria"] == "Violões" for a in alternatives)


def test_details_hide_inconsistent_descriptions(data):
    details = get_product_details(data, 135)
    assert details["descricao"] is None
    assert "Fender" in details["alerta_qualidade_dados"]


def test_overview_marks_empty_categories(data):
    overview = "\n".join(catalog_overview(data))
    assert "Instrumentos de Sopro (Madeiras): nenhum produto" in overview
