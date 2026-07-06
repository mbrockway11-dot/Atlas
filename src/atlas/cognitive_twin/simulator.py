
"""Cognitive Digital Twin scenario simulator."""

from __future__ import annotations

from typing import Any

from atlas.cognitive_twin.states import CognitiveState, state_to_dict
from atlas.cognitive_twin.transitions import CognitiveTransition, transition_to_dict


def simulate_scenario(
    states: list[CognitiveState],
    transitions: list[CognitiveTransition],
    scenario: str,
) -> dict[str, Any]:
    """Simulate likely state activation for a scenario."""
    scenario_text = scenario.lower()

    scored = []
    for state in states:
        score = float(state.confidence)
        matched_triggers = []

        for trigger in state.triggers:
            if any(word in scenario_text for word in trigger.lower().split()):
                score += 0.08
                matched_triggers.append(trigger)

        if state.category in scenario_text:
            score += 0.05

        scored.append(
            {
                "state": state,
                "score": min(1.0, score),
                "matched_triggers": matched_triggers,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)

    active = scored[0]["state"] if scored else states[0]
    likely_transitions = [
        transition
        for transition in transitions
        if transition.source == active.state_id
    ]

    likely_transitions = sorted(
        likely_transitions,
        key=lambda item: item.probability,
        reverse=True,
    )

    return {
        "scenario": scenario,
        "active_state": state_to_dict(active),
        "activation_score": scored[0]["score"] if scored else 0,
        "matched_triggers": scored[0]["matched_triggers"] if scored else [],
        "likely_transitions": [
            transition_to_dict(item)
            for item in likely_transitions
        ],
        "state_scores": [
            {
                "state_id": item["state"].state_id,
                "label": item["state"].label,
                "score": item["score"],
                "matched_triggers": item["matched_triggers"],
            }
            for item in scored
        ],
    }
