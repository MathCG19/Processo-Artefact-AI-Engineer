"""Conversation session: history plus server-side identity state.

Identity lives here, not in the prompt. The LLM can ask a tool to look up an order, but only the
tool decides - based on this state and the contact supplied - whether the data may be returned.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

MAX_FAILED_VERIFICATIONS = 3


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    # Phone number supplied by the channel itself (e.g. WhatsApp sender). Trusted, unlike text
    # typed by the user. In the CLI it is simulated with --phone.
    channel_phone: str | None = None
    verified_customer_id: int | None = None
    customer_first_name: str | None = None
    failed_verifications: int = 0
    turns: list[list[dict]] = field(default_factory=list)  # one list of messages per user turn

    @property
    def verification_locked(self) -> bool:
        return self.failed_verifications >= MAX_FAILED_VERIFICATIONS

    def history(self, max_turns: int) -> list[dict]:
        return [msg for turn in self.turns[-max_turns:] for msg in turn]

    def reset(self) -> None:
        self.turns.clear()
