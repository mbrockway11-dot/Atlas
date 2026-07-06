
"""Evidence registry."""

from __future__ import annotations

from typing import Any


def create_evidence_registry() -> dict[str, Any]:
    """Create empty evidence registry."""
    return {
        "success": True,
        "records": {},
        "relations": [],
    }


def register_evidence(
    registry: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Register one evidence record."""
    evidence_id = evidence.get("evidence_id")

    if not evidence_id:
        return registry

    registry.setdefault("records", {})[evidence_id] = evidence
    return registry


def register_many(
    registry: dict[str, Any],
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Register many evidence records."""
    for record in evidence_records:
        registry = register_evidence(registry, record)

    return registry


def link_evidence(
    registry: dict[str, Any],
    source_id: str,
    target_id: str,
    relation: str,
    *,
    weight: float = 1.0,
) -> dict[str, Any]:
    """Link evidence to another object."""
    registry.setdefault("relations", []).append(
        {
            "source": source_id,
            "target": target_id,
            "relation": relation,
            "weight": float(weight),
        }
    )
    return registry
