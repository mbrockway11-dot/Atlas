
"""Execution Engine loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BROKER_ORDERS = Path("output/investment_broker/broker_orders.csv")
SAFETY_REPORT = Path("output/investment_safety/trade_safety_report.json")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")


def load_csv(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_execution_inputs() -> dict:
    return {
        "broker_orders": load_csv(BROKER_ORDERS),
        "safety": load_json(SAFETY_REPORT),
        "risk": load_json(RISK_REPORT),
        "portfolio_state": load_json(PORTFOLIO_STATE),
    }
