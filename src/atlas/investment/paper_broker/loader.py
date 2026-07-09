
"""Paper Broker v2 loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


EXECUTION_ORDERS = Path("output/investment_execution_engine/execution_engine_orders.csv")
FILLS_CSV = Path("output/investment_paper_broker/paper_broker_fills.csv")
LEDGER_CSV = Path("output/investment_paper_broker/paper_broker_ledger.csv")


def load_execution_orders() -> pd.DataFrame:
    if not EXECUTION_ORDERS.exists():
        return pd.DataFrame()
    return pd.read_csv(EXECUTION_ORDERS)


def load_existing_fills() -> pd.DataFrame:
    if not FILLS_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(FILLS_CSV)


def load_ledger() -> pd.DataFrame:
    if not LEDGER_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(LEDGER_CSV)
