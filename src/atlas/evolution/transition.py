
"""Evolution transition modeling."""

from __future__ import annotations

from typing import Any

from atlas.evolution.memory import EvolutionMemory


def build_transition_report(memory: EvolutionMemory) -> dict[str, Any]:
    """Build transition report from experience sequence."""
    experiences = list(memory.experiences)
    transitions = []

    for index in range(1, len(experiences)):
        previous = experiences[index - 1]
        current = experiences[index]
        transitions.append(
            {
                "from_action": previous.likely_action,
                "to_action": current.likely_action,
                "from_recovery": previous.recovery_mode,
                "to_recovery": current.recovery_mode,
                "scenario": current.scenario,
            }
        )

    return {
        "transition_count": len(transitions),
        "transitions": transitions,
    }
