
"""Cognitive Digital Twin transitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.cognitive_twin.states import CognitiveState


@dataclass(frozen=True)
class CognitiveTransition:
    """Transition between cognitive twin states."""

    source: str
    target: str
    trigger: str
    probability: float
    explanation: str


def build_cognitive_transitions(states: list[CognitiveState]) -> list[CognitiveTransition]:
    """Build default state transitions."""
    ids = {state.state_id for state in states}
    transitions: list[CognitiveTransition] = []

    def add(source: str, target: str, trigger: str, probability: float, explanation: str) -> None:
        if source in ids and target in ids:
            transitions.append(
                CognitiveTransition(
                    source=source,
                    target=target,
                    trigger=trigger,
                    probability=probability,
                    explanation=explanation,
                )
            )

    add(
        "stable_builder",
        "synthesis_mode",
        "complexity increases",
        0.78,
        "Stable construction tends to route into cross-domain synthesis when the system encounters complexity.",
    )
    add(
        "synthesis_mode",
        "symbolic_compression",
        "patterns become abstract",
        0.72,
        "Cross-domain material compresses into symbolic or reusable structures.",
    )
    add(
        "symbolic_compression",
        "visible_author",
        "structure becomes transmissible",
        0.70,
        "Compressed structures become public-facing when they are ready to be explained or taught.",
    )
    add(
        "visible_author",
        "stable_builder",
        "output reintegrates",
        0.74,
        "Public authorship returns to stable construction after the message becomes an artifact.",
    )
    add(
        "stable_builder",
        "innovation_pressure",
        "continuity no longer fits",
        0.58,
        "Innovation pressure emerges when persistence encounters a structure that needs redesign.",
    )
    add(
        "innovation_pressure",
        "stable_builder",
        "new pattern stabilizes",
        0.64,
        "Innovation resolves when a new structure becomes durable enough to preserve.",
    )

    return transitions


def transition_to_dict(transition: CognitiveTransition) -> dict[str, Any]:
    """Convert transition to dict."""
    return asdict(transition)
