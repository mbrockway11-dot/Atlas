
"""Rebalance Engine v4 order generation."""

from __future__ import annotations


def generate_rebalance_orders(rows: list[dict]) -> list[dict]:
    orders = []

    priority = 1

    for row in rows:
        action = row.get("rebalance_action")

        if action not in {"BUY", "SELL"}:
            continue

        delta = float(row.get("abs_delta") or 0.0)

        if delta <= 0:
            continue

        orders.append({
            "asset": row.get("asset"),
            "action": action,
            "side": "LONG",
            "weight_delta": round(delta, 6),
            "signed_delta": row.get("signed_delta"),
            "current_weight": row.get("current_weight"),
            "target_weight": row.get("target_weight"),
            "order_type": "REBALANCE_INTENT",
            "priority": priority,
            "source": "rebalance_engine_v4",
            "reason": row.get("reason"),
        })

        priority += 1

    return orders
