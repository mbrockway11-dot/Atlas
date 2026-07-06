
"""Executive systems summary."""

from __future__ import annotations

from typing import Any


def build_executive_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build executive systems summary."""
    identity = payload.get("identity", {})
    classification = payload.get("classification", {})
    synthesis = payload.get("synthesis", {})
    reasoning = synthesis.get("reasoning", {})
    inference_graph = synthesis.get("inference_graph", {})

    strongest = reasoning.get("strongest_inferences", [])
    top = strongest[0] if strongest else {}

    return {
        "title": "Systems Engineering Report",
        "profile_key": payload.get("profile_key"),
        "name": identity.get("display_name") or identity.get("full_name") or payload.get("profile_key"),
        "system_class": classification.get("structural_role", "Unclassified"),
        "system_subtype": classification.get("structural_subtype", "Unresolved"),
        "classification_confidence": classification.get("confidence", {}),
        "primary_architecture": top.get("inference", "unresolved"),
        "primary_architecture_confidence": top.get("confidence", 0),
        "strongest_themes": synthesis.get("strongest_theme_names", []),
        "structural_tensions": inference_graph.get("conflicts", []),
        "applied_rules": inference_graph.get("applied_rules", []),
        "summary": synthesis.get("summary", ""),
    }
