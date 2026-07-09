
"""Portfolio State loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


MARK_TO_MARKET_REPORT = Path("output/investment_mark_to_market/mark_to_market_report.json")
MTM_POSITIONS = Path("output/investment_mark_to_market/positions.csv")
PAPER_BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
PAPER_BROKER_LEDGER = Path("output/investment_paper_broker/paper_broker_ledger.csv")
BROKER_ORDERS = Path("output/investment_broker/broker_orders.csv")
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
        "mtm_report": load_json(MARK_TO_MARKET_REPORT),
        "mtm_positions": load_csv(MTM_POSITIONS),
        "paper_broker_fills": load_csv(PAPER_BROKER_FILLS),
        "paper_broker_ledger": load_csv(PAPER_BROKER_LEDGER),
        "broker_orders": load_csv(BROKER_ORDERS),
        "decision": load_json(DECISION_REPORT),
    }
