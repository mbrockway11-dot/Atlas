
"""Rebalance Engine v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.rebalance.action_overlay import apply_action_requests
from atlas.investment.rebalance.loader import load_rebalance_inputs
from atlas.investment.rebalance.optimizer import optimize_targets
from atlas.investment.rebalance.order_generation import generate_rebalance_orders
from atlas.investment.rebalance.targets import current_weights, target_weights
from atlas.investment.rebalance.turnover import build_rebalance_table, total_turnover


OUT_DIR = Path("output/investment_rebalance")
REPORT_JSON = OUT_DIR / "rebalance_report.json"
REPORT_MD = OUT_DIR / "rebalance_report.md"
TABLE_CSV = OUT_DIR / "rebalance_table.csv"
ORDERS_CSV = OUT_DIR / "rebalance_orders.csv"


def build_rebalance_report() -> dict[str, Any]:
    inputs = load_rebalance_inputs()

    current = current_weights(inputs["mtm_positions"])
    raw_target = target_weights(inputs["target_portfolio"], current)
    action_adjusted = apply_action_requests(raw_target, current, inputs["action_requests"])
    optimized = optimize_targets(current, action_adjusted, inputs["risk"])

    table = build_rebalance_table(current, optimized)
    turnover = total_turnover(table)
    orders = generate_rebalance_orders(table)

    report = {
        "success": True,
        "version": "rebalance_engine_v3",
        "summary": (
            f"Rebalance Engine v3 optimized {len(table)} asset(s), "
            f"generated {len(orders)} order intent(s), turnover={turnover}."
        ),
        "current_weights": current,
        "raw_target_weights": raw_target,
        "action_adjusted_targets": action_adjusted,
        "optimized_targets": optimized,
        "total_turnover": turnover,
        "order_count": len(orders),
        "rebalance_table": table,
        "orders": orders,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "rebalance_csv": str(TABLE_CSV),
            "orders_csv": str(ORDERS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("rebalance_table", [])).to_csv(TABLE_CSV, index=False)
    pd.DataFrame(report.get("orders", [])).to_csv(ORDERS_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rebalance Engine v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Rebalance Table",
        "",
    ]

    for row in report.get("rebalance_table", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('rebalance_action')}` "
            f"current=`{row.get('current_weight')}` target=`{row.get('target_weight')}` "
            f"delta=`{row.get('signed_delta')}`"
        )

    return "\n".join(lines) + "\n"
