"""Human handoff: the agent does not refund, cancel or exchange anything itself - it registers a
ticket for the team (here a JSONL file standing in for a helpdesk/CRM integration)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from .session import Session

HANDOFF_REASONS = [
    "reclamacao",
    "atraso_na_entrega",
    "solicitacao_de_devolucao",
    "solicitacao_de_troca",
    "cancelamento",
    "problema_com_produto",
    "duvida_sem_resposta",
    "outro",
]

# Policy manual 7.3: complaints are forwarded to the person in charge, reply within 24 business hours.
RESPONSE_SLA = "até 24 horas úteis"


def escalate_to_human(
    session: Session,
    now: datetime,
    tickets_path: Path,
    reason: str,
    summary: str,
    order_id: int | None = None,
) -> dict:
    if reason not in HANDOFF_REASONS:
        reason = "outro"
    # One ticket per case per conversation: a second call about the same order (or, without an
    # order, the same reason) is appended to the existing ticket instead of opening a duplicate.
    case_key = f"pedido-{order_id}" if order_id else f"motivo-{reason}"
    existing = session.tickets.get(case_key)
    protocol = existing or f"EMP-{now:%Y%m%d}-{uuid.uuid4().hex[:4].upper()}"
    session.tickets[case_key] = protocol

    record = {
        "protocol": protocol,
        "type": "update" if existing else "new",
        "created_at": now.isoformat(timespec="seconds"),
        "session_id": session.session_id,
        "customer_id": session.verified_customer_id,  # None if the customer was not verified
        "reason": reason,
        "order_id": order_id,
        "summary": summary,
    }
    tickets_path.parent.mkdir(parents=True, exist_ok=True)
    with tickets_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if existing:
        return {
            "protocolo": protocol,
            "ja_existia": True,
            "prazo_de_retorno": RESPONSE_SLA,
            "mensagem": "Este caso já tinha um protocolo nesta conversa; a nova informação foi anexada a ele. "
            "Informe ao cliente o mesmo protocolo (não diga que abriu um novo).",
        }
    return {
        "protocolo": protocol,
        "prazo_de_retorno": RESPONSE_SLA,
        "mensagem": "Solicitação registrada e encaminhada para a equipe de atendimento.",
    }
