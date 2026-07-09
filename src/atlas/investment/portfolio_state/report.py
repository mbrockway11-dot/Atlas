
"""Portfolio State report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.portfolio_state.loader import load_portfolio_state_inputs
from atlas.investment.portfolio_state.snapshots import append_state_snapshot
from atlas.investment.portfolio_state.state import build_portfolio_state


OUT_DIR = Path("output/investment_portfolio_state")
STATE_JSON = OUT_DIR / "portfolio_state.json"
REPORT_MD = OUT_DIR / "portfolio_state_report.md"
HOLDINGS_CSV = OUT_DIR / "portfolio_holdings.csv"
PENDING_ORDERS_CSV = OUT_DIR / "portfolio_pending_orders.csv"


def build_portfolio_state_report() -> dict[str, Any]:
    state = build_portfolio_state(load_portfolio_state_inputs())

    report = {
        "success": state.get("success", False),
        "summary": build_summary(state),
        "state": state,
        "outputs": {
            "json": str(STATE_JSON),
            "markdown": str(REPORT_MD),
            "holdings_csv": str(HOLDINGS_CSV),
            "pending_orders_csv": str(PENDING_ORDERS_CSV),
        },
    }

    write_outputs(report)
    return report


def build_summary(state: dict[str, Any]) -> str:
    if not state.get("success"):
        return state.get("error", "Portfolio State unavailable.")

    equity = state.get("equity", {}) or {}
    exposure = state.get("exposure", {}) or {}
    decision = state.get("decision", {}) or {}

    return (
        f"Portfolio State updated. Equity={equity.get('current_equity')}, "
        f"risky={exposure.get('risky_weight')}, cash={exposure.get('cash_weight')}, "
        f"reserved={exposure.get('reserved_cash_weight')}, direction={decision.get('direction')}."
    )


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    state = report.get("state", {}) or {}

    STATE_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")

    pd.DataFrame(state.get("holdings", [])).to_csv(HOLDINGS_CSV, index=False)
    pd.DataFrame(state.get("pending_orders", [])).to_csv(PENDING_ORDERS_CSV, index=False)

    if state.get("success"):
        append_state_snapshot(state)


def build_markdown(report: dict[str, Any]) -> str:
    state = report.get("state", {}) or {}

    lines = [
        "# Portfolio State Report",
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
            f"- `{row.get('asset')}` side=`{row.get('side')}` "
            f"weight=`{row.get('paper_weight')}` value=`{row.get('paper_value')}`"
        )

    return "\n".join(lines) + "\n"
