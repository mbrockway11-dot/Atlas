
"""Structural Simulation Engine report."""

from __future__ import annotations

from typing import Any

from atlas.simulation.activation import activate_graph
from atlas.simulation.adaptation import build_adaptation_model
from atlas.simulation.decision import build_decision_candidates
from atlas.simulation.environment import SimulationEnvironment, environment_from_dict, environment_to_dict
from atlas.simulation.growth import build_growth_model
from atlas.simulation.propagation import propagate_activation
from atlas.simulation.recovery import build_recovery_path
from atlas.simulation.scenarios import get_scenario_environment
from atlas.simulation.stimuli import build_stimuli


SIMULATION_REPORT_VERSION = "1.0"


def build_simulation_report(
    systems_report: dict[str, Any],
    *,
    scenario: str = "",
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build structural simulation report."""
    if environment:
        env = environment_from_dict(environment)
    elif scenario:
        env = get_scenario_environment(scenario)
    else:
        env = SimulationEnvironment()

    stimuli_payload = build_stimuli(env)
    inference_graph = systems_report.get("diagrams", {}).get("inference_graph", {})

    activation = activate_graph(inference_graph, stimuli_payload["stimuli"])
    propagation = propagate_activation(
        inference_graph,
        activation["node_activations"],
    )

    decisions = build_decision_candidates(propagation["propagated_activations"])
    recovery = build_recovery_path(decisions)
    adaptation = build_adaptation_model(decisions, recovery)

    simulation = {
        "environment": environment_to_dict(env),
        "stimuli": stimuli_payload,
        "activation": activation,
        "propagation": propagation,
        "decisions": decisions,
        "recovery": recovery,
        "adaptation": adaptation,
    }

    return {
        "success": True,
        "version": SIMULATION_REPORT_VERSION,
        "profile_key": systems_report.get("profile_key"),
        "scenario": scenario,
        "simulation": simulation,
        "growth": build_growth_model(simulation),
    }
