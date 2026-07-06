
"""Unified dynamic field model."""

from __future__ import annotations

from typing import Any


def build_identity_field(signature: dict[str, Any]) -> dict[str, Any]:
    """Build compact identity field from dynamic signature."""
    field = signature.get("dynamic_field", {}) or {}
    attractors = field.get("field_attractors", []) or []
    currents = field.get("edge_currents", []) or []

    return {
        "profile_key": signature.get("profile_key"),
        "node_count": field.get("node_count", 0),
        "current_count": field.get("edge_count", 0),
        "dominant_attractors": attractors[:10],
        "dominant_currents": currents[:10],
        "field_density": round(
            float(field.get("edge_count") or 0) / max(1, float(field.get("node_count") or 1)),
            6,
        ),
    }
