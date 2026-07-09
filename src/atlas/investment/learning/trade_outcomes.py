
"""Learning v2 trade/performance outcomes."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


PERFORMANCE_SNAPSHOTS = Path("output/investment_performance/performance_snapshots.csv")
PERFORMANCE_ATTRIBUTION = Path("output/investment_performance/performance_attribution.csv")
MTM_EQUITY_CURVE = Path("output/investment_mark_to_market/equity_curve.csv")
MTM_UNREALIZED = Path("output/investment_mark_to_market/unrealized_pnl.csv")
PAPER_BROKER_LEDGER = Path("output/investment_paper_broker/paper_broker_ledger.csv")


def load_performance_snapshots() -> pd.DataFrame:
    if not PERFORMANCE_SNAPSHOTS.exists():
        return pd.DataFrame()
    return pd.read_csv(PERFORMANCE_SNAPSHOTS)


def load_performance_attribution() -> pd.DataFrame:
    if not PERFORMANCE_ATTRIBUTION.exists():
        return pd.DataFrame()
    return pd.read_csv(PERFORMANCE_ATTRIBUTION)


def load_equity_curve() -> pd.DataFrame:
    if not MTM_EQUITY_CURVE.exists():
        return pd.DataFrame()
    return pd.read_csv(MTM_EQUITY_CURVE)


def load_unrealized_positions() -> pd.DataFrame:
    if not MTM_UNREALIZED.exists():
        return pd.DataFrame()
    return pd.read_csv(MTM_UNREALIZED)


def load_trade_outcomes() -> pd.DataFrame:
    if not PAPER_BROKER_LEDGER.exists():
        return pd.DataFrame()
    return pd.read_csv(PAPER_BROKER_LEDGER)
