
"""Learning trade outcomes."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


LEDGER_CSV = Path("output/investment_paper_trading/paper_trade_ledger.csv")
PERFORMANCE_CSV = Path("output/investment_performance/performance_snapshots.csv")


def load_trade_outcomes() -> pd.DataFrame:
    if not LEDGER_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(LEDGER_CSV)


def load_performance_snapshots() -> pd.DataFrame:
    if not PERFORMANCE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(PERFORMANCE_CSV)
