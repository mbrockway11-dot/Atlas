
"""Autonomous Falsification Engine report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.falsification.challenger import challenge_theory


FALSIFICATION_VERSION = "1.0.0"


def build_falsification_report(
    theories: list[dict[str, Any]],
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build falsification report for theories."""
    challenges = [
        challenge_theory(theory, evidence_records)
        for theory in theories
    ]

    return {
        "success": True,
        "version": FALSIFICATION_VERSION,
        "theory_count": len(theories),
        "evidence_count": len(evidence_records),
        "challenge_count": len(challenges),
        "challenges": challenges,
        "summary": build_summary(challenges),
    }


def build_summary(challenges: list[dict[str, Any]]) -> str:
    """Build summary."""
    survived = sum(1 for item in challenges if item.get("status") == "survived_initial_challenge")
    contradicted = sum(1 for item in challenges if item.get("status") == "challenged_by_contradiction")
    weakened = sum(1 for item in challenges if item.get("status") == "weakened_by_counterexamples")

    return (
        f"Falsification Engine challenged {len(challenges)} theory/theories. "
        f"Survived: {survived}. Contradicted: {contradicted}. Weakened: {weakened}."
    )
