
"""Theory scoring."""

from __future__ import annotations

from typing import Any


def score_theory_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score theory candidates."""
    rows = []

    for candidate in candidates:
        score = theory_score(candidate)

        rows.append(
            {
                **candidate,
                "theory_score": score,
                "theory_strength": theory_strength(score),
            }
        )

    return sorted(rows, key=lambda item: item.get("theory_score", 0.0), reverse=True)


def theory_score(candidate: dict[str, Any]) -> float:
    """Compute theory score."""
    evidence_count = int(candidate.get("evidence_count") or 0)
    confidence = float(candidate.get("mean_confidence") or 0.0)
    effect = float(candidate.get("mean_effect_size") or 0.0)
    hypothesis_count = len(candidate.get("hypothesis_links", []) or [])

    evidence_score = min(0.25, evidence_count / 20)
    confidence_score = confidence * 0.40
    effect_score = effect * 0.25
    hypothesis_score = min(0.10, hypothesis_count / 50)

    return round(min(0.99, evidence_score + confidence_score + effect_score + hypothesis_score), 6)


def theory_strength(score: float) -> str:
    """Label theory strength."""
    if score >= 0.78:
        return "strong_theory_candidate"
    if score >= 0.58:
        return "moderate_theory_candidate"
    if score >= 0.35:
        return "weak_theory_candidate"
    return "insufficient_theory_candidate"
