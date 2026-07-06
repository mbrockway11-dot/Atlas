
"""Theory updater."""

from __future__ import annotations

from typing import Any


def update_theory_with_evidence(
    theory: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Update one theory with new evidence."""
    evidence_ids = list(theory.get("evidence_ids", []) or [])
    evidence_id = evidence.get("evidence_id")

    if evidence_id and evidence_id not in evidence_ids:
        evidence_ids.append(evidence_id)

    variables = sorted(set(list(theory.get("variables", []) or []) + list(evidence.get("variables", []) or [])))

    return {
        **theory,
        "evidence_ids": evidence_ids,
        "evidence_count": len(evidence_ids),
        "variables": variables,
        "status": "updated",
    }


def merge_theory_updates(
    existing_theories: list[dict[str, Any]],
    new_theories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge new theories into existing theories by theory_id."""
    merged = {item.get("theory_id"): item for item in existing_theories}

    for theory in new_theories:
        theory_id = theory.get("theory_id")
        if theory_id in merged:
            merged[theory_id] = {
                **merged[theory_id],
                **theory,
                "status": "updated",
            }
        else:
            merged[theory_id] = theory

    return list(merged.values())
