"""Order tools with ownership verification (LGPD).

Authorization is enforced in code: an order is only returned when the session is already tied to
its owner (trusted channel phone or a previous successful check) or when the contact provided
matches the owner's e-mail/phone. Failures return the same generic message whether the order
exists or not, so the tool cannot be used to probe order numbers.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .data import StoreData
from .session import MAX_FAILED_VERIFICATIONS, Session
from .textutils import digits_only

STATUS_LABELS = {
    "pending": "pendente — aguardando confirmação do pagamento",
    "confirmed": "confirmado — pagamento aprovado, pedido em preparação (ainda não foi enviado)",
    "shipped": "enviado — em transporte",
    "delivered": "entregue",
    "cancelled": "cancelado",
}

GENERIC_DENIAL = (
    "Não foi possível verificar: não há pedido com esse número vinculado a esse contato. "
    "Peça ao cliente para conferir o número do pedido e o e-mail ou telefone usado na compra. "
    "Não diga se o pedido existe ou não."
)


def payment_label(method: str) -> str:
    if method.startswith("credit_"):
        return f"cartão de crédito em {method.removeprefix('credit_')}"
    return {"pix": "PIX", "debit": "cartão de débito", "boleto": "boleto bancário"}.get(method, method)


def contact_matches(customer: pd.Series, contact: str) -> bool:
    contact = (contact or "").strip()
    if not contact:
        return False
    if "@" in contact:
        return contact.lower() == customer.email_norm
    typed = digits_only(contact)
    if typed.startswith("55") and len(typed) >= 12:  # +55 country code
        typed = typed[2:]
    # Accept the number with or without area code, but require at least 8 digits.
    return len(typed) >= 8 and customer.phone_digits.endswith(typed)


def identify_by_channel_phone(data: StoreData, session: Session) -> None:
    """Tie the session to a customer when the channel provides a phone that is on file."""
    if not session.channel_phone:
        return
    digits = digits_only(session.channel_phone)
    matches = data.customers[data.customers.phone_digits.str.endswith(digits[-9:])] if len(digits) >= 8 else []
    if len(matches) == 1:
        customer = matches.iloc[0]
        session.verified_customer_id = int(customer.customer_id)
        session.customer_first_name = customer["name"].split()[0]


def _order_view(data: StoreData, order: pd.Series, today: date) -> dict:
    items = data.order_items[data.order_items.order_id == order.order_id].merge(
        data.products[["product_id", "name"]], on="product_id", how="left"
    )
    view = {
        "order_id": int(order.order_id),
        "status": STATUS_LABELS.get(order.status, order.status),
        "data_do_pedido": order.order_date.isoformat(),
        "dias_desde_o_pedido": (today - order.order_date).days,
        "itens": [{"produto": r["name"], "quantidade": int(r.quantity)} for _, r in items.iterrows()],
        "valor_total": float(order.total_brl),
        "forma_de_pagamento": payment_label(order.payment_method),
        "codigo_de_rastreamento": order.tracking_code,
        "observacoes": order.notes,
    }
    eta = order.estimated_delivery
    if pd.notna(eta) and eta is not None:
        view["previsao_de_entrega"] = eta.isoformat()
        if order.status == "shipped":
            late_by = (today - eta).days
            view["entrega_atrasada"] = late_by > 0
            if late_by > 0:
                view["dias_de_atraso"] = late_by
        if order.status == "delivered":
            # The data has no actual delivery date; the estimate is used as a proxy (README).
            view["data_de_entrega_considerada"] = eta.isoformat()
            view["dias_desde_a_entrega"] = (today - eta).days
            view["nota"] = "Data real de recebimento não registrada; usando a previsão de entrega como referência."
    return view


def get_order_status(
    data: StoreData, session: Session, today: date, order_id: int, contact: str | None = None
) -> dict:
    if session.verification_locked:
        return {
            "erro": "verificacao_bloqueada",
            "mensagem": "Muitas tentativas de verificação sem sucesso nesta conversa. "
            "Não tente de novo; ofereça encaminhar o cliente para um atendente humano.",
        }

    rows = data.orders[data.orders.order_id == int(order_id)]
    order = None if rows.empty else rows.iloc[0]
    owner_id = None if order is None else int(order.customer_id)

    authorized = owner_id is not None and session.verified_customer_id == owner_id
    if not authorized and contact:
        owner = data.customers[data.customers.customer_id == owner_id]
        authorized = not owner.empty and contact_matches(owner.iloc[0], contact)

    if not authorized:
        if not contact:
            return {
                "erro": "verificacao_necessaria",
                "mensagem": "Para consultar o pedido, peça o e-mail ou telefone cadastrado na compra.",
            }
        session.failed_verifications += 1
        remaining = MAX_FAILED_VERIFICATIONS - session.failed_verifications
        return {"erro": "verificacao_falhou", "mensagem": GENERIC_DENIAL, "tentativas_restantes": remaining}

    if session.verified_customer_id is None:
        session.verified_customer_id = owner_id
        owner_name = data.customers.loc[data.customers.customer_id == owner_id, "name"].iloc[0]
        session.customer_first_name = owner_name.split()[0]

    view = _order_view(data, order, today)
    view["cliente"] = session.customer_first_name if session.verified_customer_id == owner_id else None
    return view


def list_my_orders(data: StoreData, session: Session, today: date) -> dict:
    if session.verified_customer_id is None:
        return {
            "erro": "cliente_nao_identificado",
            "mensagem": "Para listar pedidos, peça o número de um pedido e o e-mail ou telefone "
            "usado na compra (use get_order_status).",
        }
    orders = data.orders[data.orders.customer_id == session.verified_customer_id]
    orders = orders.sort_values("order_date", ascending=False)
    return {
        "cliente": session.customer_first_name,
        "pedidos": [_order_view(data, o, today) for _, o in orders.iterrows()],
    }
