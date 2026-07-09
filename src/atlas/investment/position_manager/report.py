
"""Position Manager v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.position_manager.loader import load_position_manager_inputs
from atlas.investment.position_manager.rules import evaluate_position


OUT_DIR = Path("output/investment_position_manager")
REPORT_JSON = OUT_DIR / "position_manager_report.json"
REPORT_MD = OUT_DIR / "position_manager_report.md"
ACTIONS_CSV = OUT_DIR / "position_manager_actions.csv"


def build_position_manager_report() -> dict[str, Any]:
    inputs = load_position_manager_inputs()
    lifecycle = inputs["lifecycle"]
    risk = inputs["risk"]
    learning = inputs["learning"]

    actions = []

    if not lifecycle.empty:
        active = lifecycle[lifecycle["asset"] != "CASH"].copy()

        for _, row in active.iterrows():
            position = row.to_dict()
            position_id = position.get("position_id")

            for action in evaluate_position(position, risk, learning):
                action["position_id"] = position_id
                action["side"] = position.get("side")
                action["state"] = position.get("state")
                action["unrealized_pnl_pct"] = position.get("unrealized_pnl_pct")
                action["holding_age_hours"] = position.get("holding_age_hours")
                actions.append(action)

    counts = pd.Series([a["manager_action"] for a in actions]).value_counts().to_dict() if actions else {}

    report = {
        "success": True,
        "version": "position_manager_v3",
        "summary": f"Position Manager v3 produced {len(actions)} action row(s).",
        "action_counts": counts,
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
        "# Position Manager v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Actions",
        "",
    ]

    for row in report.get("actions", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('manager_action')}` reason=`{row.get('reason')}`"
        )

    return "\n".join(lines) + "\n"
