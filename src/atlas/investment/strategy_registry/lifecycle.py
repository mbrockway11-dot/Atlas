
"""Strategy Registry v3 lifecycle rules."""

from __future__ import annotations


def lifecycle_status(recommendation: str, confidence: float, learning_regime: str) -> str:
    recommendation = str(recommendation or "maintain").lower()

    if recommendation == "promote" and confidence >= 0.70 and learning_regime in {"improving", "flat"}:
        return "PROMOTE"

    if recommendation == "reduce":
        return "REDUCE"

    if confidence <= 0.25 and learning_regime == "deteriorating":
        return "REVIEW_RETIRE"

    return "MAINTAIN"


def next_weight_multiplier(status: str) -> float:
    if status == "PROMOTE":
        return 1.10
    if status == "REDUCE":
        return 0.75
    if status == "REVIEW_RETIRE":
        return 0.50
    return 1.00
