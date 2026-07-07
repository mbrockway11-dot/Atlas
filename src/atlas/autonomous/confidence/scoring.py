
"""Scientific confidence scoring."""

from __future__ import annotations

from typing import Any


def score_scientific_confidence(
    *,
    evidence_count: int = 0,
    mean_evidence_confidence: float = 0.0,
    prediction_accuracy: str = "",
    falsification_status: str = "",
    replication_count: int = 0,
    sample_size: int = 0,
) -> dict[str, Any]:
    """Score scientific confidence from multiple research integrity factors."""
    evidence_score = min(1.0, evidence_count / 20) * 0.20
    confidence_score = clamp(mean_evidence_confidence) * 0.25
    prediction_score = prediction_accuracy_score(prediction_accuracy) * 0.20
    falsification_score = falsification_status_score(falsification_status) * 0.20
    replication_score = min(1.0, replication_count / 10) * 0.10
    sample_score = min(1.0, sample_size / 500) * 0.05

    total = round(
        evidence_score
        + confidence_score
        + prediction_score
        + falsification_score
        + replication_score
        + sample_score,
        6,
    )

    return {
        "scientific_confidence": total,
        "confidence_label": confidence_label(total),
        "components": {
            "evidence_score": round(evidence_score, 6),
            "confidence_score": round(confidence_score, 6),
            "prediction_score": round(prediction_score, 6),
            "falsification_score": round(falsification_score, 6),
            "replication_score": round(replication_score, 6),
            "sample_score": round(sample_score, 6),
        },
    }


def prediction_accuracy_score(label: str) -> float:
    """Convert prediction accuracy label to score."""
    return {
        "high_accuracy": 1.0,
        "moderate_accuracy": 0.75,
        "low_accuracy": 0.45,
        "poor_accuracy": 0.20,
    }.get(label, 0.0)


def falsification_status_score(status: str) -> float:
    """Convert falsification status to score."""
    return {
        "survived_initial_challenge": 1.0,
        "needs_more_evidence": 0.55,
        "weakened_by_counterexamples": 0.35,
        "challenged_by_contradiction": 0.10,
    }.get(status, 0.50)


def confidence_label(score: float) -> str:
    """Label scientific confidence."""
    if score >= 0.85:
        return "high_scientific_confidence"
    if score >= 0.70:
        return "moderate_scientific_confidence"
    if score >= 0.50:
        return "developing_scientific_confidence"
    return "low_scientific_confidence"


def clamp(value: float) -> float:
    """Clamp value to 0..1."""
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0
