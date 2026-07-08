
"""Run full Atlas investment pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


OUT_DIR = Path("output/investment_runbook")
REPORT_JSON = OUT_DIR / "daily_investment_runbook.json"
REPORT_MD = OUT_DIR / "daily_investment_runbook.md"


STEPS = [
    ("market_features", ["scripts/build_market_features.py", "--root", r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"]),
    ("alpha_hypotheses", ["scripts/generate_alpha_hypotheses.py"]),
    ("alpha_backtests", ["scripts/run_alpha_backtests.py", "--min-trades", "5"]),
    ("alpha_validation", ["scripts/validate_alpha_strategies.py", "--top-n", "25"]),
    ("alpha_ensemble", ["scripts/build_alpha_ensemble.py"]),
    ("cross_sectional_ranker", ["scripts/build_cross_sectional_alpha_ranker.py"]),
    ("alpha_portfolio", ["scripts/build_alpha_portfolio.py"]),
    ("sigil_v32_adapter", ["scripts/build_sigil_v32_adapter.py", "--root", r"C:\Projects\sigil-engine-git"]),
    ("strategy_registry", ["scripts/build_strategy_registry.py"]),
    ("adaptive_weighting", ["scripts/build_adaptive_weighting.py"]),
    ("market_direction", ["scripts/build_market_direction.py"]),
    ("decision_engine", ["scripts/build_decision_engine.py"]),
    ("execution_planner", ["scripts/build_execution_planner.py"]),
    ("execution_simulator", ["scripts/simulate_execution_plan.py"]),
]


def run_step(name: str, command: list[str]) -> dict:
    started = datetime.now().isoformat(timespec="seconds")

    proc = subprocess.run(
        [sys.executable, *command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    ended = datetime.now().isoformat(timespec="seconds")

    return {
        "name": name,
        "command": " ".join([sys.executable, *command]),
        "success": proc.returncode == 0,
        "returncode": proc.returncode,
        "started": started,
        "ended": ended,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_final_snapshot() -> dict:
    decision = load_json("output/investment_decision/decision_engine_report.json")
    execution = load_json("output/investment_execution/execution_planner_report.json")
    simulation = load_json("output/investment_execution_simulator/execution_simulator_report.json")
    direction = load_json("output/investment_direction/market_direction_report.json")

    return {
        "market_direction": direction.get("exposure", {}),
        "decision": decision.get("risk_adjusted_decision", {}),
        "execution_orders": execution.get("orders", []),
        "simulation_summary": simulation.get("summary", {}),
        "simulation_fills": simulation.get("fills", []),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for name, command in STEPS:
        print(f"RUNNING {name}...")
        result = run_step(name, command)
        results.append(result)

        print("OK" if result["success"] else "FAILED")
        if not result["success"]:
            break

    snapshot = build_final_snapshot()

    report = {
        "success": all(r["success"] for r in results),
        "started": results[0]["started"] if results else None,
        "ended": results[-1]["ended"] if results else None,
        "step_count": len(results),
        "steps": results,
        "final_snapshot": snapshot,
        "summary": build_summary(results, snapshot),
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")

    print(report["success"])
    print(report["summary"])
    print("JSON:", REPORT_JSON)
    print("Markdown:", REPORT_MD)


def build_summary(results: list[dict], snapshot: dict) -> str:
    decision = snapshot.get("decision", {})
    sim = snapshot.get("simulation_summary", {})

    return (
        f"Daily Investment Runbook completed {len(results)} step(s). "
        f"Decision: {decision.get('final_direction')} "
        f"confidence={decision.get('final_confidence')} "
        f"target_exposure={decision.get('target_net_exposure')}. "
        f"Simulated filled weight={sim.get('filled_weight')} "
        f"cash={sim.get('cash_weight')} "
        f"cost_drag={sim.get('total_cost_drag')}."
    )


def build_markdown(report: dict) -> str:
    lines = [
        "# Daily Investment Runbook",
        "",
        report.get("summary", ""),
        "",
        "## Final Snapshot",
        "",
        "```json",
        json.dumps(report.get("final_snapshot", {}), indent=2, default=str),
        "```",
        "",
        "## Steps",
        "",
    ]

    for step in report.get("steps", []):
        lines.extend([
            f"### {step.get('name')}",
            "",
            f"- Success: `{step.get('success')}`",
            f"- Return code: `{step.get('returncode')}`",
            "",
            "```text",
            (step.get("stdout") or "")[-3000:],
            "```",
            "",
        ])

        if step.get("stderr"):
            lines.extend([
                "Errors:",
                "",
                "```text",
                (step.get("stderr") or "")[-3000:],
                "```",
                "",
            ])

    return "\n".join(lines)


if __name__ == "__main__":
    main()
