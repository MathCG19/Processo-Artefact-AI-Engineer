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
    protocol = f"EMP-{now:%Y%m%d}-{uuid.uuid4().hex[:4].upper()}"
    ticket = {
        "protocol": protocol,
        "created_at": now.isoformat(timespec="seconds"),
        "session_id": session.session_id,
        "customer_id": session.verified_customer_id,  # None if the customer was not verified
        "reason": reason,
        "order_id": order_id,
        "summary": summary,
    }
    tickets_path.parent.mkdir(parents=True, exist_ok=True)
    with tickets_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ticket, ensure_ascii=False) + "\n")
    return {
        "protocolo": protocol,
        "prazo_de_retorno": RESPONSE_SLA,
        "mensagem": "Solicitação registrada e encaminhada para a equipe de atendimento.",
    }
