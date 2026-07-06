
"""Service layer for Evolution Lab dashboard."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.evolution import build_evolution_report
from atlas.library.profile_library import list_saved_profiles
from atlas.simulation import build_simulation_report
from atlas.simulation.scenarios import SCENARIO_PRESETS


def list_evolution_profiles() -> list[str]:
    """List profiles available for evolution modeling."""
    return list_saved_profiles()


def list_evolution_scenarios() -> list[str]:
    """List simulation scenario presets."""
    return sorted(SCENARIO_PRESETS.keys())


def build_evolution_lab_payload(
    profile_key: str,
    scenarios: list[str],
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Build Evolution Lab payload."""
    payload = compile_canonical_profile(profile_key, force=force)

    if not payload.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": payload.get("errors", []),
            "payload": payload,
            "simulations": [],
            "evolution": {},
        }

    systems_report = payload.get("systems_report", {})

    simulations = [
        build_simulation_report(
            systems_report,
            scenario=scenario,
        )
        for scenario in scenarios
    ]

    evolution = build_evolution_report(
        profile_key,
        simulations,
    )

    return {
        "success": True,
        "profile_key": profile_key,
        "errors": [],
        "payload": payload,
        "systems_report": systems_report,
        "simulations": simulations,
        "evolution": evolution,
    }
