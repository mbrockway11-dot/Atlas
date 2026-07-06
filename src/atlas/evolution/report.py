
"""Evolution report builder."""

from __future__ import annotations

from typing import Any

from atlas.evolution.adaptation import build_adaptation_report
from atlas.evolution.experience import ExperienceRecord, experience_from_simulation
from atlas.evolution.history import build_history
from atlas.evolution.learning import build_learning_model
from atlas.evolution.memory import build_memory, memory_to_dict
from atlas.evolution.transition import build_transition_report


EVOLUTION_REPORT_VERSION = "1.0"


def build_evolution_report(
    profile_key: str,
    simulations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build evolution report from simulation outputs."""
    experiences = [
        experience_from_simulation(
            simulation,
            experience_id=f"experience_{index + 1:03d}",
        )
        for index, simulation in enumerate(simulations)
    ]

    memory = build_memory(profile_key, experiences)
    learning = build_learning_model(memory)
    adaptation = build_adaptation_report(learning)
    transitions = build_transition_report(memory)

    return {
        "success": True,
        "version": EVOLUTION_REPORT_VERSION,
        "profile_key": profile_key,
        "history": build_history(experiences),
        "memory": memory_to_dict(memory),
        "learning": learning,
        "adaptation": adaptation,
        "transitions": transitions,
        "summary": build_summary(learning, adaptation),
    }


def build_summary(learning: dict[str, Any], adaptation: dict[str, Any]) -> str:
    """Build compact evolution summary."""
    return (
        f"Evolution model detected {learning.get('learning_signal')} after "
        f"{learning.get('experience_count')} experience(s). "
        f"Current adaptation: {adaptation.get('adaptation_label')}."
    )
