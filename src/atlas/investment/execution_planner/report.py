
"""Execution Planner report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.execution_planner.gating import apply_execution_gates
from atlas.investment.execution_planner.loader import load_decision, load_portfolio, load_registry
from atlas.investment.execution_planner.orders import build_order_intents
from atlas.investment.execution_planner.sizing import scale_portfolio_to_decision


OUT_DIR = Path("output/investment_execution")
PLAN_CSV = OUT_DIR / "execution_plan.csv"
ORDERS_CSV = OUT_DIR / "execution_order_intents.csv"
REPORT_JSON = OUT_DIR / "execution_planner_report.json"
REPORT_MD = OUT_DIR / "execution_planner_report.md"


def build_execution_planner_report() -> dict[str, Any]:
    decision = load_decision()
    portfolio = load_portfolio()
    registry = load_registry()

    plan = scale_portfolio_to_decision(portfolio, decision)
    gated = apply_execution_gates(plan, registry)
    orders = build_order_intents(gated)

    report = {
        "success": True,
        "summary": (
            f"Execution Planner built {len(gated)} planned position row(s) "
            f"and {len(orders)} order intent row(s)."
        ),
        "decision": decision.get("risk_adjusted_decision", {}),
        "plan": gated.to_dict("records"),
        "orders": orders.to_dict("records"),
        "outputs": {
            "plan_csv": str(PLAN_CSV),
            "orders_csv": str(ORDERS_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, gated, orders)
    return report


def write_outputs(report: dict[str, Any], plan: pd.DataFrame, orders: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plan.to_csv(PLAN_CSV, index=False)
    orders.to_csv(ORDERS_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Execution Planner Report",
        "",
        report.get("summary", ""),
        "",
        "## Decision",
        "",
        "```json",
        json.dumps(report.get("decision", {}), indent=2),
        "```",
        "",
        "## Order Intents",
        "",
    ]

    for row in report.get("orders", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('order_action')}` "
            f"side=`{row.get('side')}` weight=`{row.get('planned_weight')}` "
            f"gate=`{row.get('execution_gate')}`"
        )

    return "\n".join(lines) + "\n"
