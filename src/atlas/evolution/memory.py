
"""Evolution memory model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.evolution.experience import ExperienceRecord, experience_to_dict


@dataclass(frozen=True)
class EvolutionMemory:
    """Persistent memory for a cognitive twin."""

    profile_key: str
    experiences: tuple[ExperienceRecord, ...]
    action_counts: dict[str, int]
    recovery_counts: dict[str, int]
    growth_counts: dict[str, int]


def build_memory(profile_key: str, experiences: list[ExperienceRecord]) -> EvolutionMemory:
    """Build memory from experience records."""
    return EvolutionMemory(
        profile_key=profile_key,
        experiences=tuple(experiences),
        action_counts=count_values([item.likely_action for item in experiences]),
        recovery_counts=count_values([item.recovery_mode for item in experiences]),
        growth_counts=count_values([item.growth_vector for item in experiences]),
    )


def memory_to_dict(memory: EvolutionMemory) -> dict[str, Any]:
    """Convert memory to dict."""
    data = asdict(memory)
    data["experiences"] = [experience_to_dict(item) for item in memory.experiences]
    return data


def count_values(values: list[str]) -> dict[str, int]:
    """Count string values."""
    counts: dict[str, int] = {}

    for value in values:
        counts[value] = counts.get(value, 0) + 1

    return counts
