
"""Paper Broker loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.common.io import safe_read_csv


EXECUTION_ORDERS = Path("output/investment_execution_engine/execution_engine_orders.csv")
PAPER_BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
PAPER_BROKER_LEDGER = Path("output/investment_paper_broker/paper_broker_ledger.csv")


def load_execution_orders() -> pd.DataFrame:
    return safe_read_csv(EXECUTION_ORDERS)


def load_existing_fills() -> pd.DataFrame:
    return safe_read_csv(PAPER_BROKER_FILLS)


def load_existing_ledger() -> pd.DataFrame:
    return safe_read_csv(PAPER_BROKER_LEDGER)



def load_ledger() -> pd.DataFrame:
    return load_existing_ledger()
