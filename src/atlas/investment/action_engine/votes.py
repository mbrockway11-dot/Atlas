
"""Action Engine vote models."""

from __future__ import annotations


ACTIONS = {
    "HOLD",
    "SCALE_IN",
    "REDUCE",
    "EXIT_REVIEW",
    "TRAILING_STOP_PENDING",
}


VOTE_WEIGHTS = {
    "decision_alignment": 0.30,
    "position_manager": 0.25,
    "learning": 0.15,
    "performance": 0.15,
    "trailing_stop": 0.10,
    "exposure": 0.05,
}


def empty_score() -> dict[str, float]:
    return {action: 0.0 for action in ACTIONS}
