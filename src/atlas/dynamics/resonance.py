
"""Dynamic resonance between profiles."""

from __future__ import annotations

from typing import Any


def compare_dynamic_resonance(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Compare two dynamic profile signatures."""
    left_profile = left.get("dynamic_profile", {}) or {}
    right_profile = right.get("dynamic_profile", {}) or {}

    recurrence_similarity = 1.0 - abs(
        float(left_profile.get("recurrence") or 0.0)
        - float(right_profile.get("recurrence") or 0.0)
    )

    energy_similarity = 1.0 / (
        1.0 + abs(
            float(left_profile.get("mean_energy") or 0.0)
            - float(right_profile.get("mean_energy") or 0.0)
        )
    )

    attractor_similarity = 1.0 / (
        1.0 + abs(
            float(left_profile.get("attractor_density") or 0.0)
            - float(right_profile.get("attractor_density") or 0.0)
        )
    )

    score = (
        recurrence_similarity * 0.40
        + energy_similarity * 0.25
        + attractor_similarity * 0.35
    )

    return {
        "success": True,
        "left_profile_key": left.get("profile_key"),
        "right_profile_key": right.get("profile_key"),
        "dynamic_resonance": round(score, 6),
        "recurrence_similarity": round(recurrence_similarity, 6),
        "energy_similarity": round(energy_similarity, 6),
        "attractor_similarity": round(attractor_similarity, 6),
        "label": resonance_label(score),
    }


def resonance_label(score: float) -> str:
    """Label resonance."""
    if score >= 0.82:
        return "high_dynamic_resonance"
    if score >= 0.62:
        return "moderate_dynamic_resonance"
    if score >= 0.42:
        return "low_dynamic_resonance"
    return "dynamic_dissonance"
