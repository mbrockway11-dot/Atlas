
"""Action Engine v3 loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


POSITION_MANAGER_JSON = Path("output/investment_position_manager/position_manager_report.json")
POSITION_MANAGER_ACTIONS = Path("output/investment_position_manager/position_manager_actions.csv")
LIFECYCLE_CSV = Path("output/investment_lifecycle/position_lifecycle.csv")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")
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
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def load_action_engine_inputs() -> dict:
    return {
        "position_manager": load_json(POSITION_MANAGER_JSON),
        "position_manager_actions": load_csv(POSITION_MANAGER_ACTIONS),
        "lifecycle": load_csv(LIFECYCLE_CSV),
        "portfolio_state": load_json(PORTFOLIO_STATE),
        "risk": load_json(RISK_REPORT),
    }
