
"""Paper Broker v3 idempotency."""

from __future__ import annotations

import pandas as pd


def filter_new_fills(execution_fills: pd.DataFrame, existing_broker_fills: pd.DataFrame) -> pd.DataFrame:
    if execution_fills.empty:
        return pd.DataFrame()

    fills = execution_fills.copy()

    if "stable_order_key" not in fills.columns:
        if "idempotency_key" in fills.columns:
            fills["stable_order_key"] = fills["idempotency_key"]
        else:
            fills["stable_order_key"] = ""

    existing_keys = set()

    if existing_broker_fills is not None and not existing_broker_fills.empty:
        if "stable_order_key" in existing_broker_fills.columns:
            existing_keys |= set(existing_broker_fills["stable_order_key"].astype(str).tolist())
        if "idempotency_key" in existing_broker_fills.columns:
            existing_keys |= set(existing_broker_fills["idempotency_key"].astype(str).tolist())

    return fills[~fills["stable_order_key"].astype(str).isin(existing_keys)].copy()


# Backward compatibility
def filter_new_orders(orders: pd.DataFrame, existing_fills: pd.DataFrame) -> pd.DataFrame:
    return filter_new_fills(orders, existing_fills)
