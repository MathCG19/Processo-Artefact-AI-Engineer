"""Run the evaluation set against the agent.

    python evals/run_evals.py                      # all cases, default model
    python evals/run_evals.py --model anthropic/claude-sonnet-5.5
    python evals/run_evals.py --case preco_no_pix --case endereco
    python evals/run_evals.py --no-judge          # deterministic checks only

Each case runs in a fresh session. Deterministic checks (tools called, regex on the answer) are
combined with an LLM judge for behaviors that regex cannot capture (e.g. "refuses politely").
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from emporio_agent.agent import Agent, AgentResources
from emporio_agent.config import PROJECT_ROOT, RUNTIME_DIR, Settings
from emporio_agent.session import Session
from emporio_agent.textutils import strip_accents

EVALS_DIR = PROJECT_ROOT / "evals"

JUDGE_PROMPT = """Você é um avaliador rigoroso de um assistente virtual de uma loja de instrumentos musicais.

Critério a verificar:
{rubric}

Conversa:
{conversation}

Avalie SOMENTE o critério acima, com base apenas no que está escrito na conversa.
Responda apenas com um JSON: {{"pass": true ou false, "reason": "<uma frase curta em português>"}}"""


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def _matches(pattern: str, text: str) -> bool:
    return re.search(strip_accents(pattern), strip_accents(text), re.IGNORECASE) is not None


def _same(a, b) -> bool:
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a).strip().lower() == str(b).strip().lower()


def judge(client, model: str, rubric: str, transcript: str, attempts: int = 3) -> Check:
    raw = ""
    for _ in range(attempts):  # occasional empty/non-JSON outputs are retried
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": JUDGE_PROMPT.format(rubric=rubric, conversation=transcript)}],
            temperature=0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content or ""
        try:
            verdict = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
            return Check("juiz", bool(verdict.get("pass")), str(verdict.get("reason", "")))
        except (AttributeError, json.JSONDecodeError):
            # Malformed JSON (e.g. unescaped quotes in "reason"): read the verdict directly.
            match = re.search(r'"pass"\s*:\s*(true|false)', raw, re.I)
            if match:
                reason = re.search(r'"reason"\s*:\s*"(.*)', raw, re.S)
                return Check("juiz", match.group(1).lower() == "true", reason.group(1)[:200] if reason else "")
    return Check("juiz", False, f"resposta do juiz não parseável: {raw[:120]!r}")


def run_case(case: dict, resources: AgentResources, use_judge: bool, tickets_path: Path) -> dict:
    agent = Agent(resources, Session(channel_phone=case.get("phone")), tickets_path=tickets_path)
    started = time.perf_counter()
    replies, error = [], None
    try:
        for turn in case["turns"]:
            replies.append(agent.reply(turn))
    except Exception as exc:  # record API failures as failed cases instead of aborting the run
        error = f"{type(exc).__name__}: {exc}"

    calls = [tc for r in replies for tc in r.tool_calls]
    called = [tc.name for tc in calls]
    final = replies[-1].text if replies else ""
    all_text = "\n".join(r.text for r in replies)
    checks: list[Check] = []

    if error:
        checks.append(Check("execução", False, error))
    for tool in case.get("expect_tools", []):
        checks.append(Check(f"chamou {tool}", tool in called))
    if case.get("expect_any_tool"):
        options = case["expect_any_tool"]
        checks.append(Check(f"chamou um de {options}", any(t in called for t in options)))
    for tool in case.get("forbid_tools", []):
        checks.append(Check(f"não chamou {tool}", tool not in called))
    for tool, expected in case.get("expect_args", {}).items():
        ok = any(
            tc.name == tool and all(_same(tc.arguments.get(k), v) for k, v in expected.items()) for tc in calls
        )
        checks.append(Check(f"{tool} com {expected}", ok, str([tc.arguments for tc in calls if tc.name == tool])))
    for pattern in case.get("must_match", []):
        checks.append(Check(f"contém /{pattern}/", _matches(pattern, final)))
    for pattern in case.get("must_not_match", []):
        checks.append(Check(f"não contém /{pattern}/", not _matches(pattern, all_text)))

    conversation = "\n".join(
        f"Cliente: {turn}\nAssistente: {reply.text}" for turn, reply in zip(case["turns"], replies)
    )
    if use_judge and case.get("judge") and replies:
        checks.append(judge(resources.client, resources.settings.judge_model, case["judge"], conversation))

    return {
        "id": case["id"],
        "category": case.get("category", ""),
        "passed": all(c.ok for c in checks),
        "checks": [c.__dict__ for c in checks],
        "tools_called": called,
        "conversation": conversation,
        "latency_s": round(time.perf_counter() - started, 2),
        "llm_calls": sum(r.llm_calls for r in replies),
        "cost_usd": sum(r.cost_usd for r in replies),
        "turns": len(case["turns"]),
    }


def write_report(results: list[dict], settings: Settings, use_judge: bool) -> Path:
    passed = sum(r["passed"] for r in results)
    total_turns = sum(r["turns"] for r in results)
    total_cost = sum(r["cost_usd"] for r in results)
    total_latency = sum(r["latency_s"] for r in results)
    slug = settings.llm_model.replace("/", "_")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    results_dir = EVALS_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / f"{stamp}_{slug}.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Resultado dos evals — `{settings.llm_model}`",
        "",
        f"- Data: {datetime.now():%d/%m/%Y %H:%M} · Juiz: `{settings.judge_model if use_judge else 'desativado'}`",
        f"- **Casos aprovados: {passed}/{len(results)} ({passed / len(results):.0%})**",
        f"- Latência média por mensagem: {total_latency / max(total_turns, 1):.1f}s",
        f"- Custo do agente: US$ {total_cost:.4f} no total · US$ {total_cost / max(total_turns, 1):.5f} por mensagem (sem o juiz)",
        "",
        "| Caso | Categoria | Resultado | Ferramentas chamadas | Falhas |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        failures = "; ".join(f"{c['name']} ({c['detail']})" if c["detail"] else c["name"] for c in r["checks"] if not c["ok"])
        tools = ", ".join(dict.fromkeys(r["tools_called"])) or "—"
        lines.append(f"| `{r['id']}` | {r['category']} | {'✅' if r['passed'] else '❌'} | {tools} | {failures or '—'} |")
    report = results_dir / f"summary_{slug}.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="Modelo do agente (padrão: LLM_MODEL).")
    parser.add_argument("--judge-model", help="Modelo do juiz (padrão: JUDGE_MODEL).")
    parser.add_argument("--case", action="append", help="Rodar só este caso (pode repetir).")
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    console = Console()
    settings = Settings.from_env(llm_model=args.model, judge_model=args.judge_model)
    cases = yaml.safe_load((EVALS_DIR / "cases.yaml").read_text(encoding="utf-8"))
    if args.case:
        cases = [c for c in cases if c["id"] in args.case]

    resources = AgentResources.load(settings)
    tickets_path = RUNTIME_DIR / "eval_tickets.jsonl"
    console.print(f"Rodando {len(cases)} casos com [cyan]{settings.llm_model}[/]...")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda c: run_case(c, resources, not args.no_judge, tickets_path), cases))

    table = Table("Caso", "Resultado", "Falhas")
    for r in results:
        failures = "\n".join(f"{c['name']}: {c['detail']}" if c["detail"] else c["name"] for c in r["checks"] if not c["ok"])
        table.add_row(r["id"], "[green]PASS[/]" if r["passed"] else "[red]FAIL[/]", failures[:300])
    console.print(table)
    report = write_report(results, settings, not args.no_judge)
    passed = sum(r["passed"] for r in results)
    console.print(f"[bold]{passed}/{len(results)} casos aprovados[/] · relatório: {report}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
