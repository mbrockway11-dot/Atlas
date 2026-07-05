"""Semantic career and public role domain."""

from __future__ import annotations

from typing import Any

from atlas.semantic.common import confidence, evidence_item, sentence_join


def build_career_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build semantic career summary."""
    classification = payload.get("classification", {})
    fingerprint = payload.get("fingerprint", {})
    role = classification.get("structural_role", "Unresolved Structural Actor")
    function = classification.get("civilization_function", "")

    summary = sentence_join([
        f"The public-role layer centers on the compiled role: {role}.",
        function,
        "Career or contribution is most coherent when the person is placed in environments that reward the profile's dominant structural function.",
        "The fingerprint layer should eventually allow comparison against population neighbors and role-specific contribution patterns.",
    ])

    return {
        "domain": "career",
        "title": "Career & Contribution Architecture",
        "summary": summary,
        "confidence": confidence(0.64 if role != "Unresolved Structural Actor" else 0.38),
        "evidence": [
            evidence_item("classification", "Civilization function informs contribution.", classification),
            evidence_item("fingerprint", "Fingerprint supports future population comparison.", fingerprint),
        ],
    }
