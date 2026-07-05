"""Semantic relationship domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_relationship_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic relationship summary."""
    classification = payload.get("classification", {})
    topology = payload.get("topology", {})

    role = classification.get("structural_role", "Unresolved Structural Actor")
    topology_class = topology.get("topology_class", "unresolved topology")

    summary = sentence_join([
        f"Relationship style is interpreted through the compiled {role} role and {topology_class} topology.",
        "A distributed topology may indicate that the person relates through multiple conceptual or emotional centers rather than one fixed relational script.",
        "For timing-oriented profiles, relationships may be strongly affected by readiness, sequence, pacing, and the felt timing of disclosure or commitment.",
    ])

    return {
        "domain": "relationships",
        "title": "Relationship Architecture",
        "summary": summary,
        "confidence": confidence(0.58 if classification else 0.35),
        "evidence": [
            evidence_item("classification", "Role contributes relationship style.", classification),
            evidence_item("topology", "Topology contributes relational organization.", topology),
        ],
    }
