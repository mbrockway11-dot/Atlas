
"""Broker Ledger v4.1 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.broker_ledger.accounting import (
    build_authoritative_ledger,
)
from atlas.investment.broker_ledger.loader import (
    load_broker_ledger_inputs,
)


OUT_DIR = Path("output/investment_broker_ledger")
REPORT_JSON = OUT_DIR / "broker_ledger_report.json"
REPORT_MD = OUT_DIR / "broker_ledger_report.md"
TRADES_CSV = OUT_DIR / "broker_ledger_trades.csv"
POSITIONS_CSV = OUT_DIR / "broker_ledger_positions.csv"
CASH_CSV = OUT_DIR / "broker_ledger_cash.csv"


POSITION_COLUMNS = [
    "asset",
    "side",
    "net_weight",
    "market_value",
    "status",
    "source",
]

TRADE_COLUMNS = [
    "timestamp",
    "stable_order_key",
    "asset",
    "side",
    "action",
    "filled_weight",
    "notional_value",
    "fill_status",
    "source",
]


def build_broker_ledger_report() -> dict[str, Any]:
    result = build_authoritative_ledger(
        load_broker_ledger_inputs()
    )

    reconciliation = result["reconciliation"]

    report = {
        "success": True,
        "version": "broker_ledger_v4_1",
        "accounting_mode": result["accounting_mode"],
        "summary": (
            "Broker Ledger v4.1 loaded the authoritative Paper Broker "
            f"snapshot. Cash={result['cash']}, "
            f"market_value={result['market_value']}, "
            f"equity={result['equity']}, "
            f"balanced={reconciliation['balanced']}."
        ),
        "text_summary": (
            "Broker Ledger v4.1 loaded the authoritative Paper Broker "
            f"snapshot. Cash={result['cash']}, "
            f"market_value={result['market_value']}, "
            f"equity={result['equity']}, "
            f"balanced={reconciliation['balanced']}."
        ),
        "cash": result["cash"],
        "market_value": result["market_value"],
        "equity": result["equity"],
        "pnl": result["pnl"],
        "pnl_pct": result["pnl_pct"],
        "positions": result["positions"],
        "trades": result["trade_rows"],
        "reconciliation": reconciliation,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "trades_csv": str(TRADES_CSV),
            "positions_csv": str(POSITIONS_CSV),
            "cash_csv": str(CASH_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    positions = report.get("positions", [])
    trades = report.get("trades", [])

    (
        pd.DataFrame(positions)
        if positions
        else pd.DataFrame(columns=POSITION_COLUMNS)
    ).to_csv(POSITIONS_CSV, index=False)

    (
        pd.DataFrame(trades)
        if trades
        else pd.DataFrame(columns=TRADE_COLUMNS)
    ).to_csv(TRADES_CSV, index=False)

    pd.DataFrame([{
        "cash": report.get("cash"),
        "market_value": report.get("market_value"),
        "equity": report.get("equity"),
        "pnl": report.get("pnl"),
        "pnl_pct": report.get("pnl_pct"),
        "balanced": (
            report.get("reconciliation", {}) or {}
        ).get("balanced"),
    }]).to_csv(CASH_CSV, index=False)

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    REPORT_MD.write_text(
        build_markdown(report),
        encoding="utf-8",
    )


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Broker Ledger v4.1 Report",
        "",
        report.get("summary", ""),
        "",
        "## Reconciliation",
        "",
        "```json",
        json.dumps(
            report.get("reconciliation", {}),
            indent=2,
        ),
        "```",
        "",
        "## Positions",
        "",
    ]

    for row in report.get("positions", []):
        lines.append(
            f"- `{row.get('asset')}` "
            f"weight=`{row.get('net_weight')}` "
            f"value=`{row.get('market_value')}` "
            f"status=`{row.get('status')}`"
        )

    return "\n".join(lines) + "\n"
