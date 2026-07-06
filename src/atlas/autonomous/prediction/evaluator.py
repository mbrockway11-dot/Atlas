
"""Prediction evaluator."""

from __future__ import annotations

from typing import Any


def evaluate_prediction_readiness(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate if enough records exist for prediction challenge."""
    count = len(records)

    if count >= 100:
        readiness = "strong_sample"
    elif count >= 50:
        readiness = "usable_sample"
    elif count >= 20:
        readiness = "small_sample"
    else:
        readiness = "insufficient_sample"

    return {
        "success": True,
        "record_count": count,
        "readiness": readiness,
        "can_run_prediction": count >= 20,
    }
