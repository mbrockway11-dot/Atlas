
"""Execution Engine v3 cost model."""

from __future__ import annotations


FEE_BPS = 8
SLIPPAGE_BPS = 12


def estimate_costs(order: dict) -> dict:
    weight = float(order.get("requested_weight") or 0.0)

    fee_drag = weight * FEE_BPS / 10000
    slippage_drag = weight * SLIPPAGE_BPS / 10000
    total = fee_drag + slippage_drag

    return {
        "fee_bps": FEE_BPS,
        "slippage_bps": SLIPPAGE_BPS,
        "fee_drag": round(fee_drag, 8),
        "slippage_drag": round(slippage_drag, 8),
        "total_cost_drag": round(total, 8),
    }
