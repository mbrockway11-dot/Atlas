"""Semantic stress domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_stress_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic stress summary."""
    classification = payload.get("classification", {})
    resonance = payload.get("resonance", {})

    role = classification.get("structural_role", "Unresolved Structural Actor")

    if role == "Temporal-Interpreter":
        stress = (
            "Under pressure, this profile may over-monitor signals, timing, "
            "future possibilities, or unresolved patterns. Stress can increase "
            "the desire to wait for the perfect window rather than act with the "
            "available window."
        )
    else:
        stress = (
            "Stress response should be interpreted through available resonance, "
            "classification, and temporal evidence."
        )

    summary = sentence_join([
        stress,
        "Resonance describes how activation propagates or dampens under pressure.",
    ])

    return {
        "domain": "stress",
        "title": "Stress Pattern",
        "summary": summary,
        "confidence": confidence(0.66 if classification else 0.35),
        "evidence": [
            evidence_item("classification", "Role informs stress pattern.", classification),
            evidence_item("resonance", "Resonance informs activation under pressure.", resonance),
        ],
    }
