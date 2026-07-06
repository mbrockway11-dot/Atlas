
"""Cognitive Digital Twin states."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CognitiveState:
    """One cognitive twin state."""

    state_id: str
    label: str
    category: str
    confidence: float
    triggers: tuple[str, ...]
    behaviors: tuple[str, ...]
    risks: tuple[str, ...]
    stabilizers: tuple[str, ...]


def state_to_dict(state: CognitiveState) -> dict[str, Any]:
    """Convert state to dict."""
    data = asdict(state)
    data["triggers"] = list(state.triggers)
    data["behaviors"] = list(state.behaviors)
    data["risks"] = list(state.risks)
    data["stabilizers"] = list(state.stabilizers)
    return data
