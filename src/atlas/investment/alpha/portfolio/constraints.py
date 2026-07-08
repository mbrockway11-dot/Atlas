
"""Portfolio constraints."""

from __future__ import annotations

MAX_ASSET_WEIGHT = 0.40
MIN_CASH_WEIGHT = 0.10
MAX_TOTAL_RISK_EXPOSURE = 0.90


def clamp_weight(value: float, *, max_weight: float = MAX_ASSET_WEIGHT) -> float:
    return max(0.0, min(float(value), max_weight))
