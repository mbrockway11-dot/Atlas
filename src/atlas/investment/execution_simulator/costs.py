
"""Execution cost model."""

from __future__ import annotations


DEFAULT_FEE_BPS = 8.0
DEFAULT_SLIPPAGE_BPS = 12.0


def estimate_cost(weight: float, *, fee_bps: float = DEFAULT_FEE_BPS, slippage_bps: float = DEFAULT_SLIPPAGE_BPS) -> dict:
    """Estimate round-trip independent one-way execution cost as portfolio-weight drag."""
    w = abs(float(weight or 0.0))
    fee = w * (fee_bps / 10000.0)
    slippage = w * (slippage_bps / 10000.0)
    total = fee + slippage

    return {
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "fee_drag": round(float(fee), 8),
        "slippage_drag": round(float(slippage), 8),
        "total_cost_drag": round(float(total), 8),
    }
