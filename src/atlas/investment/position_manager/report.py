
"""Position Manager report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.position_manager.entries import evaluate_entries
from atlas.investment.position_manager.exits import evaluate_exits
from atlas.investment.position_manager.loader import load_position_manager_inputs
from atlas.investment.position_manager.rebalance import evaluate_rebalance
from atlas.investment.position_manager.scaling import evaluate_scaling
from atlas.investment.position_manager.trailing_stop import evaluate_trailing_stops


OUT_DIR = Path("output/investment_position_manager")
REPORT_JSON = OUT_DIR / "position_manager_report.json"
REPORT_MD = OUT_DIR / "position_manager_report.md"
ACTIONS_CSV = OUT_DIR / "position_manager_actions.csv"


def build_position_manager_report() -> dict[str, Any]:
    inputs = load_position_manager_inputs()

    lifecycle = inputs["lifecycle"]
    portfolio_state = inputs["portfolio_state"]
    decision = inputs["decision"]
    learning = inputs["learning"]

    entry_actions = evaluate_entries(lifecycle, decision)
    scaling_actions = evaluate_scaling(lifecycle, portfolio_state)
    exit_actions = evaluate_exits(lifecycle, decision, learning)
    trailing_actions = evaluate_trailing_stops(lifecycle)
    rebalance = evaluate_rebalance(lifecycle, portfolio_state)

    actions = entry_actions + scaling_actions + exit_actions + trailing_actions

    report = {
        "success": True,
        "summary": (
            f"Position Manager produced {len(actions)} position action(s). "
            f"Rebalance action: {rebalance.get('manager_action')}."
        ),
        "rebalance": rebalance,
        "entry_actions": entry_actions,
        "scaling_actions": scaling_actions,
        "exit_actions": exit_actions,
        "trailing_actions": trailing_actions,
        "actions": actions,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "actions_csv": str(ACTIONS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("actions", [])).to_csv(ACTIONS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Position Manager Report",
        "",
        report.get("summary", ""),
        "",
        "## Rebalance",
        "",
        "```json",
        json.dumps(report.get("rebalance", {}), indent=2),
        "```",
        "",
        "## Actions",
        "",
    ]

    for row in report.get("actions", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('manager_action')}` "
            f"state=`{row.get('current_state')}` reason=`{row.get('reason')}`"
        )

    return "\n".join(lines) + "\n"
