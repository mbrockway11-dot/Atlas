
"""Execution Engine report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.execution_engine.batch import new_execution_batch
from atlas.investment.execution_engine.guards import apply_execution_guards
from atlas.investment.execution_engine.loader import load_execution_inputs
from atlas.investment.execution_engine.normalizer import normalize_orders
from atlas.investment.execution_engine.router import route_orders


OUT_DIR = Path("output/investment_execution_engine")
REPORT_JSON = OUT_DIR / "execution_engine_report.json"
REPORT_MD = OUT_DIR / "execution_engine_report.md"
ORDERS_CSV = OUT_DIR / "execution_engine_orders.csv"


def build_execution_engine_report(mode: str = "paper") -> dict[str, Any]:
    inputs = load_execution_inputs()
    batch = new_execution_batch(mode=mode)

    broker_orders = inputs["broker_orders"]
    normalized = normalize_orders(broker_orders, batch_id=batch["execution_batch_id"])
    routed = route_orders(normalized, mode=mode)
    guarded = apply_execution_guards(routed, inputs["safety"], inputs["risk"], mode=mode)

    approved_count = int((guarded["execution_status"] == "APPROVED_FOR_EXECUTION").sum()) if not guarded.empty else 0
    blocked_count = int(len(guarded) - approved_count) if not guarded.empty else 0

    report = {
        "success": True,
        "summary": (
            f"Execution Engine prepared {approved_count} approved order(s) "
            f"and {blocked_count} blocked order(s) in {mode} mode."
        ),
        "batch": batch,
        "mode": mode,
        "approved_count": approved_count,
        "blocked_count": blocked_count,
        "orders": guarded.to_dict("records") if not guarded.empty else [],
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "orders_csv": str(ORDERS_CSV),
        },
    }

    write_outputs(report, guarded)
    return report


def write_outputs(report: dict[str, Any], orders: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    orders.to_csv(ORDERS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Execution Engine Report",
        "",
        report.get("summary", ""),
        "",
        "## Batch",
        "",
        "```json",
        json.dumps(report.get("batch", {}), indent=2),
        "```",
        "",
        "## Orders",
        "",
    ]

    for row in report.get("orders", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('action')}` "
            f"weight=`{row.get('weight')}` route=`{row.get('route')}` "
            f"status=`{row.get('execution_status')}`"
        )

    return "\n".join(lines) + "\n"
