
"""Service layer for Decision Lab dashboard."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.decision_engine import build_decision_report
from atlas.decision_engine.choice import make_choice
from atlas.library.profile_library import list_saved_profiles
from atlas.simulation.scenarios import SCENARIO_PRESETS


def list_decision_profiles() -> list[str]:
    """List profiles available for Decision Lab."""
    return list_saved_profiles()


def list_decision_scenarios() -> list[str]:
    """List available scenario presets."""
    return sorted(SCENARIO_PRESETS.keys())


def build_decision_lab_payload(
    profile_key: str,
    choices: list[dict[str, Any]],
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Build Decision Lab payload."""
    payload = compile_canonical_profile(profile_key, force=force)

    if not payload.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": payload.get("errors", []),
            "payload": payload,
            "decision_report": {},
        }

    systems_report = payload.get("systems_report", {})

    decision_choices = [
        make_choice(
            choice_id=str(item.get("choice_id") or f"choice_{index + 1}"),
            label=str(item.get("label") or f"Choice {index + 1}"),
            scenario=str(item.get("scenario") or ""),
            environment=item.get("environment") or {},
            notes=str(item.get("notes") or ""),
        )
        for index, item in enumerate(choices)
    ]

    decision_report = build_decision_report(
        systems_report,
        decision_choices,
    )

    return {
        "success": True,
        "profile_key": profile_key,
        "errors": [],
        "payload": payload,
        "systems_report": systems_report,
        "decision_report": decision_report,
    }
