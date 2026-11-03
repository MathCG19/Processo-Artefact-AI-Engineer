"""Catalog tools: product search and product details (deterministic, pandas-based)."""

from __future__ import annotations

import pandas as pd

from .data import AVAILABILITY_LABELS, StoreData, resolve_category, translate_specs
from .textutils import compact, format_brl, fuzzy_equal, tokens

DEFAULT_LIMIT = 15
MAX_LIMIT = 30


def _token_matches(query_token: str, product_tokens: set[str], product_compact: str) -> bool:
    if query_token in product_tokens:
        return True
    # Model codes typed with different spacing/hyphens: "gd 20", "gd-20", "gn15".
    if (len(query_token) >= 3 or any(c.isdigit() for c in query_token)) and query_token in product_compact:
        return True
    # Typos: "takamini" ~ "takamine".
    return any(fuzzy_equal(query_token, t) for t in product_tokens)


def _match_score(query: str, row: pd.Series) -> float:
    """Fraction of query terms found in the product's searchable text (0..1)."""
    q_tokens = tokens(query)
    if not q_tokens:
        return 1.0
    product_tokens = set(row.search_text.split())
    product_compact = compact(row["name"])
    hits = sum(_token_matches(t, product_tokens, product_compact) for t in q_tokens)
    return hits / len(q_tokens)


def product_summary(row: pd.Series) -> dict:
    promo = None
    if pd.notna(row.promo_discount_pct):
        promo = {
            "nome": row.promo_name,
            "desconto_percentual": int(row.promo_discount_pct),
            "preco_promocional": float(row.final_price),
        }
    summary = {
        "product_id": int(row.product_id),
        "nome": row["name"],
        "categoria": row.category_name,
        "preco": float(row.price_brl),
        "promocao_ativa": promo,
        "preco_final": float(row.final_price),
        "disponibilidade": AVAILABILITY_LABELS[row.availability],
    }
    if row.availability == "available":
        summary["estoque"] = int(row.stock_quantity)
    return summary


def search_products(
    data: StoreData,
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    include_unavailable: bool | None = None,
    limit: int = DEFAULT_LIMIT,
) -> dict:
    """Search the catalog by name/brand/model and/or filter by category and final price.

    Default availability rule: when the customer names a product (query given) we also show
    unavailable matches, so the agent can say "it's sold out" instead of "not found". When the
    customer is browsing (no query), only sellable items are listed.
    """
    df = data.products
    applied = {}

    if category:
        canonical = resolve_category(data, category)
        if canonical is None:
            return {
                "erro": f"Categoria '{category}' não existe.",
                "categorias_validas": data.category_names,
            }
        df = df[df.category_name == canonical]
        applied["categoria"] = canonical

    if include_unavailable is None:
        include_unavailable = bool(query)
    if not include_unavailable:
        df = df[df.availability == "available"]

    # Price filters use the final price (with any active promotion applied).
    if min_price is not None:
        df = df[df.final_price >= float(min_price)]
        applied["preco_minimo"] = float(min_price)
    if max_price is not None:
        df = df[df.final_price <= float(max_price)]
        applied["preco_maximo"] = float(max_price)

    df = df.assign(_unavailable=(df.availability != "available").astype(int))
    if query:
        applied["busca"] = query
        scores = [_match_score(query, r) for _, r in df.iterrows()]
        df = df.assign(_score=scores)
        # Prefer products that match every term ("Takamine GD20" -> only the GD20);
        # fall back to partial matches only if nothing matches fully.
        full = df[df._score >= 0.999]
        df = full if not full.empty else df[df._score >= 0.5]
        df = df.sort_values(["_score", "_unavailable", "final_price"], ascending=[False, True, True])
    else:
        df = df.sort_values(["_unavailable", "final_price"])

    limit = max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))
    results = [product_summary(r) for _, r in df.head(limit).iterrows()]
    response = {"filtros_aplicados": applied, "total_encontrado": int(len(df)), "produtos": results}
    if len(df) > limit:
        response["observacao"] = f"Mostrando {limit} de {len(df)}. Refine a busca se necessário."
    if not results:
        response["observacao"] = (
            "Nenhum produto encontrado com esses critérios. Não invente produtos; "
            "informe o cliente e, se fizer sentido, sugira outra faixa de preço ou categoria."
        )
    return response


def _alternatives(data: StoreData, row: pd.Series, n: int = 3) -> list[dict]:
    """Similar sellable products: same category, closest final price."""
    df = data.products
    pool = df[
        (df.category_name == row.category_name)
        & (df.availability == "available")
        & (df.product_id != row.product_id)
    ]
    if pool.empty:
        return []
    pool = pool.assign(_dist=(pool.final_price - row.final_price).abs()).sort_values("_dist")
    return [product_summary(r) for _, r in pool.head(n).iterrows()]


def get_product_details(data: StoreData, product_id: int) -> dict:
    row = data.product(int(product_id))
    if row is None:
        return {"erro": f"Produto {product_id} não encontrado. Use search_products para localizar o produto."}

    details = product_summary(row)
    details["especificacoes"] = translate_specs(row.specs)
    if row.description_conflict:
        details["descricao"] = None
        details["alerta_qualidade_dados"] = (
            "A descrição cadastrada deste produto cita outra marca "
            f"({', '.join(row.description_conflict)}) e é inconsistente com o nome. "
            "Não afirme detalhes além do nome, preço e disponibilidade; ofereça confirmar com a equipe."
        )
    else:
        details["descricao"] = row.description

    if row.availability != "available":
        details["alternativas_disponiveis"] = _alternatives(data, row)
    return details


def catalog_overview(data: StoreData) -> list[str]:
    """One line per category, used in the system prompt so the agent knows what exists."""
    lines = []
    sellable = data.products[data.products.availability == "available"]
    for name in data.category_names:
        items = sellable[sellable.category_name == name]
        if items.empty:
            lines.append(f"{name}: nenhum produto no catálogo no momento")
        else:
            lines.append(
                f"{name}: {len(items)} disponíveis, de {format_brl(items.final_price.min())} "
                f"a {format_brl(items.final_price.max())}"
            )
    return lines
