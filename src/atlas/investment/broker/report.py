
"""Broker Interface report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.broker.interface import build_broker_interface_payload


OUT_DIR = Path("output/investment_broker")
REPORT_JSON = OUT_DIR / "broker_interface_report.json"
REPORT_MD = OUT_DIR / "broker_interface_report.md"
ORDERS_CSV = OUT_DIR / "broker_orders.csv"


def build_broker_interface_report() -> dict[str, Any]:
    report = build_broker_interface_payload()
    report["outputs"] = {
        "json": str(REPORT_JSON),
        "markdown": str(REPORT_MD),
        "orders_csv": str(ORDERS_CSV),
    }
    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(report.get("orders", [])).to_csv(ORDERS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Broker Interface Report",
        "",
        report.get("summary", ""),
        "",
        "## Orders",
        "",
    ]

    for o in report.get("orders", []):
        lines.append(
            f"- `{o.get('asset')}` action=`{o.get('action')}` "
            f"weight=`{o.get('weight')}` broker=`{o.get('broker')}` status=`{o.get('status')}`"
        )

    return "\n".join(lines) + "\n"
