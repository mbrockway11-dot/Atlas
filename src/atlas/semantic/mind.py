"""Semantic cognition and communication domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_mind_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic mind summary."""
    classification = payload.get("classification", {})
    topology = payload.get("topology", {})
    resonance = payload.get("resonance", {})

    role = classification.get("structural_role", "Unresolved Structural Actor")
    cognitive_style = classification.get("cognitive_style", "")
    topology_class = topology.get("topology_class", "unresolved topology")
    resonance_class = resonance.get("resonance_class", "unresolved resonance")

    if role == "Temporal-Interpreter":
        core = (
            "This profile appears to organize cognition through timing, sequence, "
            "context, and transition. Rather than reading information as isolated "
            "facts, the mind tends to track how patterns unfold across time."
        )
    else:
        core = (
            "This profile's cognitive style should be interpreted through the "
            "available classification, topology, resonance, and temporal layers."
        )

    summary = sentence_join([
        core,
        cognitive_style,
        f"The topology layer currently resolves as {topology_class}, while resonance resolves as {resonance_class}.",
        "Together, these layers describe how information may be organized, activated, and expressed.",
    ])

    return {
        "domain": "mind",
        "title": "Mind Architecture",
        "summary": summary,
        "confidence": classification.get("confidence", confidence(0.55)),
        "evidence": [
            evidence_item("classification", "Structural role contributes to cognition summary.", classification),
            evidence_item("topology", "Topology contributes organizational pattern.", topology),
            evidence_item("resonance", "Resonance contributes activation pattern.", resonance),
        ],
    }
