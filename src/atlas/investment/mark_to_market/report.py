
"""Mark-to-Market v2 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.mark_to_market.cost_basis import build_cost_basis
from atlas.investment.mark_to_market.equity_curve import append_equity_curve, build_equity_snapshot
from atlas.investment.mark_to_market.loader import load_equity_curve, load_fills, load_market_features
from atlas.investment.mark_to_market.pricing import latest_prices
from atlas.investment.mark_to_market.realized import realized_pnl
from atlas.investment.mark_to_market.unrealized import unrealized_pnl
from atlas.investment.mark_to_market.valuation import value_positions


OUT_DIR = Path("output/investment_mark_to_market")
REPORT_JSON = OUT_DIR / "mark_to_market_report.json"
REPORT_MD = OUT_DIR / "mark_to_market_report.md"
POSITIONS_CSV = OUT_DIR / "positions.csv"
UNREALIZED_CSV = OUT_DIR / "unrealized_pnl.csv"
REALIZED_CSV = OUT_DIR / "realized_pnl.csv"
EQUITY_CURVE_CSV = OUT_DIR / "equity_curve.csv"


def build_mark_to_market_report() -> dict[str, Any]:
    fills = load_fills()
    features = load_market_features()
    existing_curve = load_equity_curve()

    prices = latest_prices(features)
    basis = build_cost_basis(fills, prices)
    valued = value_positions(basis, prices)
    unrealized = unrealized_pnl(valued)
    realized = realized_pnl()
    snapshot = build_equity_snapshot(unrealized, existing_curve)
    equity_curve = append_equity_curve(existing_curve, snapshot)

    report = {
        "success": True,
        "version": "mark_to_market_v2",
        "summary": (
            f"Mark-to-Market v2 valued {len(unrealized)} open position(s). "
            f"Equity={snapshot['equity']}, PnL={snapshot['pnl']}, drawdown={snapshot['drawdown']}."
        ),
        "latest_prices": prices,
        "equity_snapshot": snapshot,
        "positions": unrealized.to_dict("records") if not unrealized.empty else [],
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "positions_csv": str(POSITIONS_CSV),
            "unrealized_csv": str(UNREALIZED_CSV),
            "realized_csv": str(REALIZED_CSV),
            "equity_curve_csv": str(EQUITY_CURVE_CSV),
        },
    }

    write_outputs(report, unrealized, realized, equity_curve)
    return report


def write_outputs(report: dict[str, Any], unrealized: pd.DataFrame, realized: pd.DataFrame, equity_curve: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    unrealized.to_csv(POSITIONS_CSV, index=False)
    unrealized.to_csv(UNREALIZED_CSV, index=False)
    realized.to_csv(REALIZED_CSV, index=False)
    equity_curve.to_csv(EQUITY_CURVE_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Mark-to-Market v2 Report",
        "",
        report.get("summary", ""),
        "",
        "## Equity Snapshot",
        "",
        "```json",
        json.dumps(report.get("equity_snapshot", {}), indent=2),
        "```",
        "",
        "## Positions",
        "",
    ]

    for row in report.get("positions", []):
        lines.append(
            f"- `{row.get('asset')}` value=`{round(float(row.get('market_value') or 0), 2)}` "
            f"unrealized=`{round(float(row.get('unrealized_pnl') or 0), 2)}`"
        )

    return "\n".join(lines) + "\n"
