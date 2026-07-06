
"""Evolution learning model."""

from __future__ import annotations

from typing import Any

from atlas.evolution.memory import EvolutionMemory


def build_learning_model(memory: EvolutionMemory) -> dict[str, Any]:
    """Build learning model from memory."""
    dominant_action = max(memory.action_counts, key=memory.action_counts.get) if memory.action_counts else "unresolved"
    dominant_recovery = max(memory.recovery_counts, key=memory.recovery_counts.get) if memory.recovery_counts else "unresolved"
    dominant_growth = max(memory.growth_counts, key=memory.growth_counts.get) if memory.growth_counts else "unresolved"

    experience_count = len(memory.experiences)

    return {
        "experience_count": experience_count,
        "dominant_action": dominant_action,
        "dominant_recovery": dominant_recovery,
        "dominant_growth_vector": dominant_growth,
        "learning_signal": learning_signal(dominant_action, dominant_recovery, experience_count),
        "confidence": min(1.0, 0.35 + experience_count * 0.08),
    }


def learning_signal(action: str, recovery: str, experience_count: int) -> str:
    """Describe learning signal."""
    if experience_count <= 1:
        return "early_signal"

    if action == "structure_plan" and "stable" in recovery:
        return "structure_reinforcement"

    if action in {"explain_publicly", "publish_artifact", "teach_framework"}:
        return "visibility_reinforcement"

    if action in {"map_relationships", "gather_information", "connect_domains"}:
        return "cognitive_mapping_reinforcement"

    return "mixed_adaptation"
