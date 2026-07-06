
"""Autonomous Director state machine."""

from __future__ import annotations

from typing import Any


DIRECTOR_STATES = [
    "initialized",
    "observing",
    "planning",
    "executing",
    "evaluating",
    "learning",
    "persisting",
    "completed",
    "failed",
]


def create_director_state() -> dict[str, Any]:
    """Create initial Director state."""
    return {
        "success": True,
        "state": "initialized",
        "history": [],
    }


def transition_state(state: dict[str, Any], next_state: str, *, note: str = "") -> dict[str, Any]:
    """Transition Director state."""
    if next_state not in DIRECTOR_STATES:
        next_state = "failed"
        note = note or "Invalid state transition."

    state.setdefault("history", []).append(
        {
            "from": state.get("state"),
            "to": next_state,
            "note": note,
        }
    )

    state["state"] = next_state
    return state
