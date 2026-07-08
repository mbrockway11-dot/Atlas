
"""Paper Trading report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.paper_trading.ledger import append_fills_to_ledger
from atlas.investment.paper_trading.loader import load_ledger, load_simulated_fills
from atlas.investment.paper_trading.portfolio import portfolio_from_fills


OUT_DIR = Path("output/investment_paper_trading")
LEDGER_CSV = OUT_DIR / "paper_trade_ledger.csv"
PORTFOLIO_CSV = OUT_DIR / "paper_portfolio.csv"
REPORT_JSON = OUT_DIR / "paper_trading_report.json"
REPORT_MD = OUT_DIR / "paper_trading_report.md"


def build_paper_trading_report() -> dict[str, Any]:
    fills = load_simulated_fills()
    existing_ledger = load_ledger()

    portfolio = portfolio_from_fills(fills)
    ledger = append_fills_to_ledger(existing_ledger, fills)

    risky = portfolio[portfolio["asset"] != "CASH"] if not portfolio.empty else pd.DataFrame()
    cash = portfolio[portfolio["asset"] == "CASH"] if not portfolio.empty else pd.DataFrame()

    summary = {
        "portfolio_rows": int(len(portfolio)),
        "ledger_rows": int(len(ledger)),
        "risky_weight": round(float(risky["paper_weight"].sum()), 6) if not risky.empty else 0.0,
        "cash_weight": round(float(cash["paper_weight"].sum()), 6) if not cash.empty else 0.0,
        "paper_equity": round(float(portfolio["paper_value"].sum()), 2) if not portfolio.empty else 0.0,
    }

    report = {
        "success": True,
        "summary": summary,
        "portfolio": portfolio.to_dict("records"),
        "latest_ledger_rows": ledger.tail(20).to_dict("records") if not ledger.empty else [],
        "text_summary": (
            f"Paper Trading portfolio built with risky weight {summary['risky_weight']} "
            f"and cash weight {summary['cash_weight']}."
        ),
        "outputs": {
            "ledger_csv": str(LEDGER_CSV),
            "portfolio_csv": str(PORTFOLIO_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, portfolio, ledger)
    return report


def write_outputs(report: dict[str, Any], portfolio: pd.DataFrame, ledger: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    portfolio.to_csv(PORTFOLIO_CSV, index=False)
    ledger.to_csv(LEDGER_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Paper Trading Report",
        "",
        report.get("text_summary", ""),
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(report.get("summary", {}), indent=2),
        "```",
        "",
        "## Portfolio",
        "",
    ]

    for row in report.get("portfolio", []):
        lines.append(
            f"- `{row.get('asset')}` side=`{row.get('side')}` "
            f"weight=`{row.get('paper_weight')}` value=`{row.get('paper_value')}`"
        )

    return "\n".join(lines) + "\n"
