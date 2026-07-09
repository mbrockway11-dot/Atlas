
"""Execution Planner v2 loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


REBALANCE_ORDERS = Path("output/investment_rebalance/rebalance_orders.csv")
REBALANCE_REPORT = Path("output/investment_rebalance/rebalance_report.json")
DECISION_REPORT = Path("output/investment_decision/decision_engine_report.json")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")


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


def load_execution_planner_inputs() -> dict:
    return {
        "rebalance_orders": load_csv(REBALANCE_ORDERS),
        "rebalance": load_json(REBALANCE_REPORT),
        "decision": load_json(DECISION_REPORT),
        "risk": load_json(RISK_REPORT),
        "portfolio_state": load_json(PORTFOLIO_STATE),
    }
