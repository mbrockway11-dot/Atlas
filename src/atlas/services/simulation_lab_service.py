
"""Service layer for Simulation Lab dashboard."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles
from atlas.simulation import build_simulation_report
from atlas.simulation.scenarios import SCENARIO_PRESETS


def list_simulation_profiles() -> list[str]:
    """List profiles available for simulation."""
    return list_saved_profiles()


def list_simulation_scenarios() -> list[str]:
    """List scenario presets."""
    return sorted(SCENARIO_PRESETS.keys())


def build_simulation_lab_payload(
    profile_key: str,
    *,
    scenario: str = "",
    environment: dict[str, Any] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Build Simulation Lab payload."""
    payload = compile_canonical_profile(profile_key, force=force)

    if not payload.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": payload.get("errors", []),
            "payload": payload,
            "simulation": {},
        }

    report = payload.get("systems_report", {})
    simulation = build_simulation_report(
        report,
        scenario=scenario,
        environment=environment,
    )

    return {
        "success": True,
        "profile_key": profile_key,
        "errors": [],
        "payload": payload,
        "systems_report": report,
        "simulation": simulation,
        "interpretation": build_simulation_interpretation(simulation),
    }



def build_simulation_interpretation(simulation: dict[str, Any]) -> dict[str, Any]:
    """Build human-readable simulation interpretation."""
    sim = simulation.get("simulation", {})
    decisions = sim.get("decisions", {})
    likely = decisions.get("likely_action") or {}
    recovery = sim.get("recovery", {})
    growth = simulation.get("growth", {})
    top_nodes = sim.get("propagation", {}).get("top_activated", [])[:5]

    action = likely.get("action", "unresolved")

    return {
        "headline": action_to_headline(action),
        "plain_english": action_to_plain_english(action),
        "what_activated": [
            clean_node(item.get("node_id", ""))
            for item in top_nodes
        ],
        "likely_behavior": action_to_behavior(action),
        "recovery_summary": " -> ".join(recovery.get("recovery_path", [])),
        "growth_summary": " -> ".join(growth.get("growth_sequence", [])),
        "interpretation": (
            f"In this scenario, Atlas expects the system to respond primarily through "
            f"{action.replace('_', ' ')}. The strongest activated patterns suggest that "
            f"the person will try to convert environmental pressure into structure before "
            f"acting too impulsively."
        ),
    }


def action_to_headline(action: str) -> str:
    """Return headline for likely action."""
    mapping = {
        "structure_plan": "Likely response: organize the pressure into a plan.",
        "protect_continuity": "Likely response: preserve what is already working.",
        "sequence_work": "Likely response: break the situation into ordered steps.",
        "map_relationships": "Likely response: map how the moving parts connect.",
        "gather_information": "Likely response: collect context before acting.",
        "connect_domains": "Likely response: synthesize across different domains.",
        "compress_into_model": "Likely response: turn complexity into a reusable model.",
        "build_symbolic_artifact": "Likely response: create an artifact that carries the pattern.",
        "name_the_pattern": "Likely response: identify the underlying pattern.",
        "explain_publicly": "Likely response: explain the structure to others.",
        "teach_framework": "Likely response: translate the structure into a teachable framework.",
        "publish_artifact": "Likely response: make the work visible as an artifact.",
        "reduce_noise": "Likely response: reduce noise before taking action.",
        "stabilize_environment": "Likely response: stabilize the environment first.",
        "execute_conservatively": "Likely response: act carefully inside constraints.",
    }
    return mapping.get(action, "Likely response: unresolved.")


def action_to_plain_english(action: str) -> str:
    """Return plain-English explanation."""
    if action in {"structure_plan", "sequence_work", "protect_continuity"}:
        return (
            "This profile is likely to slow the situation down, define the structure, "
            "and create an ordered path forward. Pressure is converted into architecture."
        )

    if action in {"map_relationships", "gather_information", "connect_domains"}:
        return (
            "This profile is likely to understand the system before acting. The first move "
            "is cognitive mapping: identifying relationships, missing context, and leverage points."
        )

    if action in {"compress_into_model", "build_symbolic_artifact", "name_the_pattern"}:
        return (
            "This profile is likely to compress complexity into a model, symbol, phrase, diagram, "
            "or reusable framework."
        )

    if action in {"explain_publicly", "teach_framework", "publish_artifact"}:
        return (
            "This profile is likely to externalize the structure through teaching, authorship, "
            "performance, or public explanation."
        )

    return (
        "This profile is likely to stabilize first, reduce noise, and then choose the next "
        "structurally safe action."
    )


def action_to_behavior(action: str) -> list[str]:
    """Return expected behaviors for likely action."""
    mapping = {
        "structure_plan": ["define scope", "sequence priorities", "protect continuity", "build a usable plan"],
        "map_relationships": ["map dependencies", "compare domains", "look for leverage points", "identify missing context"],
        "compress_into_model": ["simplify complexity", "name the pattern", "create a reusable model", "externalize the structure"],
        "explain_publicly": ["clarify the message", "teach the framework", "make the structure visible", "invite feedback"],
        "reduce_noise": ["remove distractions", "stabilize inputs", "lower ambiguity", "act conservatively"],
    }
    return mapping.get(action, ["stabilize", "observe", "structure", "act"])


def clean_node(node_id: str) -> str:
    """Clean node id for display."""
    return (
        str(node_id)
        .replace("theme:", "")
        .replace("inference:", "")
        .replace("_", " ")
    )
