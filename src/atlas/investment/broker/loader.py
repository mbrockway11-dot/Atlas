
"""Broker loader."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ORDERS_CSV = Path("output/investment_execution/execution_order_intents.csv")
SAFETY_JSON = Path("output/investment_safety/trade_safety_report.json")


def load_orders() -> pd.DataFrame:
    if not ORDERS_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(ORDERS_CSV)


def load_safety() -> dict:
    if not SAFETY_JSON.exists():
        return {}
    return json.loads(SAFETY_JSON.read_text(encoding="utf-8"))
