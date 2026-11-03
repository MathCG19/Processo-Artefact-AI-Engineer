"""Central configuration: paths, model choices and the store's reference clock."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
POLICY_PDF = DATA_DIR / "políticas_da_loja.pdf"
CACHE_DIR = PROJECT_ROOT / ".cache"
RUNTIME_DIR = PROJECT_ROOT / "runtime"

# The store is in Campo Grande/MS (UTC-4, no daylight saving time).
STORE_TZ = ZoneInfo("America/Campo_Grande")

DEFAULT_LLM_MODEL = "anthropic/claude-haiku-5.5"
DEFAULT_EMBEDDING_MODEL = "baai/bge-m3"  # chosen by evals/retrieval_benchmark.py
DEFAULT_JUDGE_MODEL = "anthropic/claude-sonnet-5.5"


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = DEFAULT_LLM_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    judge_model: str = DEFAULT_JUDGE_MODEL
    temperature: float = 0.2
    max_agent_steps: int = 6          # max LLM calls per user message (guards against tool loops)
    max_history_turns: int = 12       # user turns kept in the context window
    reference_date: date | None = None  # None -> "today" in the store's timezone

    @classmethod
    def from_env(cls, **overrides) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key and "api_key" not in overrides:
            raise RuntimeError(
                "OPENROUTER_API_KEY não definida. Copie .env.example para .env e preencha a chave."
            )
        ref = os.getenv("REFERENCE_DATE", "").strip()
        values = dict(
            api_key=api_key,
            llm_model=os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
            embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            judge_model=os.getenv("JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            reference_date=date.fromisoformat(ref) if ref else None,
        )
        values.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**values)

    def now(self) -> datetime:
        """Current time in the store's timezone (date can be pinned via REFERENCE_DATE)."""
        current = datetime.now(STORE_TZ)
        if self.reference_date:
            current = current.replace(
                year=self.reference_date.year,
                month=self.reference_date.month,
                day=self.reference_date.day,
            )
        return current

    def today(self) -> date:
        return self.now().date()
