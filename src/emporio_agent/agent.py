"""The agent loop: plain function calling against an OpenAI-compatible API (OpenRouter).

    user message
        -> LLM (system prompt + history + tool schemas)
        -> tool calls? execute them in Python, append results, call the LLM again
        -> final text answer
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI

from .catalog import catalog_overview
from .config import RUNTIME_DIR, Settings
from .data import StoreData, load_store_data
from .llm import embed_texts, make_client, usage_cost
from .orders import identify_by_channel_phone
from .policies import PolicyIndex
from .prompts import build_system_prompt
from .session import Session
from .tools import ToolContext, build_tool_schemas, execute_tool

FALLBACK_MESSAGE = (
    "Desculpe, não consegui concluir essa consulta agora. Quer que eu encaminhe sua mensagem "
    "para alguém da nossa equipe?"
)


@dataclass
class ToolCallRecord:
    name: str
    arguments: dict
    result: dict
    duration_ms: int


@dataclass
class AgentReply:
    text: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0


@dataclass
class AgentResources:
    """Heavy, shareable state: loaded once and reused by every session (CLI, evals, demos)."""

    settings: Settings
    client: OpenAI
    data: StoreData
    policies: PolicyIndex

    @classmethod
    def load(cls, settings: Settings) -> "AgentResources":
        client = make_client(settings)
        data = load_store_data()
        policies = PolicyIndex.build_or_load(
            lambda texts: embed_texts(client, settings.embedding_model, texts), settings.embedding_model
        )
        return cls(settings=settings, client=client, data=data, policies=policies)


class Agent:
    def __init__(self, resources: AgentResources, session: Session | None = None, tickets_path: Path | None = None):
        self.res = resources
        self.settings = resources.settings
        self.session = session or Session()
        identify_by_channel_phone(resources.data, self.session)
        self.tools = build_tool_schemas(resources.data)
        self.ctx = ToolContext(
            data=resources.data,
            policies=resources.policies,
            session=self.session,
            settings=self.settings,
            tickets_path=tickets_path or RUNTIME_DIR / "tickets.jsonl",
        )

    def _system_prompt(self) -> str:
        return build_system_prompt(
            self.settings.now(), self.session.customer_first_name, catalog_overview(self.res.data)
        )

    def reply(self, user_text: str) -> AgentReply:
        started = time.perf_counter()
        result = AgentReply(text="")
        turn: list[dict] = [{"role": "user", "content": user_text}]
        # The system prompt is rebuilt every turn: fresh clock and identity state.
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages += self.session.history(self.settings.max_history_turns) + turn

        for _ in range(self.settings.max_agent_steps):
            response = self.res.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                tools=self.tools,
                temperature=self.settings.temperature,
                max_tokens=1200,
            )
            result.llm_calls += 1
            if response.usage:
                result.prompt_tokens += response.usage.prompt_tokens or 0
                result.completion_tokens += response.usage.completion_tokens or 0
                result.cost_usd += usage_cost(response.usage)

            message = response.choices[0].message
            if not message.tool_calls:
                result.text = (message.content or "").strip() or FALLBACK_MESSAGE
                turn.append({"role": "assistant", "content": result.text})
                break

            assistant_msg = {
                "role": "assistant",
                "content": message.content or None,
                "tool_calls": [
                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in message.tool_calls
                ],
            }
            messages.append(assistant_msg)
            turn.append(assistant_msg)
            for tc in message.tool_calls:
                t0 = time.perf_counter()
                output = execute_tool(tc.function.name, tc.function.arguments, self.ctx)
                result.tool_calls.append(
                    ToolCallRecord(
                        name=tc.function.name,
                        arguments=_safe_json(tc.function.arguments),
                        result=output,
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                    )
                )
                tool_msg = {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(output, ensure_ascii=False, default=str)}
                messages.append(tool_msg)
                turn.append(tool_msg)
        else:
            # Step budget exhausted (tool loop). Fail safe instead of hanging.
            result.text = FALLBACK_MESSAGE
            turn.append({"role": "assistant", "content": result.text})

        self.session.turns.append(turn)
        result.latency_s = time.perf_counter() - started
        return result


def _safe_json(raw: str | None) -> dict:
    try:
        value = json.loads(raw) if raw else {}
        return value if isinstance(value, dict) else {"_raw": raw}
    except json.JSONDecodeError:
        return {"_raw": raw}
