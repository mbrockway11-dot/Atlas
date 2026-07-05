"""Semantic emotional domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_emotion_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic emotional summary."""
    classification = payload.get("classification", {})
    resonance = payload.get("resonance", {})

    role = classification.get("structural_role", "Unresolved Structural Actor")
    resonance_class = resonance.get("resonance_class", "unresolved resonance")
    dominant_axis = resonance.get("dominant_resonance_axis", "unresolved axis")

    summary = sentence_join([
        f"The emotional layer is interpreted through the profile's {resonance_class} resonance pattern.",
        f"The dominant resonance axis is {dominant_axis}.",
        "This describes how activation may move through the profile under emotional or environmental pressure.",
        "For Temporal-Interpreter profiles, emotional regulation often improves when timing sensitivity is grounded into practical action rather than left in open analysis.",
    ])

    return {
        "domain": "emotion",
        "title": "Emotional Regulation",
        "summary": summary,
        "confidence": confidence(0.62 if resonance else 0.35),
        "evidence": [
            evidence_item("resonance", "Resonance informs emotional activation.", resonance),
            evidence_item("classification", "Role modifies emotional interpretation.", classification),
        ],
    }
