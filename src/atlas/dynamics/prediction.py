
"""Dynamic prediction layer."""

from __future__ import annotations

from typing import Any


def build_dynamic_prediction(dynamic_profile: dict[str, Any]) -> dict[str, Any]:
    """Build simple prediction from dynamic profile."""
    recurrence = float(dynamic_profile.get("recurrence") or 0.0)
    energy = float(dynamic_profile.get("mean_energy") or 0.0)
    attractor_density = float(dynamic_profile.get("attractor_density") or 0.0)

    recovery_probability = min(0.95, 0.35 + recurrence * 0.6 + min(0.25, attractor_density / 20))
    perturbation_sensitivity = min(0.95, 0.25 + energy / 10)

    return {
        "profile_key": dynamic_profile.get("profile_key"),
        "recovery_probability": round(recovery_probability, 6),
        "perturbation_sensitivity": round(perturbation_sensitivity, 6),
        "likely_dynamic_response": classify_response(recovery_probability, perturbation_sensitivity),
    }


def classify_response(recovery: float, sensitivity: float) -> str:
    """Classify dynamic response."""
    if recovery >= 0.70 and sensitivity < 0.55:
        return "stable_basin_recovery"

    if recovery >= 0.70 and sensitivity >= 0.55:
        return "activated_recovery_loop"

    if recovery < 0.55 and sensitivity >= 0.55:
        return "flow_disruption_risk"

    return "mixed_dynamic_response"
