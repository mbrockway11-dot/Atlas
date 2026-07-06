
"""Causal confidence scoring."""

from __future__ import annotations

from typing import Any


def score_causal_confidence(
    scan_results: list[dict[str, Any]],
    interventions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score causal candidates."""
    intervention_map = {
        item.get("candidate_id"): item
        for item in interventions
    }

    rows = []

    for result in scan_results:
        intervention = intervention_map.get(result.get("candidate_id"), {})
        confidence = causal_confidence(result, intervention)

        rows.append(
            {
                **result,
                "intervention": intervention,
                "causal_confidence": confidence,
                "causal_label": causal_label(confidence),
                "caution": (
                    "Observational correlation only. This is a candidate causal hypothesis, not proof."
                ),
            }
        )

    return sorted(rows, key=lambda item: item.get("causal_confidence", 0.0), reverse=True)


def causal_confidence(result: dict[str, Any], intervention: dict[str, Any]) -> float:
    """Compute candidate causal confidence."""
    sample_size = int(result.get("sample_size") or 0)
    correlation = abs(float(result.get("correlation") or 0.0))
    expected_shift = abs(float(intervention.get("expected_effect_shift") or 0.0))

    sample_score = min(0.25, sample_size / 1000)
    correlation_score = correlation * 0.55
    intervention_score = min(0.20, expected_shift * 2)

    if result.get("direction") == "neutral":
        penalty = 0.15
    else:
        penalty = 0.0

    return round(max(0.0, min(0.95, sample_score + correlation_score + intervention_score - penalty)), 6)


def causal_label(confidence: float) -> str:
    """Label causal confidence."""
    if confidence >= 0.78:
        return "strong_causal_candidate"
    if confidence >= 0.58:
        return "moderate_causal_candidate"
    if confidence >= 0.35:
        return "weak_causal_candidate"
    return "unsupported_causal_candidate"
