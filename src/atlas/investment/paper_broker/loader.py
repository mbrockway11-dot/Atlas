
"""Paper Broker v3 loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from atlas.common.io import safe_read_csv


EXECUTION_FILLS = Path("output/investment_execution_engine/execution_fills.csv")
BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
BROKER_LEDGER = Path("output/investment_paper_broker/paper_broker_ledger.csv")
BROKER_POSITIONS = Path("output/investment_paper_broker/paper_broker_positions.csv")
CASH_LEDGER = Path("output/investment_paper_broker/paper_broker_cash_ledger.csv")


def load_execution_fills() -> pd.DataFrame:
    return safe_read_csv(EXECUTION_FILLS)


def load_existing_fills() -> pd.DataFrame:
    return safe_read_csv(BROKER_FILLS)


def load_ledger() -> pd.DataFrame:
    return safe_read_csv(BROKER_LEDGER)


def load_existing_positions() -> pd.DataFrame:
    return safe_read_csv(BROKER_POSITIONS)


def load_cash_ledger() -> pd.DataFrame:
    return safe_read_csv(CASH_LEDGER)


# Backward compatibility
def load_execution_orders() -> pd.DataFrame:
    return load_execution_fills()


def load_existing_ledger() -> pd.DataFrame:
    return load_ledger()
