
"""Cognitive Digital Twin report builder."""

from __future__ import annotations

from typing import Any

from atlas.cognitive_twin.simulator import simulate_scenario
from atlas.cognitive_twin.state_builder import build_cognitive_states
from atlas.cognitive_twin.states import state_to_dict
from atlas.cognitive_twin.transitions import build_cognitive_transitions, transition_to_dict


COGNITIVE_TWIN_VERSION = "1.0"


def build_cognitive_twin_report(
    systems_report: dict[str, Any],
    *,
    scenario: str = "",
) -> dict[str, Any]:
    """Build Cognitive Digital Twin report."""
    states = build_cognitive_states(systems_report)
    transitions = build_cognitive_transitions(states)

    report = {
        "success": True,
        "version": COGNITIVE_TWIN_VERSION,
        "profile_key": systems_report.get("profile_key"),
        "state_count": len(states),
        "transition_count": len(transitions),
        "states": [state_to_dict(item) for item in states],
        "transitions": [transition_to_dict(item) for item in transitions],
    }

    if scenario:
        report["simulation"] = simulate_scenario(states, transitions, scenario)

    return report
