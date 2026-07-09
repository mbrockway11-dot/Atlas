
"""Performance v2 position tracker."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


PORTFOLIO_STATE_JSON = Path("output/investment_portfolio_state/portfolio_state.json")
PAPER_BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")


def load_portfolio_state() -> dict:
    if not PORTFOLIO_STATE_JSON.exists():
        return {}
    return json.loads(PORTFOLIO_STATE_JSON.read_text(encoding="utf-8"))


def load_broker_fills() -> pd.DataFrame:
    if not PAPER_BROKER_FILLS.exists():
        return pd.DataFrame()
    return pd.read_csv(PAPER_BROKER_FILLS)


def holdings_from_state(state_report: dict) -> pd.DataFrame:
    state = state_report.get("state", {}) or {}
    holdings = state.get("holdings", []) or []
    return pd.DataFrame(holdings)


def summarize_positions(holdings: pd.DataFrame) -> dict:
    if holdings.empty:
        return {"position_count": 0, "risky_weight": 0.0, "cash_weight": 1.0, "reserved_cash_weight": 0.0}

    risky = holdings[~holdings["asset"].isin(["CASH", "RESERVED_CASH"])]
    cash = holdings[holdings["asset"] == "CASH"]
    reserved = holdings[holdings["asset"] == "RESERVED_CASH"]

    return {
        "position_count": int(len(risky)),
        "risky_weight": round(float(pd.to_numeric(risky["paper_weight"], errors="coerce").fillna(0).sum()), 6) if not risky.empty else 0.0,
        "cash_weight": round(float(pd.to_numeric(cash["paper_weight"], errors="coerce").fillna(0).sum()), 6) if not cash.empty else 0.0,
        "reserved_cash_weight": round(float(pd.to_numeric(reserved["paper_weight"], errors="coerce").fillna(0).sum()), 6) if not reserved.empty else 0.0,
    }
