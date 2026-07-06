
"""Unified dynamics reasoning."""

from __future__ import annotations

from typing import Any


def build_dynamics_reasoning(dynamic_profile: dict[str, Any]) -> dict[str, Any]:
    """Build higher-order reasoning from dynamic profile."""
    recurrence = float(dynamic_profile.get("recurrence") or 0.0)
    attractor_density = float(dynamic_profile.get("attractor_density") or 0.0)
    stability = dynamic_profile.get("flow_stability")

    inferences = []

    if recurrence >= 0.25:
        inferences.append({
            "inference": "recursive_stabilization",
            "confidence": min(0.95, 0.60 + recurrence),
            "explanation": "The profile repeatedly returns to symbolic nodes, suggesting stabilization through recurrence.",
        })

    if attractor_density >= 2.0:
        inferences.append({
            "inference": "attractor_basin_identity",
            "confidence": min(0.95, 0.55 + attractor_density / 10),
            "explanation": "Multiple attractor nodes suggest the identity field has stable basins.",
        })

    if stability == "low_recurrence_diffuse_flow":
        inferences.append({
            "inference": "diffuse_exploratory_flow",
            "confidence": 0.68,
            "explanation": "Low recurrence suggests broad movement through the field rather than basin return.",
        })

    return {
        "profile_key": dynamic_profile.get("profile_key"),
        "inference_count": len(inferences),
        "inferences": inferences,
    }
