
"""Broker Interface loaders."""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


ORDERS_CSV = Path("output/investment_broker/broker_orders.csv")
SAFETY_REPORT = Path("output/investment_safety/trade_safety_report.json")


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def load_orders() -> pd.DataFrame:
    return safe_read_csv(ORDERS_CSV)


def load_safety_report() -> dict:
    if not SAFETY_REPORT.exists():
        return {}
    try:
        return json.loads(SAFETY_REPORT.read_text(encoding="utf-8"))
    except Exception:
        return {}



def load_safety() -> dict:
    return load_safety_report()
