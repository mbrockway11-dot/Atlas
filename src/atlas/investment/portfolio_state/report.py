
"""Portfolio State v4 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.portfolio_state.loader import load_portfolio_state_inputs
from atlas.investment.portfolio_state.state import build_portfolio_state


OUT_DIR = Path("output/investment_portfolio_state")
REPORT_JSON = OUT_DIR / "portfolio_state.json"
REPORT_MD = OUT_DIR / "portfolio_state_report.md"
HOLDINGS_CSV = OUT_DIR / "portfolio_holdings.csv"
PENDING_CSV = OUT_DIR / "portfolio_pending_orders.csv"


def build_portfolio_state_report() -> dict[str, Any]:
    state = build_portfolio_state(load_portfolio_state_inputs())

    report = {
        "success": True,
        "version": "portfolio_state_v4",
        "summary": (
            f"Portfolio State v4 updated from MTM v4. "
            f"Equity={state['equity']['current_equity']}, "
            f"risky={state['exposure']['risky_weight']}, "
            f"cash={state['exposure']['cash_weight']}, "
            f"direction={state['direction']}."
        ),
        "state": state,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "holdings_csv": str(HOLDINGS_CSV),
            "pending_orders_csv": str(PENDING_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    state = report.get("state", {})
    pd.DataFrame(state.get("holdings", [])).to_csv(HOLDINGS_CSV, index=False)
    pd.DataFrame().to_csv(PENDING_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    state = report.get("state", {})

    lines = [
        "# Portfolio State v4 Report",
        "",
        report.get("summary", ""),
        "",
        "## Equity",
        "",
        "```json",
        json.dumps(state.get("equity", {}), indent=2),
        "```",
        "",
        "## Exposure",
        "",
        "```json",
        json.dumps(state.get("exposure", {}), indent=2),
        "```",
        "",
        "## Holdings",
        "",
    ]

    for row in state.get("holdings", []):
        lines.append(
            f"- `{row.get('asset')}` weight=`{row.get('weight')}` value=`{row.get('value')}`"
        )

    return "\n".join(lines) + "\n"
