"""Markdown transcripts of conversations (used by the CLI and the demo-conversation script)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .agent import AgentReply


def format_tool_call(name: str, arguments: dict) -> str:
    args = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
    return f"{name}({args})"


@dataclass
class Transcript:
    title: str
    model: str
    date: str
    channel: str
    entries: list[tuple[str, AgentReply]] = field(default_factory=list)

    def add(self, user_text: str, reply: AgentReply) -> None:
        self.entries.append((user_text, reply))

    def to_markdown(self, description: str | None = None) -> str:
        total_cost = sum(r.cost_usd for _, r in self.entries)
        lines = [f"# {self.title}", ""]
        if description:
            lines += [description, ""]
        lines += [
            f"> **Modelo:** `{self.model}` · **Data de referência:** {self.date} · **Canal:** {self.channel}  ",
            f"> **Custo total:** US$ {total_cost:.4f} · As linhas 🔧 mostram as ferramentas que o agente chamou (não aparecem para o cliente).",
            "",
            "---",
            "",
        ]
        for user_text, reply in self.entries:
            lines += [f"**👤 Cliente:** {user_text}", ""]
            if reply.tool_calls:
                calls = " → ".join(f"`{format_tool_call(t.name, t.arguments)}`" for t in reply.tool_calls)
                lines += [f"> 🔧 {calls}", ""]
            lines += ["**🎸 Duda:**", "", reply.text, "", "---", ""]
        return "\n".join(lines)

    def save(self, path: Path, description: str | None = None) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(description), encoding="utf-8")
        return path
