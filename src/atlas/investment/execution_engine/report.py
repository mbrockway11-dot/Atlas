
"""Execution Engine v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.execution_engine.fills import simulate_execution
from atlas.investment.execution_engine.loader import load_execution_inputs
from atlas.investment.execution_engine.schema import new_batch
from atlas.investment.execution_engine.sequencer import sequence_orders
from atlas.investment.execution_engine.validator import validate_intents


OUT_DIR = Path("output/investment_execution_engine")
REPORT_JSON = OUT_DIR / "execution_engine_report.json"
REPORT_MD = OUT_DIR / "execution_engine_report.md"
ORDERS_CSV = OUT_DIR / "execution_engine_orders.csv"
LOG_CSV = OUT_DIR / "execution_log.csv"
FILLS_CSV = OUT_DIR / "execution_fills.csv"
COSTS_CSV = OUT_DIR / "execution_costs.csv"


def build_execution_engine_report(mode: str = "paper") -> dict[str, Any]:
    inputs = load_execution_inputs()
    batch = new_batch(mode=mode)

    validated = validate_intents(inputs["intents"], inputs["safety"], inputs["risk"])
    sequenced = sequence_orders(validated, inputs["execution_log"], batch)
    executed = [simulate_execution(order) for order in sequenced]

    executed_count = sum(1 for r in executed if r.get("execution_status") == "EXECUTED_SIMULATED")
    duplicate_count = sum(1 for r in executed if r.get("execution_status") == "DUPLICATE_TARGET")
    rejected_count = sum(1 for r in executed if r.get("execution_status") == "REJECTED_VALIDATION")

    report = {
        "success": True,
        "version": "execution_engine_v3",
        "summary": (
            f"Execution Engine v3 processed {len(executed)} order(s): "
            f"executed={executed_count}, duplicates={duplicate_count}, rejected={rejected_count}."
        ),
        "batch": batch,
        "mode": mode,
        "executed_count": executed_count,
        "duplicate_count": duplicate_count,
        "rejected_count": rejected_count,
        "orders": executed,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "orders_csv": str(ORDERS_CSV),
            "log_csv": str(LOG_CSV),
            "fills_csv": str(FILLS_CSV),
            "costs_csv": str(COSTS_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(report.get("orders", []))
    df.to_csv(ORDERS_CSV, index=False)

    fills = df[df.get("fill_status", pd.Series(dtype=str)) == "FILLED_SIMULATED"].copy() if not df.empty else pd.DataFrame()
    fills.to_csv(FILLS_CSV, index=False)

    cost_cols = [
        "execution_id", "asset", "requested_weight", "fee_bps", "slippage_bps",
        "fee_drag", "slippage_drag", "total_cost_drag"
    ]
    existing_cost_cols = [c for c in cost_cols if c in df.columns]
    df[existing_cost_cols].to_csv(COSTS_CSV, index=False) if existing_cost_cols else pd.DataFrame().to_csv(COSTS_CSV, index=False)

    if LOG_CSV.exists() and LOG_CSV.stat().st_size > 0:
        try:
            old = pd.read_csv(LOG_CSV)
            log = pd.concat([old, df], ignore_index=True)
        except Exception:
            log = df
    else:
        log = df

    log.to_csv(LOG_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Execution Engine v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Orders",
        "",
    ]

    for row in report.get("orders", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('action')}` "
            f"requested=`{row.get('requested_weight')}` filled=`{row.get('filled_weight')}` "
            f"status=`{row.get('execution_status')}`"
        )

    return "\n".join(lines) + "\n"
