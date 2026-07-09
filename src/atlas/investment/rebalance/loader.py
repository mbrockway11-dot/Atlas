
"""Rebalancing Engine loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PORTFOLIO_STATE_JSON = Path("output/investment_portfolio_state/portfolio_state.json")
ALPHA_PORTFOLIO_CSV = Path("output/investment_alpha/alpha_portfolio_latest.csv")
POSITION_MANAGER_JSON = Path("output/investment_position_manager/position_manager_report.json")
DECISION_JSON = Path("output/investment_decision/decision_engine_report.json")


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
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def load_rebalance_inputs() -> dict:
    return {
        "portfolio_state": load_json(PORTFOLIO_STATE_JSON),
        "target_portfolio": load_csv(ALPHA_PORTFOLIO_CSV),
        "position_manager": load_json(POSITION_MANAGER_JSON),
        "decision": load_json(DECISION_JSON),
    }
