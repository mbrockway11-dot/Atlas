
"""Rebalance Engine v3 loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


MTM_POSITIONS = Path("output/investment_mark_to_market/positions.csv")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")
TARGET_PORTFOLIO = Path("output/investment_alpha/alpha_portfolio.csv")
ACTION_REQUESTS = Path("output/investment_action_engine/portfolio_action_requests.csv")
ACTION_REPORT = Path("output/investment_action_engine/action_engine_report.json")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_rebalance_inputs() -> dict:
    return {
        "mtm_positions": load_csv(MTM_POSITIONS),
        "portfolio_state": load_json(PORTFOLIO_STATE),
        "target_portfolio": load_csv(TARGET_PORTFOLIO),
        "action_requests": load_csv(ACTION_REQUESTS),
        "action_report": load_json(ACTION_REPORT),
        "risk": load_json(RISK_REPORT),
    }
