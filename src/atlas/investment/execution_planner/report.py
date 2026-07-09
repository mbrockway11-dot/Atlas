
"""Execution Planner v2 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.execution_planner.loader import load_execution_planner_inputs
from atlas.investment.execution_planner.orders import build_execution_plan_from_rebalance


OUT_DIR = Path("output/investment_execution")
PLAN_CSV = OUT_DIR / "execution_plan.csv"
ORDERS_CSV = OUT_DIR / "execution_order_intents.csv"
REPORT_JSON = OUT_DIR / "execution_planner_report.json"
REPORT_MD = OUT_DIR / "execution_planner_report.md"


def build_execution_planner_report() -> dict[str, Any]:
    inputs = load_execution_planner_inputs()
    plan = build_execution_plan_from_rebalance(inputs["rebalance_orders"], inputs["risk"])

    order_intents = plan.copy()

    open_count = int((plan["execution_gate"] == "OPEN").sum()) if not plan.empty else 0
    blocked_count = int((plan["execution_gate"].astype(str).str.contains("BLOCKED")).sum()) if not plan.empty else 0

    report = {
        "success": True,
        "version": "execution_planner_v2",
        "summary": (
            f"Execution Planner v2 built {len(plan)} rebalance-driven planned order row(s). "
            f"Open={open_count}, blocked={blocked_count}."
        ),
        "source": "rebalance_orders",
        "plan_rows": int(len(plan)),
        "open_count": open_count,
        "blocked_count": blocked_count,
        "planned_positions": plan.to_dict("records") if not plan.empty else [],
        "order_intents": order_intents.to_dict("records") if not order_intents.empty else [],
        "outputs": {
            "plan_csv": str(PLAN_CSV),
            "orders_csv": str(ORDERS_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, plan, order_intents)
    return report


def write_outputs(report: dict[str, Any], plan: pd.DataFrame, orders: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plan.to_csv(PLAN_CSV, index=False)
    orders.to_csv(ORDERS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Execution Planner v2 Report",
        "",
        report.get("summary", ""),
        "",
        "## Order Intents",
        "",
    ]

    for row in report.get("order_intents", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('order_action')}` "
            f"weight=`{row.get('planned_weight')}` gate=`{row.get('execution_gate')}`"
        )

    return "\n".join(lines) + "\n"
