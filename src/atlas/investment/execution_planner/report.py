
"""Execution Planner v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.execution_planner.loader import load_execution_planner_inputs
from atlas.investment.execution_planner.planner import build_execution_plan


OUT_DIR = Path("output/investment_execution")
PLAN_CSV = OUT_DIR / "execution_plan.csv"
ORDER_INTENTS_CSV = OUT_DIR / "execution_order_intents.csv"
REPORT_JSON = OUT_DIR / "execution_planner_report.json"
REPORT_MD = OUT_DIR / "execution_planner_report.md"


EMPTY_ORDER_COLUMNS = [
    "asset", "side", "planned_weight", "signed_delta", "order_action",
    "execution_gate", "priority", "source", "order_type", "reason"
]


def build_execution_planner_report() -> dict[str, Any]:
    result = build_execution_plan(load_execution_planner_inputs())

    report = {
        "success": True,
        "version": "execution_planner_v3",
        "planner_status": result["planner_status"],
        "summary": result["summary"],
        "text_summary": result["summary"],
        "counts": result["counts"],
        "rebalance_turnover": result.get("rebalance_turnover", 0),
        "planned_orders": result["planned_orders"],
        "outputs": {
            "plan_csv": str(PLAN_CSV),
            "orders_csv": str(ORDER_INTENTS_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    orders = report.get("planned_orders", [])

    if orders:
        df = pd.DataFrame(orders)
    else:
        df = pd.DataFrame(columns=EMPTY_ORDER_COLUMNS)

    df.to_csv(PLAN_CSV, index=False)
    df.to_csv(ORDER_INTENTS_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Execution Planner v3 Report",
        "",
        report.get("summary", ""),
        "",
        f"Planner status: `{report.get('planner_status')}`",
        "",
        "## Planned Orders",
        "",
    ]

    orders = report.get("planned_orders", [])

    if not orders:
        lines.append("No rebalance needed. No execution order intents generated.")
    else:
        for row in orders:
            lines.append(
                f"- `{row.get('asset')}` {row.get('order_action')} weight=`{row.get('planned_weight')}`"
            )

    return "\n".join(lines) + "\n"
