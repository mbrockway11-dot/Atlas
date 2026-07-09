
"""Mark-to-Market v2 loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


PAPER_BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
MARKET_FEATURES = Path("output/investment_alpha/market_asset_features.csv")
EQUITY_CURVE = Path("output/investment_mark_to_market/equity_curve.csv")


def load_fills() -> pd.DataFrame:
    if not PAPER_BROKER_FILLS.exists():
        return pd.DataFrame()
    return pd.read_csv(PAPER_BROKER_FILLS)


def load_market_features() -> pd.DataFrame:
    if not MARKET_FEATURES.exists():
        return pd.DataFrame()
    return pd.read_csv(MARKET_FEATURES)


def load_equity_curve() -> pd.DataFrame:
    if not EQUITY_CURVE.exists():
        return pd.DataFrame()
    return pd.read_csv(EQUITY_CURVE)
