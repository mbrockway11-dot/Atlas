
"""Generate rebalance order intents."""

from __future__ import annotations


def generate_rebalance_orders(rows: list[dict]) -> list[dict]:
    orders = []

    for row in rows:
        action = row.get("rebalance_action")

        if action == "HOLD":
            continue

        orders.append({
            "asset": row.get("asset"),
            "action": action,
            "side": "LONG",
            "weight_delta": row.get("abs_delta"),
            "signed_delta": row.get("signed_delta"),
            "current_weight": row.get("current_weight"),
            "target_weight": row.get("target_weight"),
            "order_type": "REBALANCE_INTENT",
            "reason": row.get("reason"),
        })

    return orders
