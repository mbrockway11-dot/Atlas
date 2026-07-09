
"""Paper Broker v2 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.paper_broker.fills import simulate_paper_broker_fills
from atlas.investment.paper_broker.idempotency import filter_new_orders
from atlas.investment.paper_broker.ledger import append_fills
from atlas.investment.paper_broker.loader import load_execution_orders, load_existing_fills, load_ledger


OUT_DIR = Path("output/investment_paper_broker")
FILLS_CSV = OUT_DIR / "paper_broker_fills.csv"
LEDGER_CSV = OUT_DIR / "paper_broker_ledger.csv"
REPORT_JSON = OUT_DIR / "paper_broker_report.json"
REPORT_MD = OUT_DIR / "paper_broker_report.md"


def build_paper_broker_report() -> dict[str, Any]:
    orders = load_execution_orders()
    existing_fills = load_existing_fills()
    existing_ledger = load_ledger()

    new_orders = filter_new_orders(orders, existing_fills)
    new_fills = simulate_paper_broker_fills(new_orders)

    all_fills = append_fills(existing_fills, new_fills)
    ledger = append_fills(existing_ledger, new_fills)

    report = {
        "success": True,
        "summary": (
            f"Paper Broker v2 processed {len(new_orders)} new order(s) "
            f"and created {len(new_fills)} new fill(s)."
        ),
        "input_order_count": int(len(orders)),
        "new_order_count": int(len(new_orders)),
        "new_fill_count": int(len(new_fills)),
        "total_fill_count": int(len(all_fills)),
        "new_fills": new_fills.to_dict("records"),
        "outputs": {
            "fills_csv": str(FILLS_CSV),
            "ledger_csv": str(LEDGER_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, all_fills, ledger)
    return report


def write_outputs(report: dict[str, Any], fills: pd.DataFrame, ledger: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fills.to_csv(FILLS_CSV, index=False)
    ledger.to_csv(LEDGER_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Paper Broker v2 Report",
        "",
        report.get("summary", ""),
        "",
        f"- Input orders: `{report.get('input_order_count')}`",
        f"- New orders: `{report.get('new_order_count')}`",
        f"- New fills: `{report.get('new_fill_count')}`",
        f"- Total fills: `{report.get('total_fill_count')}`",
        "",
        "## New Fills",
        "",
    ]

    for row in report.get("new_fills", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('action')}` "
            f"weight=`{row.get('filled_weight')}` status=`{row.get('fill_status')}`"
        )

    return "\n".join(lines) + "\n"
