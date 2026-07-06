
"""Theory challenger."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.falsification.contradictions import find_contradictions
from atlas.autonomous.falsification.counterexamples import find_counterexamples
from atlas.autonomous.falsification.rival_models import build_rival_models


def challenge_theory(
    theory: dict[str, Any],
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Challenge one theory with counterexamples, contradictions, and rivals."""
    counterexamples = find_counterexamples(theory, evidence_records)
    contradictions = find_contradictions(theory, evidence_records)
    rivals = build_rival_models(theory)

    penalty = falsification_penalty(counterexamples, contradictions, rivals)
    adjusted_score = max(0.0, float(theory.get("theory_score") or 0.0) - penalty)

    return {
        "success": True,
        "theory_id": theory.get("theory_id"),
        "label": theory.get("label"),
        "original_score": theory.get("theory_score"),
        "falsification_penalty": round(penalty, 6),
        "adjusted_score": round(adjusted_score, 6),
        "counterexample_count": len(counterexamples),
        "contradiction_count": len(contradictions),
        "rival_model_count": len(rivals),
        "counterexamples": counterexamples,
        "contradictions": contradictions,
        "rival_models": rivals,
        "status": falsification_status(adjusted_score, counterexamples, contradictions),
        "summary": build_challenge_summary(theory, adjusted_score, counterexamples, contradictions, rivals),
    }


def falsification_penalty(
    counterexamples: list[dict[str, Any]],
    contradictions: list[dict[str, Any]],
    rivals: list[dict[str, Any]],
) -> float:
    """Compute falsification penalty."""
    return min(
        0.60,
        len(counterexamples) * 0.04
        + len(contradictions) * 0.08
        + len(rivals) * 0.015,
    )


def falsification_status(
    adjusted_score: float,
    counterexamples: list[dict[str, Any]],
    contradictions: list[dict[str, Any]],
) -> str:
    """Classify falsification status."""
    if contradictions:
        return "challenged_by_contradiction"

    if len(counterexamples) >= 3:
        return "weakened_by_counterexamples"

    if adjusted_score >= 0.58:
        return "survived_initial_challenge"

    return "needs_more_evidence"


def build_challenge_summary(
    theory: dict[str, Any],
    adjusted_score: float,
    counterexamples: list[dict[str, Any]],
    contradictions: list[dict[str, Any]],
    rivals: list[dict[str, Any]],
) -> str:
    """Build challenge summary."""
    return (
        f"{theory.get('label')} challenged with {len(counterexamples)} counterexample(s), "
        f"{len(contradictions)} contradiction(s), and {len(rivals)} rival model(s). "
        f"Adjusted score: {adjusted_score:.3f}."
    )
