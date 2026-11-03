from datetime import date

from emporio_agent.orders import get_order_status, identify_by_channel_phone, list_my_orders
from emporio_agent.session import Session

from .conftest import TODAY

ANA_EMAIL = "anacarol.ferreira@coldmail.com"   # customer 2, owner of order 8
ANA_PHONE = "(67) 99654-7821"


def test_order_requires_contact(data):
    result = get_order_status(data, Session(), TODAY, order_id=8)
    assert result["erro"] == "verificacao_necessaria"


def test_order_with_matching_email_or_phone_is_returned(data):
    for contact in [ANA_EMAIL, " AnaCarol.Ferreira@coldmail.com ", ANA_PHONE, "99654-7821", "+55 67 99654 7821"]:
        result = get_order_status(data, Session(), TODAY, order_id=8, contact=contact)
        assert result["codigo_de_rastreamento"] == "BRJL5544332BR", contact


def test_wrong_contact_and_missing_order_get_the_same_generic_denial(data):
    wrong_owner = get_order_status(data, Session(), TODAY, order_id=3, contact="lucas.mendes@jmail.com")
    missing = get_order_status(data, Session(), TODAY, order_id=999, contact="lucas.mendes@jmail.com")
    assert wrong_owner["mensagem"] == missing["mensagem"]
    assert "Isabela" not in str(wrong_owner)


def test_session_locks_after_repeated_failures(data):
    session = Session()
    for _ in range(3):
        get_order_status(data, session, TODAY, order_id=3, contact="intruso@x.com")
    locked = get_order_status(data, session, TODAY, order_id=8, contact=ANA_EMAIL)
    assert locked["erro"] == "verificacao_bloqueada"


def test_verified_session_cannot_read_other_customers_orders(data):
    session = Session()
    get_order_status(data, session, TODAY, order_id=8, contact=ANA_EMAIL)
    assert session.verified_customer_id == 2
    other = get_order_status(data, session, TODAY, order_id=3)   # belongs to customer 12
    assert "erro" in other


def test_channel_phone_identifies_customer_and_lists_orders(data):
    session = Session(channel_phone=ANA_PHONE)
    identify_by_channel_phone(data, session)
    assert session.customer_first_name == "Ana"
    orders = list_my_orders(data, session, TODAY)
    assert [o["order_id"] for o in orders["pedidos"]] == [8]


def test_list_orders_without_identity_is_refused(data):
    assert list_my_orders(data, Session(), TODAY)["erro"] == "cliente_nao_identificado"


def test_dates_are_computed_by_code(data):
    shipped = get_order_status(data, Session(), TODAY, order_id=8, contact=ANA_EMAIL)
    assert shipped["entrega_atrasada"] is True
    assert shipped["dias_de_atraso"] == (TODAY - date(2026, 2, 28)).days
    delivered = get_order_status(data, Session(), TODAY, order_id=7, contact="leticia.rocha@jmail.com")
    assert delivered["dias_desde_a_entrega"] == (TODAY - date(2026, 2, 17)).days
