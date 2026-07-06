
"""Counterexample search for autonomous theories."""

from __future__ import annotations

from typing import Any


def find_counterexamples(
    theory: dict[str, Any],
    evidence_records: list[dict[str, Any]],
    *,
    threshold: float = 0.25,
) -> list[dict[str, Any]]:
    """Find evidence that weakens or contradicts a theory."""
    theory_vars = set(theory.get("variables", []) or [])
    rows = []

    for evidence in evidence_records:
        evidence_vars = set(evidence.get("variables", []) or [])
        overlap = len(theory_vars & evidence_vars) / max(1, len(theory_vars | evidence_vars))

        if overlap <= 0:
            continue

        confidence = float(evidence.get("confidence") or 0.0)
        effect_size = float(evidence.get("effect_size") or 0.0)
        status = evidence.get("status")

        if status == "weak" or confidence < threshold or effect_size < threshold:
            rows.append(
                {
                    "evidence_id": evidence.get("evidence_id"),
                    "reason": "weak_or_low_effect_support",
                    "confidence": confidence,
                    "effect_size": effect_size,
                    "variable_overlap": round(overlap, 6),
                    "evidence": evidence,
                }
            )

    return rows
