
"""Action Engine v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.action_engine.loader import load_action_engine_inputs
from atlas.investment.action_engine.policy import apply_action_policy
from atlas.investment.action_engine.translator import translate_manager_action


OUT_DIR = Path("output/investment_action_engine")
REPORT_JSON = OUT_DIR / "action_engine_report.json"
REPORT_MD = OUT_DIR / "action_engine_report.md"
ACTIONS_CSV = OUT_DIR / "action_engine_actions.csv"
REQUESTS_CSV = OUT_DIR / "portfolio_action_requests.csv"


def build_action_engine_report() -> dict[str, Any]:
    inputs = load_action_engine_inputs()
    pm_actions = inputs["position_manager_actions"]
    risk = inputs["risk"]

    actions = []

    if not pm_actions.empty:
        for _, row in pm_actions.iterrows():
            translated = translate_manager_action(row.to_dict(), risk)
            actions.append(apply_action_policy(translated))

    actionable = [a for a in actions if a.get("action_status") == "ACTIONABLE"]

    counts = (
        pd.Series([a.get("portfolio_action") for a in actions]).value_counts().to_dict()
        if actions else {}
    )

    report = {
        "success": True,
        "version": "action_engine_v3",
        "summary": (
            f"Action Engine v3 translated {len(actions)} manager action(s) "
            f"into {len(actionable)} actionable portfolio request(s)."
        ),
        "action_counts": counts,
        "actions": actions,
        "portfolio_action_requests": actionable,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "actions_csv": str(ACTIONS_CSV),
            "requests_csv": str(REQUESTS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("actions", [])).to_csv(ACTIONS_CSV, index=False)
    pd.DataFrame(report.get("portfolio_action_requests", [])).to_csv(REQUESTS_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Action Engine v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Actions",
        "",
    ]

    for row in report.get("actions", []):
        lines.append(
            f"- `{row.get('asset')}` manager=`{row.get('manager_action')}` "
            f"portfolio=`{row.get('portfolio_action')}` status=`{row.get('action_status')}`"
        )

    return "\n".join(lines) + "\n"
