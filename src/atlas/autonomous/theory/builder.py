
"""Autonomous theory builder."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_theory_candidates(
    evidence_records: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build theory candidates from evidence and hypotheses."""
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for evidence in evidence_records:
        key = theory_bucket_key(evidence)
        buckets[key].append(evidence)

    candidates = []

    for key, rows in buckets.items():
        candidates.append(
            {
                "theory_id": f"theory::{key}",
                "label": theory_label(key),
                "domain": key,
                "evidence_count": len(rows),
                "evidence_ids": [row.get("evidence_id") for row in rows],
                "variables": sorted({var for row in rows for var in row.get("variables", [])}),
                "mean_confidence": mean([row.get("confidence", 0.0) for row in rows]),
                "mean_effect_size": mean([row.get("effect_size", 0.0) for row in rows]),
                "hypothesis_links": link_hypotheses(rows, hypotheses or []),
                "status": "candidate",
            }
        )

    return sorted(candidates, key=lambda item: item.get("mean_confidence", 0.0), reverse=True)


def theory_bucket_key(evidence: dict[str, Any]) -> str:
    """Assign evidence to theory bucket."""
    variables = " ".join(evidence.get("variables", []) or []).lower()
    question = str(evidence.get("question", "")).lower()

    if "recovery" in variables or "recovery" in question:
        return "dynamic_recovery"
    if "sensitivity" in variables or "sensitivity" in question:
        return "perturbation_sensitivity"
    if "attractor" in variables or "attractor" in question:
        return "attractor_basin"
    if "recurrence" in variables or "recurrence" in question:
        return "recurrence_structure"

    return "general_dynamic_structure"


def theory_label(key: str) -> str:
    """Human label for theory bucket."""
    return {
        "dynamic_recovery": "Dynamic Recovery Theory",
        "perturbation_sensitivity": "Perturbation Sensitivity Theory",
        "attractor_basin": "Attractor Basin Theory",
        "recurrence_structure": "Recurrence Structure Theory",
        "general_dynamic_structure": "General Dynamic Structure Theory",
    }.get(key, key.replace("_", " ").title())


def link_hypotheses(
    evidence_rows: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
) -> list[str]:
    """Link hypotheses by variable overlap."""
    variables = {var for row in evidence_rows for var in row.get("variables", [])}
    links = []

    for hypothesis in hypotheses:
        h_text = str(hypothesis).lower()
        if any(var.lower() in h_text for var in variables):
            links.append(str(hypothesis.get("hypothesis_id") or hypothesis.get("candidate_id")))

    return sorted(set(links))


def mean(values: list[Any]) -> float:
    """Mean numeric values."""
    nums = []
    for value in values:
        try:
            nums.append(float(value))
        except Exception:
            pass

    if not nums:
        return 0.0

    return round(sum(nums) / len(nums), 6)
