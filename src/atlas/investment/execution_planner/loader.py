
"""Execution Planner loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

DECISION_JSON = Path("output/investment_decision/decision_engine_report.json")
PORTFOLIO_CSV = Path("output/investment_alpha/alpha_portfolio_latest.csv")
REGISTRY_CSV = Path("output/investment_strategy_registry/strategy_registry_signals.csv")


def load_decision() -> dict:
    if not DECISION_JSON.exists():
        return {}
    return json.loads(DECISION_JSON.read_text(encoding="utf-8"))


def load_portfolio() -> pd.DataFrame:
    if not PORTFOLIO_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(PORTFOLIO_CSV)


def load_registry() -> pd.DataFrame:
    if not REGISTRY_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(REGISTRY_CSV)
