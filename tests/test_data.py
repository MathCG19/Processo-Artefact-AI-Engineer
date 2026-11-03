from emporio_agent.data import availability_of, conflicting_brands, data_quality_report, resolve_category


def test_status_wins_over_stock():
    assert availability_of("discontinued", 13) == "discontinued"
    assert availability_of("coming_soon", 2) == "coming_soon"
    assert availability_of("active", 0) == "out_of_stock"
    assert availability_of("active", 5) == "available"


def test_detects_descriptions_that_mention_another_brand(data):
    flagged = set(data.products[data.products.description_conflict.str.len() > 0].product_id)
    assert flagged == {135, 137, 139, 140, 142, 144}
    assert conflicting_brands("Takamine GD20 Dreadnought Natural", "Violão Takamine com tampo") == []


def test_only_active_promotions_are_applied(data):
    promo = data.products.set_index("product_id")
    assert promo.loc[94, "promo_discount_pct"] == 8           # active
    assert promo.loc[94, "final_price"] == 5519.08
    assert promo.loc[96, "promo_discount_pct"] != promo.loc[96, "promo_discount_pct"]  # NaN: both inactive
    assert promo.loc[96, "final_price"] == 799.9


def test_category_resolution_handles_plural_accents_and_synonyms(data):
    assert resolve_category(data, "violão") == "Violões"
    assert resolve_category(data, "VIOLOES") == "Violões"
    assert resolve_category(data, "contrabaixo") == "Baixos"
    assert resolve_category(data, "piano") == "Teclados e Pianos"
    assert resolve_category(data, "saxofone") is None


def test_quality_report_lists_known_issues(data):
    report = "\n".join(data_quality_report(data))
    assert "Pedido 3" in report and "Pedido 20" in report
    assert "11, 43" in report
