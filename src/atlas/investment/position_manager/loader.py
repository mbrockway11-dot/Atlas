
"""Position Manager v3 loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


LIFECYCLE_CSV = Path("output/investment_lifecycle/position_lifecycle.csv")
PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_state.json")
RISK_REPORT = Path("output/investment_risk/risk_engine_report.json")
LEARNING_REPORT = Path("output/investment_learning/learning_report.json")
ACTION_REPORT = Path("output/investment_action_engine/action_engine_report.json")


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


def load_position_manager_inputs() -> dict:
    return {
        "lifecycle": load_csv(LIFECYCLE_CSV),
        "portfolio_state": load_json(PORTFOLIO_STATE),
        "risk": load_json(RISK_REPORT),
        "learning": load_json(LEARNING_REPORT),
        "action_engine": load_json(ACTION_REPORT),
    }
