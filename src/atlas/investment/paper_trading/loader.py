
"""Paper trading loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

FILLS_CSV = Path("output/investment_execution_simulator/simulated_fills.csv")
LEDGER_CSV = Path("output/investment_paper_trading/paper_trade_ledger.csv")
PORTFOLIO_CSV = Path("output/investment_paper_trading/paper_portfolio.csv")


def load_simulated_fills() -> pd.DataFrame:
    if not FILLS_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(FILLS_CSV)


def load_ledger() -> pd.DataFrame:
    if not LEDGER_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(LEDGER_CSV)


def load_portfolio() -> pd.DataFrame:
    if not PORTFOLIO_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(PORTFOLIO_CSV)
