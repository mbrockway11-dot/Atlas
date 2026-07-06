
"""Evolution experience model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExperienceRecord:
    """One simulation experience."""

    experience_id: str
    scenario: str
    likely_action: str
    recovery_mode: str
    growth_vector: str
    activation_score: float
    notes: str = ""


def experience_to_dict(record: ExperienceRecord) -> dict[str, Any]:
    """Convert experience to dict."""
    return asdict(record)


def experience_from_simulation(
    simulation: dict[str, Any],
    *,
    experience_id: str = "experience_001",
    notes: str = "",
) -> ExperienceRecord:
    """Create experience record from simulation report."""
    sim = simulation.get("simulation", {})
    decisions = sim.get("decisions", {})
    likely = decisions.get("likely_action") or {}
    recovery = sim.get("recovery", {})
    growth = simulation.get("growth", {})

    return ExperienceRecord(
        experience_id=experience_id,
        scenario=simulation.get("scenario", ""),
        likely_action=likely.get("action", "unresolved"),
        recovery_mode=recovery.get("recovery_mode", "unresolved"),
        growth_vector=growth.get("current_growth_vector", "unresolved"),
        activation_score=float(likely.get("score") or 0.0),
        notes=notes,
    )
