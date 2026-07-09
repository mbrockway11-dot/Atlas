
"""Execution order normalization."""

from __future__ import annotations

from uuid import uuid4

import pandas as pd


def normalize_orders(orders: pd.DataFrame, batch_id: str | None = None) -> pd.DataFrame:
    if orders.empty:
        return pd.DataFrame()

    batch = batch_id or str(uuid4())
    rows = []

    for _, row in orders.iterrows():
        asset = str(row.get("asset"))
        action = str(row.get("action")).upper()
        side = str(row.get("side")).upper()
        weight = float(row.get("weight") or 0.0)

        idempotency_key = f"{batch}:{asset}:{side}:{action}:{weight:.6f}"

        rows.append({
            "execution_batch_id": batch,
            "idempotency_key": idempotency_key,
            "asset": asset,
            "side": side,
            "action": action,
            "weight": round(weight, 6),
            "broker": row.get("broker", "paper"),
            "source_status": row.get("status"),
            "execution_status": "NORMALIZED",
        })

    return pd.DataFrame(rows)
