"""Terminal chat: python -m emporio_agent [--phone "(67) 99654-7821"] [--debug] [--model ...]"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import Agent, AgentResources
from .config import PROJECT_ROOT, Settings
from .session import Session
from .transcript import Transcript, format_tool_call

HELP = (
    "Converse normalmente. Comandos: [bold]/debug[/] mostra/oculta ferramentas e custos · "
    "[bold]/reset[/] nova conversa · [bold]/sair[/] encerra (a conversa é salva em conversations/sessions/)."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Duda — assistente virtual da Empório da Música")
    parser.add_argument("--phone", help="Simula o telefone do remetente no WhatsApp (identifica o cliente pelo canal).")
    parser.add_argument("--debug", action="store_true", help="Mostra as ferramentas chamadas, tokens e custo.")
    parser.add_argument("--model", help="Modelo do OpenRouter (padrão: LLM_MODEL ou anthropic/claude-haiku-5.5).")
    args = parser.parse_args(argv)

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")  # emojis/accents on Windows terminals
    console = Console()
    settings = Settings.from_env(llm_model=args.model)

    with console.status("Carregando catálogo e manual de políticas..."):
        resources = AgentResources.load(settings)

    def new_agent() -> Agent:
        return Agent(resources, Session(channel_phone=args.phone))

    agent = new_agent()
    debug = args.debug
    channel = f"WhatsApp simulado ({args.phone})" if args.phone else "chat anônimo"
    transcript = Transcript("Conversa no terminal", settings.llm_model, settings.today().strftime("%d/%m/%Y"), channel)

    console.print(Panel.fit(
        f"[bold magenta]Empório da Música[/] — Duda, assistente virtual\n"
        f"Modelo: [cyan]{settings.llm_model}[/] · Canal: {channel}"
        + (f" · Cliente: [green]{agent.session.customer_first_name}[/]" if agent.session.customer_first_name else "")
        + f"\n{HELP}",
        border_style="magenta",
    ))

    while True:
        try:
            user_text = console.input("\n[bold cyan]Você:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_text:
            continue
        if user_text.lower() in {"/sair", "/exit", "/quit"}:
            break
        if user_text.lower() == "/debug":
            debug = not debug
            console.print(f"[dim]debug {'ligado' if debug else 'desligado'}[/]")
            continue
        if user_text.lower() == "/reset":
            agent = new_agent()
            console.print("[dim]Nova conversa iniciada.[/]")
            continue

        try:
            with console.status("Duda está digitando..."):
                reply = agent.reply(user_text)
        except Exception as exc:  # network/API errors should not kill the chat
            console.print(f"[red]Erro ao falar com o modelo: {exc}[/]")
            continue

        if debug:
            for call in reply.tool_calls:
                console.print(f"[dim]🔧 {format_tool_call(call.name, call.arguments)} ({call.duration_ms} ms)[/]")
                console.print(f"[dim]   ↳ {json.dumps(call.result, ensure_ascii=False, default=str)[:300]}[/]")
            console.print(
                f"[dim]{reply.llm_calls} chamadas ao LLM · {reply.prompt_tokens}+{reply.completion_tokens} tokens · "
                f"US$ {reply.cost_usd:.5f} · {reply.latency_s:.1f}s[/]"
            )
        console.print(Panel(Markdown(reply.text), title="Duda", title_align="left", border_style="magenta"))
        transcript.add(user_text, reply)

    if transcript.entries:
        path = PROJECT_ROOT / "conversations" / "sessions" / f"{datetime.now():%Y%m%d-%H%M%S}.md"
        transcript.save(path)
        console.print(f"[dim]Conversa salva em {path}[/]")
    console.print("Até mais! 🎶")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
