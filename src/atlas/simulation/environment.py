
"""Simulation environment model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SimulationEnvironment:
    """Continuous environment variables for structural simulation."""

    time_pressure: float = 0.0
    ambiguity: float = 0.0
    complexity: float = 0.0
    social_visibility: float = 0.0
    resource_constraints: float = 0.0
    conflict: float = 0.0
    novelty: float = 0.0
    collaboration: float = 0.0
    competition: float = 0.0
    uncertainty: float = 0.0
    fatigue: float = 0.0


def environment_to_dict(environment: SimulationEnvironment) -> dict[str, Any]:
    """Convert environment to dict."""
    return asdict(environment)


def environment_from_dict(data: dict[str, Any]) -> SimulationEnvironment:
    """Build environment from dict."""
    return SimulationEnvironment(
        time_pressure=clamp(data.get("time_pressure", 0.0)),
        ambiguity=clamp(data.get("ambiguity", 0.0)),
        complexity=clamp(data.get("complexity", 0.0)),
        social_visibility=clamp(data.get("social_visibility", 0.0)),
        resource_constraints=clamp(data.get("resource_constraints", 0.0)),
        conflict=clamp(data.get("conflict", 0.0)),
        novelty=clamp(data.get("novelty", 0.0)),
        collaboration=clamp(data.get("collaboration", 0.0)),
        competition=clamp(data.get("competition", 0.0)),
        uncertainty=clamp(data.get("uncertainty", 0.0)),
        fatigue=clamp(data.get("fatigue", 0.0)),
    )


def clamp(value: Any) -> float:
    """Clamp value between 0 and 1."""
    try:
        numeric = float(value)
    except Exception:
        numeric = 0.0

    return max(0.0, min(1.0, numeric))
