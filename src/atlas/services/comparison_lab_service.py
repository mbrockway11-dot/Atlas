
"""Service layer for Comparison Lab dashboard."""

from __future__ import annotations

from typing import Any

from atlas.comparison_v3 import build_comparison_v3_report
from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.dynamics import build_dynamic_resonance_v2
from atlas.library.profile_library import list_saved_profiles
from atlas.simulation.scenarios import SCENARIO_PRESETS


def list_comparison_profiles() -> list[str]:
    """List profiles available for comparison."""
    return list_saved_profiles()


def list_comparison_scenarios() -> list[str]:
    """List simulation scenario presets."""
    return sorted(SCENARIO_PRESETS.keys())


def build_comparison_lab_payload(
    left_profile_key: str,
    right_profile_key: str,
    scenarios: list[str],
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Build Comparison Lab payload."""
    left_payload = compile_canonical_profile(left_profile_key, force=force)
    right_payload = compile_canonical_profile(right_profile_key, force=force)

    errors = []

    if not left_payload.get("success"):
        errors.append(
            {
                "profile": left_profile_key,
                "errors": left_payload.get("errors", []),
            }
        )

    if not right_payload.get("success"):
        errors.append(
            {
                "profile": right_profile_key,
                "errors": right_payload.get("errors", []),
            }
        )

    if errors:
        return {
            "success": False,
            "errors": errors,
            "left_payload": left_payload,
            "right_payload": right_payload,
            "comparison": {},
        }

    comparison = build_comparison_v3_report(
        left_profile_key,
        left_payload,
        right_profile_key,
        right_payload,
        scenarios=scenarios,
    )

    dynamic_resonance = build_dynamic_resonance_v2(
        left_payload,
        right_payload,
    )

    comparison["dynamic_resonance_v2"] = dynamic_resonance

    return {
        "success": True,
        "errors": [],
        "left_payload": left_payload,
        "right_payload": right_payload,
        "comparison": comparison,
        "dynamic_resonance": dynamic_resonance,
    }
