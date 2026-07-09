
"""Portfolio Lifecycle v2 loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")
MTM_POSITIONS = Path("output/investment_mark_to_market/positions.csv")
PAPER_BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
ACTION_ENGINE = Path("output/investment_action_engine/action_engine_report.json")
REBALANCE_REPORT = Path("output/investment_rebalance/rebalance_report.json")


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


def load_lifecycle_inputs() -> dict:
    return {
        "portfolio_state": load_json(PORTFOLIO_STATE),
        "mtm_positions": load_csv(MTM_POSITIONS),
        "paper_broker_fills": load_csv(PAPER_BROKER_FILLS),
        "action_engine": load_json(ACTION_ENGINE),
        "rebalance": load_json(REBALANCE_REPORT),
    }
