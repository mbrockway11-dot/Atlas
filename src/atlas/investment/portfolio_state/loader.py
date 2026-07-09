
"""Portfolio State loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PAPER_PORTFOLIO = Path("output/investment_paper_trading/paper_portfolio.csv")
PAPER_LEDGER = Path("output/investment_paper_trading/paper_trade_ledger.csv")
PAPER_BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
PAPER_BROKER_LEDGER = Path("output/investment_paper_broker/paper_broker_ledger.csv")
BROKER_ORDERS = Path("output/investment_broker/broker_orders.csv")
PERFORMANCE_REPORT = Path("output/investment_performance/performance_report.json")
DECISION_REPORT = Path("output/investment_decision/decision_engine_report.json")


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


def load_portfolio_state_inputs() -> dict:
    return {
        "paper_portfolio": load_csv(PAPER_PORTFOLIO),
        "paper_ledger": load_csv(PAPER_LEDGER),
        "paper_broker_fills": load_csv(PAPER_BROKER_FILLS),
        "paper_broker_ledger": load_csv(PAPER_BROKER_LEDGER),
        "broker_orders": load_csv(BROKER_ORDERS),
        "performance": load_json(PERFORMANCE_REPORT),
        "decision": load_json(DECISION_REPORT),
    }
