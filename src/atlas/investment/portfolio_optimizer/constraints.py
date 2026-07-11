"""Portfolio Optimizer v2 constraints."""

from __future__ import annotations


MAX_ASSET_WEIGHT = 0.40
MIN_ASSET_WEIGHT = 0.01
DEFAULT_CASH_FLOOR = 0.10
MAX_CASH_WEIGHT = 0.85

DEFAULT_TARGET_VOLATILITY = 0.45
MIN_TARGET_VOLATILITY = 0.15
MAX_TARGET_VOLATILITY = 0.75

MAX_SELECTED_ASSETS = 8
MIN_SELECTED_ASSETS = 2

COVARIANCE_LOOKBACK = 180
MIN_COVARIANCE_OBSERVATIONS = 30

COVARIANCE_SHRINKAGE = 0.25
TURNOVER_PENALTY = 0.20


def clamp(
    value: float,
    lower: float,
    upper: float,
) -> float:
    return max(
        lower,
        min(
            upper,
            float(value),
        ),
    )
