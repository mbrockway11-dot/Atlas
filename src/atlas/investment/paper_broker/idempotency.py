
"""Paper Broker idempotency."""

from __future__ import annotations

import pandas as pd


def target_key(asset: str, side: str, action: str, weight: float) -> str:
    """Stable key across execution batches.

    Batch idempotency prevents duplicate fills inside one batch.
    Target idempotency prevents refilling the same target order on later batches.
    """
    return f"{asset}:{side}:{action}:{float(weight):.6f}"


def ensure_target_keys(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if "target_key" not in out.columns:
        out["target_key"] = out.apply(
            lambda r: target_key(
                str(r.get("asset")),
                str(r.get("side")),
                str(r.get("action")),
                float(r.get("weight", r.get("requested_weight", r.get("filled_weight", 0.0))) or 0.0),
            ),
            axis=1,
        )

    return out


def filter_new_orders(orders: pd.DataFrame, existing_fills: pd.DataFrame) -> pd.DataFrame:
    if orders.empty:
        return orders

    orders = ensure_target_keys(orders)

    if existing_fills.empty:
        return orders

    existing = ensure_target_keys(existing_fills)

    existing_batch_keys = set()
    if "idempotency_key" in existing.columns:
        existing_batch_keys = set(existing["idempotency_key"].astype(str).tolist())

    existing_target_keys = set()
    if "target_key" in existing.columns:
        existing_target_keys = set(existing["target_key"].astype(str).tolist())

    return orders[
        ~orders["idempotency_key"].astype(str).isin(existing_batch_keys)
        & ~orders["target_key"].astype(str).isin(existing_target_keys)
    ].copy()
