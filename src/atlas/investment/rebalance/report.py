
"""Rebalancing Engine report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.rebalance.loader import load_rebalance_inputs
from atlas.investment.rebalance.optimizer import (
    current_weights_from_state,
    optimize_rebalance,
    target_weights_from_alpha,
)
from atlas.investment.rebalance.order_generation import generate_rebalance_orders
from atlas.investment.rebalance.turnover import apply_turnover_controls


OUT_DIR = Path("output/investment_rebalance")
REPORT_JSON = OUT_DIR / "rebalance_report.json"
REPORT_MD = OUT_DIR / "rebalance_report.md"
REBALANCE_CSV = OUT_DIR / "rebalance_table.csv"
ORDERS_CSV = OUT_DIR / "rebalance_orders.csv"


def build_rebalance_report() -> dict[str, Any]:
    inputs = load_rebalance_inputs()

    current = current_weights_from_state(inputs["portfolio_state"])
    target = target_weights_from_alpha(inputs["target_portfolio"], inputs["decision"])

    rebalance = optimize_rebalance(current, target)
    controlled = apply_turnover_controls(rebalance)
    orders = generate_rebalance_orders(controlled)

    total_turnover = float(controlled.loc[controlled["asset"] != "CASH", "controlled_delta_weight"].abs().sum()) if not controlled.empty else 0.0

    report = {
        "success": True,
        "summary": (
            f"Rebalancing Engine generated {len(orders)} rebalance order(s) "
            f"with controlled turnover {round(total_turnover, 6)}."
        ),
        "total_turnover": round(total_turnover, 6),
        "order_count": int(len(orders)),
        "rebalance_table": controlled.to_dict("records"),
        "orders": orders.to_dict("records"),
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "rebalance_csv": str(REBALANCE_CSV),
            "orders_csv": str(ORDERS_CSV),
        },
    }

    write_outputs(report, controlled, orders)
    return report


def write_outputs(report: dict[str, Any], rebalance: pd.DataFrame, orders: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rebalance.to_csv(REBALANCE_CSV, index=False)
    orders.to_csv(ORDERS_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rebalancing Engine Report",
        "",
        report.get("summary", ""),
        "",
        f"- Total turnover: `{report.get('total_turnover')}`",
        f"- Order count: `{report.get('order_count')}`",
        "",
        "## Orders",
        "",
    ]

    for row in report.get("orders", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('rebalance_action')}` "
            f"delta=`{row.get('weight_delta')}`"
        )

    return "\n".join(lines) + "\n"
