
"""Decision Engine loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import json


REGISTRY_CSV = Path("output/investment_strategy_registry/strategy_registry_signals.csv")
DIRECTION_JSON = Path("output/investment_direction/market_direction_report.json")
PORTFOLIO_CSV = Path("output/investment_alpha/alpha_portfolio_latest.csv")


def load_registry() -> pd.DataFrame:
    if not REGISTRY_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(REGISTRY_CSV)


def load_market_direction() -> dict:
    if not DIRECTION_JSON.exists():
        return {}
    return json.loads(DIRECTION_JSON.read_text(encoding="utf-8"))


def load_portfolio() -> pd.DataFrame:
    if not PORTFOLIO_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(PORTFOLIO_CSV)
