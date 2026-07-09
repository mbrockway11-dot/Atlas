
"""Mark-to-Market v3 loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from atlas.common.io import safe_read_csv


BROKER_POSITIONS = Path("output/investment_paper_broker/paper_broker_positions.csv")
BROKER_FILLS = Path("output/investment_paper_broker/paper_broker_fills.csv")
CASH_LEDGER = Path("output/investment_paper_broker/paper_broker_cash_ledger.csv")
PRICE_DATA = Path("output/price_data.csv")


def load_broker_positions() -> pd.DataFrame:
    return safe_read_csv(BROKER_POSITIONS)


def load_broker_fills() -> pd.DataFrame:
    return safe_read_csv(BROKER_FILLS)


def load_cash_ledger() -> pd.DataFrame:
    return safe_read_csv(CASH_LEDGER)


def load_price_data() -> pd.DataFrame:
    return safe_read_csv(PRICE_DATA)


def load_mark_to_market_inputs() -> dict:
    return {
        "broker_positions": load_broker_positions(),
        "broker_fills": load_broker_fills(),
        "cash_ledger": load_cash_ledger(),
        "price_data": load_price_data(),
    }
