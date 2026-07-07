
"""Scientific confidence input extractors."""

from __future__ import annotations

from typing import Any


def extract_confidence_inputs(autonomous_report: dict[str, Any]) -> dict[str, Any]:
    """Extract scoring inputs from autonomous report."""
    evidence_registry = autonomous_report.get("evidence_registry", {}) or {}
    evidence_records = list((evidence_registry.get("records", {}) or {}).values())

    theory = autonomous_report.get("theory", {}) or {}
    prediction = autonomous_report.get("prediction", {}) or {}
    falsification = autonomous_report.get("falsification", {}) or {}

    prediction_scores = ((prediction.get("benchmark", {}) or {}).get("scores", {}) or {})
    challenges = falsification.get("challenges", []) or []

    return {
        "evidence_count": len(evidence_records),
        "mean_evidence_confidence": mean([item.get("confidence", 0.0) for item in evidence_records]),
        "prediction_accuracy": prediction_scores.get("accuracy_label", ""),
        "falsification_status": strongest_falsification_status(challenges),
        "replication_count": int(theory.get("promoted_count") or 0),
        "sample_size": int(autonomous_report.get("record_count") or 0),
    }


def strongest_falsification_status(challenges: list[dict[str, Any]]) -> str:
    """Return strongest overall falsification status."""
    if not challenges:
        return "needs_more_evidence"

    statuses = [item.get("status", "") for item in challenges]

    if "challenged_by_contradiction" in statuses:
        return "challenged_by_contradiction"

    if "weakened_by_counterexamples" in statuses:
        return "weakened_by_counterexamples"

    if "survived_initial_challenge" in statuses:
        return "survived_initial_challenge"

    return "needs_more_evidence"


def mean(values: list[Any]) -> float:
    """Mean numeric values."""
    nums = []
    for value in values:
        try:
            nums.append(float(value))
        except Exception:
            pass

    if not nums:
        return 0.0

    return round(sum(nums) / len(nums), 6)
