"""Structured data layer: loads the CSVs once, cleans them and derives the fields the tools need.

Design rule: everything the agent says about prices, stock, promotions and orders comes from
here (deterministic code), never from the LLM's memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import DATA_DIR
from .textutils import contains_phrase, digits_only, normalize, tokens

# Brands that appear in the catalog. Used to detect descriptions that talk about a different
# brand than the product name (e.g. "Music Man Bass 1X" described as a "Fender Jazz Bass").
KNOWN_BRANDS = [
    "Music Man", "Yamaha", "Tagima", "Giannini", "Rozini", "Shelby", "Crafter", "Martin",
    "Taylor", "Takamine", "Kala", "Ohana", "Kalani", "Fender", "Gibson", "Ibanez", "PRS",
    "Pearl", "Tama", "Korg", "Nord", "Roland",
]

AVAILABILITY_LABELS = {
    "available": "disponível",
    "out_of_stock": "esgotado (temporariamente indisponível)",
    "discontinued": "descontinuado (saiu de linha)",
    "coming_soon": "em breve (ainda não está à venda)",
}

# Extra search terms per category, so "contrabaixo" finds "Baixos" and "piano" finds keyboards.
CATEGORY_SYNONYMS = {
    "Guitarras": "guitarra elétrica",
    "Baixos": "baixo contrabaixo bass",
    "Baterias e Percussão": "bateria percussão",
    "Teclados e Pianos": "teclado piano sintetizador synth",
    "Violões": "violão",
    "Ukuleles": "ukulele",
}

SPEC_LABELS = {
    "top": "tampo", "back_sides": "fundo e laterais", "neck": "braço", "body": "corpo",
    "strings": "cordas", "scale": "escala", "electronics": "captação/eletrônica", "color": "cor",
    "shells": "cascos", "pieces": "peças", "hardware": "ferragens", "keys": "teclas",
    "type": "tipo", "polyphony": "polifonia",
}
SPEC_VALUES = {"steel": "aço", "nylon": "nylon", "yes": "sim", "no": "não", "included": "inclusas"}


@dataclass
class StoreData:
    products: pd.DataFrame
    categories: pd.DataFrame
    customers: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    promotions: pd.DataFrame

    def product(self, product_id: int) -> pd.Series | None:
        rows = self.products[self.products.product_id == product_id]
        return None if rows.empty else rows.iloc[0]

    @property
    def category_names(self) -> list[str]:
        return self.categories.sort_values("category_id").name.tolist()


def availability_of(status: str, stock: int) -> str:
    """The product status wins over stock: a discontinued item with units left is not for sale."""
    if status == "discontinued":
        return "discontinued"
    if status == "coming_soon":
        return "coming_soon"
    if status == "active" and stock > 0:
        return "available"
    return "out_of_stock"


def detect_brand(name: str) -> str | None:
    for brand in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if contains_phrase(name, brand):
            return brand
    return None


def conflicting_brands(name: str, description: str) -> list[str]:
    """Brands mentioned in the description that differ from the brand in the product name."""
    brand = detect_brand(name)
    if brand is None:
        return []
    return sorted(b for b in KNOWN_BRANDS if b != brand and contains_phrase(description, b))


def translate_specs(specs: dict) -> dict:
    return {SPEC_LABELS.get(k, k): SPEC_VALUES.get(str(v), v) for k, v in specs.items()}


def _search_text(row: pd.Series) -> str:
    specs = row.specs
    tags = []
    if specs.get("strings") == "steel":
        tags.append("aço folk")
    if specs.get("strings") == "nylon":
        tags.append("nylon clássico")
    if specs.get("electronics") == "yes":
        tags.append("elétrico eletroacústico")
    parts = [row["name"], row.category_name, CATEGORY_SYNONYMS.get(row.category_name, ""), *tags]
    return " ".join(tokens(" ".join(parts)))


def load_store_data(data_dir: Path = DATA_DIR) -> StoreData:
    categories = pd.read_csv(data_dir / "categories.csv")
    products = pd.read_csv(data_dir / "products.csv")
    promotions = pd.read_csv(data_dir / "promotions.csv")
    customers = pd.read_csv(data_dir / "customers.csv", dtype={"phone": str})
    orders = pd.read_csv(data_dir / "orders.csv", dtype={"tracking_code": str, "notes": str})
    order_items = pd.read_csv(data_dir / "order_items.csv")

    # --- products -------------------------------------------------------------------------
    products = products.merge(
        categories[["category_id", "name"]].rename(columns={"name": "category_name"}),
        on="category_id",
        how="left",
    )
    products["specs"] = products["specs"].apply(lambda s: json.loads(s) if isinstance(s, str) else {})
    products["stock_quantity"] = products["stock_quantity"].fillna(0).astype(int)
    products["availability"] = [
        availability_of(s, q) for s, q in zip(products.status, products.stock_quantity)
    ]
    products["brand"] = products["name"].apply(detect_brand)
    products["description_conflict"] = [
        conflicting_brands(n, d) for n, d in zip(products["name"], products.description)
    ]

    # Only promotions flagged as active count. If a product had more than one active promotion,
    # the best one for the customer wins (promotions are not cumulative - policy 6.2).
    active = (
        promotions[promotions.is_active == 1]
        .sort_values("discount_percent", ascending=False)
        .drop_duplicates("product_id")
        .rename(columns={"description": "promo_name", "discount_percent": "promo_discount_pct"})
    )
    products = products.merge(
        active[["product_id", "promo_name", "promo_discount_pct"]], on="product_id", how="left"
    )
    products["final_price"] = (
        products.price_brl * (1 - products.promo_discount_pct.fillna(0) / 100)
    ).round(2)
    products["search_text"] = products.apply(_search_text, axis=1)

    # --- customers & orders ---------------------------------------------------------------
    customers["email_norm"] = customers.email.str.strip().str.lower()
    customers["phone_digits"] = customers.phone.apply(digits_only)
    for col in ("order_date", "estimated_delivery"):
        orders[col] = pd.to_datetime(orders[col], errors="coerce").dt.date
    orders["notes"] = orders["notes"].where(orders["notes"].notna(), None)
    orders["tracking_code"] = orders["tracking_code"].where(orders["tracking_code"].notna(), None)

    return StoreData(
        products=products,
        categories=categories,
        customers=customers,
        orders=orders,
        order_items=order_items,
        promotions=promotions,
    )


def resolve_category(data: StoreData, value: str | None) -> str | None:
    """Map free text ('violão', 'baixos', 'teclado') to the canonical category name."""
    if not value:
        return None
    wanted = set(tokens(value))
    for name in data.category_names:
        haystack = set(tokens(name + " " + CATEGORY_SYNONYMS.get(name, "")))
        if normalize(value) == normalize(name) or wanted & haystack:
            return name
    return None


def data_quality_report(data: StoreData) -> list[str]:
    """Human-readable list of the inconsistencies found and how the agent treats each one."""
    p, o = data.products, data.orders
    issues: list[str] = []

    for row in p[p.description_conflict.str.len() > 0].itertuples():
        issues.append(
            f"Produto {row.product_id} '{row.name}': descrição cita {', '.join(row.description_conflict)} "
            "-> descrição ocultada do agente; nome é a fonte da verdade."
        )
    for row in p[(p.status != "active") & (p.stock_quantity > 0)].itertuples():
        issues.append(
            f"Produto {row.product_id} '{row.name}': status '{row.status}' com {row.stock_quantity} "
            "unidades em estoque -> status prevalece (não vendável)."
        )
    for row in p[(p.status == "active") & (p.stock_quantity == 0)].itertuples():
        issues.append(f"Produto {row.product_id} '{row.name}': ativo sem estoque -> 'esgotado'.")

    empty = data.categories[~data.categories.category_id.isin(p.category_id)]
    if not empty.empty:
        issues.append(
            "Categorias sem nenhum produto: " + ", ".join(empty.name) + " -> agente não oferece."
        )

    dup = data.promotions.groupby("product_id").size()
    if (dup > 1).any():
        issues.append(
            "Produtos com mais de uma promoção cadastrada: "
            + ", ".join(map(str, dup[dup > 1].index.tolist()))
            + " -> só is_active=1 vale."
        )

    merged = data.order_items.merge(p[["product_id", "price_brl"]], on="product_id")
    merged["subtotal"] = merged.quantity * merged.price_brl
    sums = merged.groupby("order_id").subtotal.sum()
    for row in o.itertuples():
        expected = round(float(sums.get(row.order_id, 0)), 2)
        if abs(expected - row.total_brl) > 0.01:
            issues.append(
                f"Pedido {row.order_id}: total {row.total_brl} difere da soma dos itens {expected} "
                "-> agente usa o total do pedido (valor efetivamente cobrado)."
            )

    dup_email = data.customers[data.customers.email_norm.duplicated(keep=False)]
    if not dup_email.empty:
        issues.append(
            "Clientes com e-mail duplicado: "
            + ", ".join(map(str, dup_email.customer_id))
            + " -> verificação exige nº do pedido + contato."
        )
    return issues


if __name__ == "__main__":  # python -m emporio_agent.data
    for line in data_quality_report(load_store_data()):
        print("-", line)
