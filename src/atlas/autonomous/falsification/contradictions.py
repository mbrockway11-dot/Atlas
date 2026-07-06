
"""Contradiction detection for autonomous theories."""

from __future__ import annotations

from typing import Any


def find_contradictions(
    theory: dict[str, Any],
    evidence_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find evidence with opposing direction against theory variable family."""
    theory_vars = set(theory.get("variables", []) or [])
    contradictions = []

    expected_direction = infer_expected_direction(theory)

    for evidence in evidence_records:
        evidence_vars = set(evidence.get("variables", []) or [])
        overlap = len(theory_vars & evidence_vars) / max(1, len(theory_vars | evidence_vars))

        if overlap <= 0:
            continue

        direction = (evidence.get("metadata", {}) or {}).get("direction")

        if expected_direction != "unknown" and direction and direction != expected_direction:
            contradictions.append(
                {
                    "evidence_id": evidence.get("evidence_id"),
                    "expected_direction": expected_direction,
                    "observed_direction": direction,
                    "variable_overlap": round(overlap, 6),
                    "evidence": evidence,
                }
            )

    return contradictions


def infer_expected_direction(theory: dict[str, Any]) -> str:
    """Infer expected direction from theory label/domain."""
    text = f"{theory.get('label', '')} {theory.get('domain', '')}".lower()

    if "recovery" in text or "attractor" in text or "recurrence" in text:
        return "positive"

    if "sensitivity" in text:
        return "positive"

    return "unknown"
