
"""Campaign confidence scoring."""

from __future__ import annotations

from typing import Any


def score_campaign_confidence(campaign: dict[str, Any]) -> float:
    """Score campaign confidence from cycle history."""
    cycles = campaign.get("cycles", []) or []

    if not cycles:
        return 0.0

    scores = []

    for cycle in cycles:
        learning = cycle.get("learning_update", {}) or {}
        theory = cycle.get("theory", {}) or {}
        prediction = cycle.get("prediction", {}) or {}
        health = cycle.get("health", {}) or {}

        learning_score = float(learning.get("learning_score") or 0.0)
        theory_score = min(1.0, int(theory.get("promoted_count") or 0) * 0.35 + int(theory.get("candidate_count") or 0) * 0.10)
        prediction_score = prediction_confidence(prediction)
        health_score = 1.0 if health.get("healthy") else 0.50

        scores.append(
            learning_score * 0.35
            + theory_score * 0.25
            + prediction_score * 0.25
            + health_score * 0.15
        )

    return round(sum(scores) / len(scores), 6)


def prediction_confidence(prediction: dict[str, Any]) -> float:
    """Score prediction confidence."""
    if not prediction.get("success"):
        return 0.0

    scores = ((prediction.get("benchmark", {}) or {}).get("scores", {}) or {})
    label = scores.get("accuracy_label")

    return {
        "high_accuracy": 1.0,
        "moderate_accuracy": 0.75,
        "low_accuracy": 0.45,
        "poor_accuracy": 0.20,
    }.get(label, 0.25)


def campaign_label(confidence: float) -> str:
    """Label campaign confidence."""
    if confidence >= 0.85:
        return "high_confidence_campaign"
    if confidence >= 0.70:
        return "active_promising_campaign"
    if confidence >= 0.45:
        return "developing_campaign"
    return "early_campaign"
