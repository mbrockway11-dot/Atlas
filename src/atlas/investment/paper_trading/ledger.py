
"""Paper trade ledger."""

from __future__ import annotations

from datetime import datetime, UTC

import pandas as pd


def append_fills_to_ledger(existing: pd.DataFrame, fills: pd.DataFrame) -> pd.DataFrame:
    if fills.empty:
        return existing

    timestamp = datetime.now(UTC).isoformat()

    rows = []

    for _, row in fills.iterrows():
        if row.get("fill_status") != "FILLED_SIMULATED":
            continue

        rows.append({
            "timestamp": timestamp,
            "asset": row.get("asset"),
            "side": row.get("side"),
            "order_action": row.get("order_action"),
            "paper_weight": row.get("simulated_fill_weight"),
            "fee_drag": row.get("fee_drag"),
            "slippage_drag": row.get("slippage_drag"),
            "total_cost_drag": row.get("total_cost_drag"),
            "status": "PAPER_FILLED",
            "reason": row.get("reason"),
        })

    new_rows = pd.DataFrame(rows)

    if existing.empty:
        return new_rows

    if new_rows.empty:
        return existing

    return pd.concat([existing, new_rows], ignore_index=True)
