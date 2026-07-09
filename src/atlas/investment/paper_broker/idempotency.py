
"""Paper Broker idempotency."""

from __future__ import annotations

import pandas as pd


def filter_new_orders(orders: pd.DataFrame, existing_fills: pd.DataFrame) -> pd.DataFrame:
    if orders.empty:
        return orders

    if existing_fills.empty or "idempotency_key" not in existing_fills.columns:
        return orders

    existing_keys = set(existing_fills["idempotency_key"].astype(str).tolist())

    return orders[
        ~orders["idempotency_key"].astype(str).isin(existing_keys)
    ].copy()
