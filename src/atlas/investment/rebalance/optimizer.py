
"""Rebalance Engine v4 optimizer."""

from __future__ import annotations


MIN_DELTA = 0.0005


def optimize_rebalance(current: dict[str, float], target: dict[str, float]) -> list[dict]:
    assets = sorted(set(current) | set(target))
    rows = []

    for asset in assets:
        current_weight = round(float(current.get(asset, 0.0)), 6)
        target_weight = round(float(target.get(asset, 0.0)), 6)
        signed_delta = round(target_weight - current_weight, 6)
        abs_delta = round(abs(signed_delta), 6)

        if asset == "CASH":
            action = "CASH_ADJUST"
        elif abs_delta < MIN_DELTA:
            action = "HOLD"
        elif signed_delta > 0:
            action = "BUY"
        else:
            action = "SELL"

        rows.append({
            "asset": asset,
            "current_weight": current_weight,
            "target_weight": target_weight,
            "signed_delta": signed_delta,
            "abs_delta": abs_delta,
            "rebalance_action": action,
            "reason": "Move Portfolio State v4 current weights toward Alpha Portfolio v3 adaptive targets.",
            "source": "rebalance_engine_v4",
        })

    return rows
