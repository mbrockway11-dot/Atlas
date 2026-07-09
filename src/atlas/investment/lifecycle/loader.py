
"""Portfolio Lifecycle loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


PORTFOLIO_STATE = Path("output/investment_portfolio_state/portfolio_holdings.csv")
BROKER_ORDERS = Path("output/investment_broker/broker_orders.csv")
LIFECYCLE_CSV = Path("output/investment_lifecycle/position_lifecycle.csv")


def load_portfolio_holdings() -> pd.DataFrame:
    if not PORTFOLIO_STATE.exists():
        return pd.DataFrame()
    return pd.read_csv(PORTFOLIO_STATE)


def load_broker_orders() -> pd.DataFrame:
    if not BROKER_ORDERS.exists():
        return pd.DataFrame()
    return pd.read_csv(BROKER_ORDERS)


def load_lifecycle() -> pd.DataFrame:
    if not LIFECYCLE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(LIFECYCLE_CSV)
