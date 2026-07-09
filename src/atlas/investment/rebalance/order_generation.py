
"""Rebalance order generation."""

from __future__ import annotations

import pandas as pd


def generate_rebalance_orders(rebalance: pd.DataFrame) -> pd.DataFrame:
    if rebalance.empty:
        return pd.DataFrame()

    rows = []

    for _, row in rebalance.iterrows():
        asset = row.get("asset")

        if asset == "CASH":
            continue

        delta = float(row.get("controlled_delta_weight") or 0.0)

        if abs(delta) <= 0:
            action = "NO_ORDER"
        elif delta > 0:
            action = "BUY"
        else:
            action = "SELL"

        if action == "NO_ORDER":
            continue

        rows.append({
            "asset": asset,
            "rebalance_action": action,
            "weight_delta": round(abs(delta), 6),
            "signed_delta": round(delta, 6),
            "current_weight": row.get("current_weight"),
            "target_weight": row.get("target_weight"),
            "reason": "Rebalance current portfolio toward risk-adjusted target portfolio.",
        })

    return pd.DataFrame(rows)
