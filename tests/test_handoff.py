import json
from datetime import datetime

from emporio_agent.config import STORE_TZ
from emporio_agent.handoff import escalate_to_human
from emporio_agent.session import Session

NOW = datetime(2026, 11, 3, 14, 30, tzinfo=STORE_TZ)


def test_ticket_gets_protocol_and_is_persisted(tmp_path):
    path = tmp_path / "tickets.jsonl"
    session = Session(verified_customer_id=14)
    result = escalate_to_human(session, NOW, path, "problema_com_produto", "chiado no ukulele", order_id=7)
    assert result["protocolo"].startswith("EMP-20261103-")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["customer_id"] == 14 and record["order_id"] == 7 and record["type"] == "new"


def test_same_case_reuses_protocol_instead_of_duplicating(tmp_path):
    path = tmp_path / "tickets.jsonl"
    session = Session()
    first = escalate_to_human(session, NOW, path, "problema_com_produto", "chiado", order_id=7)
    second = escalate_to_human(session, NOW, path, "solicitacao_de_devolucao", "quer devolver", order_id=7)
    assert second["protocolo"] == first["protocolo"]
    assert second["ja_existia"] is True
    types = [json.loads(line)["type"] for line in path.read_text(encoding="utf-8").splitlines()]
    assert types == ["new", "update"]


def test_unknown_reason_falls_back_to_outro(tmp_path):
    session = Session()
    escalate_to_human(session, NOW, tmp_path / "t.jsonl", "motivo_inventado", "x")
    assert "motivo-outro" in session.tickets
