
"""Dynamics evidence adapter."""

from __future__ import annotations

from typing import Any


def build_dynamics_evidence(dynamic_signature: dict[str, Any]) -> list[dict[str, Any]]:
    """Build evidence rows from dynamic signature."""
    metrics = dynamic_signature.get("dynamic_metrics", {}) or {}

    evidence = []

    evidence.append(make_evidence(
        "dynamics.recurrence",
        "recursive_patterning",
        "symbolic_architecture",
        metrics.get("mean_recurrence", 0.0),
        0.78,
    ))

    evidence.append(make_evidence(
        "dynamics.attractors",
        "stability_basin",
        "dynamic_architecture",
        metrics.get("attractor_count", 0),
        0.80,
    ))

    evidence.append(make_evidence(
        "dynamics.flow_field",
        "field_complexity",
        "dynamic_architecture",
        metrics.get("field_edge_count", 0),
        0.76,
    ))

    evidence.append(make_evidence(
        "dynamics.transition_energy",
        "activation_cost",
        "motivational_architecture",
        metrics.get("mean_energy", 0.0),
        0.70,
    ))

    return evidence


def make_evidence(
    engine: str,
    feature: str,
    category: str,
    value,
    confidence: float,
) -> dict[str, Any]:
    """Build dynamics evidence row."""
    return {
        "engine": engine,
        "feature": feature,
        "category": category,
        "value": value,
        "confidence": confidence,
        "weight": 1.0,
        "explanation": f"{engine} supports {feature}.",
        "source": engine,
        "tags": ["dynamics", feature],
    }
