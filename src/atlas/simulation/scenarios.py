
"""Scenario presets for Atlas simulation."""

from __future__ import annotations

from atlas.simulation.environment import SimulationEnvironment


SCENARIO_PRESETS = {
    "public_launch": SimulationEnvironment(
        time_pressure=0.65,
        ambiguity=0.45,
        complexity=0.75,
        social_visibility=0.95,
        resource_constraints=0.45,
        conflict=0.25,
        novelty=0.70,
        collaboration=0.65,
        competition=0.35,
        uncertainty=0.50,
        fatigue=0.30,
    ),
    "creative_pressure": SimulationEnvironment(
        time_pressure=0.70,
        ambiguity=0.75,
        complexity=0.60,
        social_visibility=0.75,
        resource_constraints=0.30,
        conflict=0.20,
        novelty=0.85,
        collaboration=0.40,
        competition=0.25,
        uncertainty=0.70,
        fatigue=0.45,
    ),
    "team_conflict": SimulationEnvironment(
        time_pressure=0.55,
        ambiguity=0.50,
        complexity=0.65,
        social_visibility=0.65,
        resource_constraints=0.45,
        conflict=0.90,
        novelty=0.35,
        collaboration=0.75,
        competition=0.40,
        uncertainty=0.60,
        fatigue=0.55,
    ),
    "deep_build": SimulationEnvironment(
        time_pressure=0.20,
        ambiguity=0.35,
        complexity=0.85,
        social_visibility=0.20,
        resource_constraints=0.35,
        conflict=0.10,
        novelty=0.55,
        collaboration=0.35,
        competition=0.15,
        uncertainty=0.35,
        fatigue=0.25,
    ),
}


def get_scenario_environment(name: str) -> SimulationEnvironment:
    """Return scenario preset or a neutral environment."""
    return SCENARIO_PRESETS.get(name, SimulationEnvironment())
