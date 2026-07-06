
"""Prediction scoring."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def score_predictions(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Score prediction rows."""
    valid = [
        item for item in predictions
        if item.get("absolute_error") is not None
    ]

    if not valid:
        return {
            "success": False,
            "prediction_count": len(predictions),
            "valid_prediction_count": 0,
            "mean_absolute_error": None,
            "targets": {},
        }

    target_buckets: dict[str, list[float]] = defaultdict(list)

    for item in valid:
        target_buckets[item.get("target")].append(float(item.get("absolute_error") or 0.0))

    target_scores = {}

    for target, errors in target_buckets.items():
        target_scores[target] = {
            "count": len(errors),
            "mean_absolute_error": round(sum(errors) / len(errors), 6),
            "max_absolute_error": round(max(errors), 6),
        }

    all_errors = [float(item.get("absolute_error") or 0.0) for item in valid]

    return {
        "success": True,
        "prediction_count": len(predictions),
        "valid_prediction_count": len(valid),
        "mean_absolute_error": round(sum(all_errors) / len(all_errors), 6),
        "max_absolute_error": round(max(all_errors), 6),
        "targets": target_scores,
        "accuracy_label": accuracy_label(sum(all_errors) / len(all_errors)),
    }


def accuracy_label(mean_absolute_error: float) -> str:
    """Label prediction accuracy."""
    if mean_absolute_error <= 0.05:
        return "high_accuracy"
    if mean_absolute_error <= 0.10:
        return "moderate_accuracy"
    if mean_absolute_error <= 0.20:
        return "low_accuracy"
    return "poor_accuracy"
