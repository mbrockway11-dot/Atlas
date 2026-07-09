
"""Mark-to-Market v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.mark_to_market.equity_curve import append_equity_snapshot
from atlas.investment.mark_to_market.loader import load_mark_to_market_inputs
from atlas.investment.mark_to_market.pricing import latest_prices
from atlas.investment.mark_to_market.valuation import INITIAL_EQUITY, cash_value, value_positions


OUT_DIR = Path("output/investment_mark_to_market")
REPORT_JSON = OUT_DIR / "mark_to_market_report.json"
REPORT_MD = OUT_DIR / "mark_to_market_report.md"
POSITIONS_CSV = OUT_DIR / "positions.csv"
UNREALIZED_CSV = OUT_DIR / "unrealized_pnl.csv"
REALIZED_CSV = OUT_DIR / "realized_pnl.csv"
EQUITY_CURVE_CSV = OUT_DIR / "equity_curve.csv"


def build_mark_to_market_report() -> dict[str, Any]:
    inputs = load_mark_to_market_inputs()
    prices = latest_prices(inputs["price_data"])

    positions = value_positions(inputs["broker_positions"], inputs["broker_fills"], prices)
    cash = cash_value(inputs["cash_ledger"], positions)

    market_value = float(pd.to_numeric(positions.get("market_value", 0.0), errors="coerce").fillna(0.0).sum()) if not positions.empty else 0.0
    equity = cash + market_value
    pnl = equity - INITIAL_EQUITY
    pnl_pct = pnl / INITIAL_EQUITY if INITIAL_EQUITY else 0.0

    equity_snapshot, equity_curve = append_equity_snapshot(equity, cash, market_value, pnl, pnl_pct)

    report = {
        "success": True,
        "version": "mark_to_market_v3",
        "summary": (
            f"Mark-to-Market v3 valued {len(positions)} broker position(s). "
            f"Equity={round(equity, 2)}, PnL={round(pnl, 2)}, drawdown={equity_snapshot.get('drawdown')}."
        ),
        "source": "paper_broker_v3",
        "equity_snapshot": equity_snapshot,
        "positions": positions.to_dict("records") if not positions.empty else [],
        "prices": prices,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "positions_csv": str(POSITIONS_CSV),
            "unrealized_csv": str(UNREALIZED_CSV),
            "realized_csv": str(REALIZED_CSV),
            "equity_curve_csv": str(EQUITY_CURVE_CSV),
        },
    }

    write_outputs(report, positions, equity_curve)
    return report


def write_outputs(report: dict[str, Any], positions: pd.DataFrame, equity_curve: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    positions.to_csv(POSITIONS_CSV, index=False)
    positions.to_csv(UNREALIZED_CSV, index=False)
    pd.DataFrame().to_csv(REALIZED_CSV, index=False)
    equity_curve.to_csv(EQUITY_CURVE_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Mark-to-Market v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Positions",
        "",
    ]

    for row in report.get("positions", []):
        lines.append(
            f"- `{row.get('asset')}` value=`{round(float(row.get('market_value') or 0.0), 2)}` "
            f"unrealized=`{round(float(row.get('unrealized_pnl') or 0.0), 2)}`"
        )

    return "\n".join(lines) + "\n"
