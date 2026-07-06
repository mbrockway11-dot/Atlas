
"""Decision choice model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionChoice:
    """One possible decision path."""

    choice_id: str
    label: str
    scenario: str
    environment: dict[str, float]
    notes: str = ""


def choice_to_dict(choice: DecisionChoice) -> dict[str, Any]:
    """Convert choice to dict."""
    return asdict(choice)


def make_choice(
    *,
    choice_id: str,
    label: str,
    scenario: str = "",
    environment: dict[str, float] | None = None,
    notes: str = "",
) -> DecisionChoice:
    """Build a decision choice."""
    return DecisionChoice(
        choice_id=choice_id,
        label=label,
        scenario=scenario,
        environment=environment or {},
        notes=notes,
    )
