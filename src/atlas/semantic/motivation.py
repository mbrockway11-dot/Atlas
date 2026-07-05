"""Semantic motivation domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_motivation_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic motivation summary."""
    classification = payload.get("classification", {})
    temporal = payload.get("temporal", {})
    role = classification.get("structural_role", "Unresolved Structural Actor")

    if role == "Temporal-Interpreter":
        body = (
            "Motivation is likely strongest when action is connected to timing, "
            "emergence, discovery, or the recognition of a meaningful transition. "
            "This profile may become most energized when it senses that a system is "
            "ready to shift and that intervention can alter the trajectory."
        )
    else:
        body = (
            "Motivation remains provisional and should be interpreted through the "
            "complete compiled payload."
        )

    summary = sentence_join([
        body,
        "Temporal data supplies activation context, while classification supplies the primary motivational frame.",
    ])

    return {
        "domain": "motivation",
        "title": "Motivation Architecture",
        "summary": summary,
        "confidence": confidence(0.68 if role != "Unresolved Structural Actor" else 0.4),
        "evidence": [
            evidence_item("classification", "Structural role informs motivation.", classification),
            evidence_item("temporal", "Temporal layer informs activation context.", temporal.get("summary", {})),
        ],
    }
