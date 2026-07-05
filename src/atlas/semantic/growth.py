"""Semantic growth domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_growth_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic growth summary."""
    classification = payload.get("classification", {})
    role = classification.get("structural_role", "Unresolved Structural Actor")

    if role == "Temporal-Interpreter":
        growth = (
            "Growth comes from allowing timing to guide action without allowing "
            "timing to become a reason for delay. The developmental task is to "
            "convert perception into execution."
        )
    else:
        growth = (
            "Growth remains provisional until the classification and supporting "
            "layers are more fully resolved."
        )

    summary = sentence_join([
        growth,
        "The strongest developmental path is the one that integrates structural awareness with embodied practice.",
    ])

    return {
        "domain": "growth",
        "title": "Growth Trajectory",
        "summary": summary,
        "confidence": confidence(0.7 if role != "Unresolved Structural Actor" else 0.4),
        "evidence": [
            evidence_item("classification", "Role informs growth path.", classification),
        ],
    }
