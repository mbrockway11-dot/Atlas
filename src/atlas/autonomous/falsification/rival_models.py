
"""Rival model generation for autonomous theories."""

from __future__ import annotations

from typing import Any


def build_rival_models(theory: dict[str, Any]) -> list[dict[str, Any]]:
    """Build rival explanations for a theory."""
    variables = theory.get("variables", []) or []
    rivals = []

    if any("recovery" in var for var in variables):
        rivals.append(
            {
                "rival_id": f"rival::{theory.get('theory_id')}::hidden_attractor_density",
                "claim": "Recovery may be driven by attractor density rather than recurrence.",
                "variables": variables,
                "status": "candidate_rival",
            }
        )

    if any("sensitivity" in var for var in variables):
        rivals.append(
            {
                "rival_id": f"rival::{theory.get('theory_id')}::formula_dependency",
                "claim": "Sensitivity may be formula-derived from energy rather than independently discovered.",
                "variables": variables,
                "status": "candidate_rival",
            }
        )

    rivals.append(
        {
            "rival_id": f"rival::{theory.get('theory_id')}::sample_artifact",
            "claim": "The observed relationship may be an artifact of sample composition or derived metrics.",
            "variables": variables,
            "status": "general_rival",
        }
    )

    return rivals
