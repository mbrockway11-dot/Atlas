
"""Stress architecture interpretation."""

from __future__ import annotations

from typing import Any


def build_stress_architecture(payload: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic stress architecture interpretation."""
    dynamics = payload.get("dynamics", {}) or {}
    prediction = dynamics.get("prediction", {}) or {}
    profile = dynamics.get("dynamic_profile", {}) or {}

    response = prediction.get("likely_dynamic_response", "unresolved")
    recovery = prediction.get("recovery_probability", 0.0)
    sensitivity = prediction.get("perturbation_sensitivity", 0.0)

    risks = []
    supports = []

    if response == "activated_recovery_loop":
        supports.append("pressure can activate recovery rather than collapse the system")
        risks.append("activation may feel intense before stability returns")

    if float(sensitivity or 0.0) >= 0.6:
        risks.append("high perturbation sensitivity under changing conditions")

    if float(recovery or 0.0) >= 0.65:
        supports.append("recovery probability is structurally supported")

    return {
        "success": True,
        "domain": "stress_architecture",
        "response_mode": response,
        "recovery_probability": recovery,
        "perturbation_sensitivity": sensitivity,
        "supports": supports,
        "risks": risks,
        "summary": "Stress architecture describes how the profile responds when pressure perturbs the dynamic field.",
    }
