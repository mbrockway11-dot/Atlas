
"""Rebalance Engine v4 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.rebalance.loader import load_rebalance_inputs
from atlas.investment.rebalance.order_generation import generate_rebalance_orders
from atlas.investment.rebalance.optimizer import optimize_rebalance
from atlas.investment.rebalance.targets import extract_current_weights, extract_target_weights
from atlas.investment.rebalance.turnover import controlled_turnover


OUT_DIR = Path("output/investment_rebalance")
REPORT_JSON = OUT_DIR / "rebalance_report.json"
REPORT_MD = OUT_DIR / "rebalance_report.md"
TABLE_CSV = OUT_DIR / "rebalance_table.csv"
ORDERS_CSV = OUT_DIR / "rebalance_orders.csv"


def build_rebalance_report() -> dict[str, Any]:
    inputs = load_rebalance_inputs()

    targets = extract_target_weights(inputs["alpha_portfolio"])
    current = extract_current_weights(inputs["portfolio_holdings"], inputs["portfolio_state"])

    raw_rows = optimize_rebalance(current, targets)
    rows, turnover = controlled_turnover(raw_rows)
    orders = generate_rebalance_orders(rows)

    report = {
        "success": True,
        "version": "rebalance_engine_v4",
        "summary": (
            f"Rebalance Engine v4 compared Portfolio State v4 to Alpha Portfolio v3, "
            f"generated {len(orders)} order intent(s), turnover={turnover}."
        ),
        "text_summary": (
            f"Rebalance Engine v4 compared Portfolio State v4 to Alpha Portfolio v3, "
            f"generated {len(orders)} order intent(s), turnover={turnover}."
        ),
        "turnover": turnover,
        "current_weights": current,
        "target_weights": targets,
        "rows": rows,
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

    pd.DataFrame(report.get("rows", [])).to_csv(TABLE_CSV, index=False)
    pd.DataFrame(report.get("orders", [])).to_csv(ORDERS_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rebalance Engine v4 Report",
        "",
        report.get("summary", ""),
        "",
        "## Rebalance Rows",
        "",
    ]

    for row in report.get("rows", []):
        lines.append(
            f"- `{row.get('asset')}` current=`{row.get('current_weight')}` "
            f"target=`{row.get('target_weight')}` delta=`{row.get('signed_delta')}` "
            f"action=`{row.get('rebalance_action')}`"
        )

    lines += ["", "## Orders", ""]

    for row in report.get("orders", []):
        lines.append(
            f"- `{row.get('asset')}` {row.get('action')} delta=`{row.get('weight_delta')}`"
        )

    return "\n".join(lines) + "\n"
