
"""Hypothesis Registry.

Turns Discovery Engine hypotheses into durable knowledge records.
"""

from __future__ import annotations

from typing import Any

from atlas.knowledge.knowledge_base import add_evidence, add_hypothesis, add_relation


REGISTRY_VERSION = "1.0.0"


def register_discovery_hypotheses(
    knowledge_base: dict[str, Any],
    discovery_report: dict[str, Any],
) -> dict[str, Any]:
    """Register hypotheses from a Discovery Engine report."""
    hypotheses = discovery_report.get("hypotheses", []) or []

    for hypothesis in hypotheses:
        knowledge_base = register_hypothesis(knowledge_base, hypothesis)

    return knowledge_base


def register_hypothesis(
    knowledge_base: dict[str, Any],
    hypothesis: dict[str, Any],
) -> dict[str, Any]:
    """Register one hypothesis and its evidence."""
    hypothesis_id = hypothesis.get("hypothesis_id")

    knowledge_base = add_hypothesis(
        knowledge_base,
        {
            **hypothesis,
            "registry_version": REGISTRY_VERSION,
            "status": hypothesis.get("status", "active"),
            "confidence": float(hypothesis.get("confidence") or 0.0),
        },
    )

    evidence = hypothesis.get("evidence", {}) or {}
    evidence_id = f"evidence::{hypothesis_id}"

    knowledge_base = add_evidence(
        knowledge_base,
        {
            "evidence_id": evidence_id,
            "hypothesis_id": hypothesis_id,
            "source": "discovery_engine",
            "x_field": evidence.get("x_field"),
            "y_field": evidence.get("y_field"),
            "supporting_rows": evidence.get("supporting_rows", []),
            "sample_size": hypothesis.get("sample_size"),
            "correlation": hypothesis.get("correlation"),
            "strength": hypothesis.get("strength"),
            "direction": hypothesis.get("direction"),
        },
    )

    knowledge_base = add_relation(
        knowledge_base,
        evidence_id,
        hypothesis_id,
        "supports",
        weight=float(hypothesis.get("confidence") or 0.0),
    )

    return knowledge_base


def update_hypothesis_confidence(
    knowledge_base: dict[str, Any],
    hypothesis_id: str,
    confidence_delta: float,
) -> dict[str, Any]:
    """Update confidence for a hypothesis."""
    hypothesis = knowledge_base.setdefault("hypotheses", {}).get(hypothesis_id)

    if not hypothesis:
        return knowledge_base

    current = float(hypothesis.get("confidence") or 0.0)
    hypothesis["confidence"] = max(0.0, min(0.99, current + confidence_delta))

    return knowledge_base
