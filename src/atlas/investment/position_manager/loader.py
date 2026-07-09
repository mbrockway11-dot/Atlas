
"""Position Manager loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


LIFECYCLE_CSV = Path("output/investment_lifecycle/position_lifecycle.csv")
PORTFOLIO_STATE_JSON = Path("output/investment_portfolio_state/portfolio_state.json")
DECISION_JSON = Path("output/investment_decision/decision_engine_report.json")
LEARNING_JSON = Path("output/investment_learning/learning_report.json")


def load_lifecycle() -> pd.DataFrame:
    if not LIFECYCLE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(LIFECYCLE_CSV)


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_position_manager_inputs() -> dict:
    return {
        "lifecycle": load_lifecycle(),
        "portfolio_state": load_json(PORTFOLIO_STATE_JSON),
        "decision": load_json(DECISION_JSON),
        "learning": load_json(LEARNING_JSON),
    }
