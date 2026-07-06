
"""Service layer for Unified Dynamics."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.dynamics import build_unified_dynamics_report
from atlas.library.profile_library import list_saved_profiles


def list_dynamics_profiles() -> list[str]:
    """List saved profiles available for dynamics analysis."""
    return list_saved_profiles()


def build_dynamics_payload(
    profile_key: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Build service-backed Unified Dynamics payload."""
    payload = compile_canonical_profile(profile_key, force=force)

    if not payload.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": payload.get("errors", []),
            "payload": payload,
            "dynamics": {},
        }

    dynamics = payload.get("dynamics")

    if not dynamics or not dynamics.get("success"):
        dynamics = build_unified_dynamics_report(payload)

    return {
        "success": True,
        "profile_key": profile_key,
        "errors": [],
        "payload": payload,
        "dynamics": dynamics,
        "dynamic_profile": dynamics.get("dynamic_profile", {}),
        "identity_field": dynamics.get("identity_field", {}),
        "prediction": dynamics.get("prediction", {}),
        "reasoning": dynamics.get("reasoning", {}),
        "evidence": dynamics.get("evidence", []),
    }


def build_dynamics_summary(
    profile_key: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Build compact Unified Dynamics summary."""
    result = build_dynamics_payload(profile_key, force=force)

    if not result.get("success"):
        return result

    dynamics = result.get("dynamics", {})
    dynamic_profile = result.get("dynamic_profile", {})
    prediction = result.get("prediction", {})
    identity_field = result.get("identity_field", {})

    return {
        "success": True,
        "profile_key": profile_key,
        "summary": dynamics.get("summary", ""),
        "flow_stability": dynamic_profile.get("flow_stability"),
        "phase_complexity": dynamic_profile.get("phase_complexity"),
        "recurrence": dynamic_profile.get("recurrence"),
        "mean_energy": dynamic_profile.get("mean_energy"),
        "attractor_density": dynamic_profile.get("attractor_density"),
        "field_node_count": dynamic_profile.get("field_node_count"),
        "field_edge_count": dynamic_profile.get("field_edge_count"),
        "recovery_probability": prediction.get("recovery_probability"),
        "perturbation_sensitivity": prediction.get("perturbation_sensitivity"),
        "likely_dynamic_response": prediction.get("likely_dynamic_response"),
        "dominant_attractors": identity_field.get("dominant_attractors", []),
        "dominant_currents": identity_field.get("dominant_currents", []),
    }
