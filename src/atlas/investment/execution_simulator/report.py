
"""Execution Simulator report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.execution_simulator.loader import load_order_intents
from atlas.investment.execution_simulator.simulator import simulate_execution


OUT_DIR = Path("output/investment_execution_simulator")
FILLS_CSV = OUT_DIR / "simulated_fills.csv"
REPORT_JSON = OUT_DIR / "execution_simulator_report.json"
REPORT_MD = OUT_DIR / "execution_simulator_report.md"


def build_execution_simulator_report() -> dict[str, Any]:
    orders = load_order_intents()
    result = simulate_execution(orders)

    report = {
        "success": result.get("success", False),
        "summary": result.get("summary", {}),
        "fills": result.get("fills", []),
        "text_summary": (
            f"Execution Simulator filled {result.get('summary', {}).get('filled_count', 0)} order(s), "
            f"waiting on {result.get('summary', {}).get('waiting_count', 0)}, "
            f"with estimated cost drag {result.get('summary', {}).get('total_cost_drag', 0.0)}."
        ),
        "outputs": {
            "fills_csv": str(FILLS_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("fills", [])).to_csv(FILLS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Execution Simulator Report",
        "",
        report.get("text_summary", ""),
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(report.get("summary", {}), indent=2),
        "```",
        "",
        "## Fills",
        "",
    ]

    for row in report.get("fills", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('order_action')}` "
            f"fill=`{row.get('simulated_fill_weight')}` status=`{row.get('fill_status')}` "
            f"cost=`{row.get('total_cost_drag')}`"
        )

    return "\n".join(lines) + "\n"
