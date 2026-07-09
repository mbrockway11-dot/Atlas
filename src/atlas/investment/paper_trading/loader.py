
"""Paper Trading loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


FILLS_CSV = Path("output/investment_execution_simulator/simulated_fills.csv")
LEDGER_CSV = Path("output/investment_paper_trading/paper_trade_ledger.csv")


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_simulated_fills() -> pd.DataFrame:
    return safe_read_csv(FILLS_CSV)


def load_ledger() -> pd.DataFrame:
    return safe_read_csv(LEDGER_CSV)
