
"""Unified legacy knowledge interpreter."""

from __future__ import annotations

from typing import Any

from atlas.knowledge.career_architecture import build_career_architecture
from atlas.knowledge.growth_architecture import build_growth_architecture
from atlas.knowledge.learning_architecture import build_learning_architecture
from atlas.knowledge.mind_architecture import build_mind_architecture
from atlas.knowledge.relationship_architecture import build_relationship_architecture
from atlas.knowledge.stress_architecture import build_stress_architecture


def build_knowledge_interpretation(payload: dict[str, Any]) -> dict[str, Any]:
    """Build unified knowledge interpretation."""
    sections = {
        "mind": build_mind_architecture(payload),
        "stress": build_stress_architecture(payload),
        "learning": build_learning_architecture(payload),
        "growth": build_growth_architecture(payload),
        "relationship": build_relationship_architecture(payload),
        "career": build_career_architecture(payload),
    }

    return {
        "success": True,
        "profile_key": payload.get("profile_key"),
        "sections": sections,
        "summary": build_summary(sections),
    }


def build_summary(sections: dict[str, Any]) -> str:
    """Build compact interpretation summary."""
    successful = [
        name for name, section in sections.items()
        if section.get("success")
    ]

    return (
        "Knowledge interpretation completed for "
        + ", ".join(successful)
        + "."
    )
