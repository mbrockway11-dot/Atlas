
"""Evolution history utilities."""

from __future__ import annotations

from typing import Any

from atlas.evolution.experience import ExperienceRecord, experience_to_dict


def build_history(experiences: list[ExperienceRecord]) -> dict[str, Any]:
    """Build experience history section."""
    return {
        "experience_count": len(experiences),
        "experiences": [
            experience_to_dict(item)
            for item in experiences
        ],
    }
