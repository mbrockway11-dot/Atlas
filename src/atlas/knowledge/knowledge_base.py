
"""Atlas Knowledge Base.

Stores durable discoveries, hypotheses, evidence links, and confidence updates.
This module is intentionally JSON-serializable and deterministic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


KNOWLEDGE_BASE_VERSION = "1.0.0"


def create_knowledge_base() -> dict[str, Any]:
    """Create empty knowledge base."""
    return {
        "success": True,
        "version": KNOWLEDGE_BASE_VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "hypotheses": {},
        "insights": {},
        "evidence": {},
        "relations": [],
    }


def add_hypothesis(
    knowledge_base: dict[str, Any],
    hypothesis: dict[str, Any],
) -> dict[str, Any]:
    """Add or update hypothesis in knowledge base."""
    hypothesis_id = str(
        hypothesis.get("hypothesis_id")
        or hypothesis.get("id")
        or build_id("hypothesis", hypothesis.get("hypothesis", "unknown"))
    )

    existing = knowledge_base.setdefault("hypotheses", {}).get(hypothesis_id, {})

    merged = {
        **existing,
        **hypothesis,
        "hypothesis_id": hypothesis_id,
        "updated_at": utc_now(),
        "created_at": existing.get("created_at") or utc_now(),
    }

    knowledge_base["hypotheses"][hypothesis_id] = merged
    knowledge_base["updated_at"] = utc_now()

    return knowledge_base


def add_insight(
    knowledge_base: dict[str, Any],
    insight: dict[str, Any],
) -> dict[str, Any]:
    """Add or update insight in knowledge base."""
    insight_id = str(
        insight.get("insight_id")
        or insight.get("id")
        or build_id("insight", insight.get("summary", insight.get("insight", "unknown")))
    )

    existing = knowledge_base.setdefault("insights", {}).get(insight_id, {})

    merged = {
        **existing,
        **insight,
        "insight_id": insight_id,
        "updated_at": utc_now(),
        "created_at": existing.get("created_at") or utc_now(),
    }

    knowledge_base["insights"][insight_id] = merged
    knowledge_base["updated_at"] = utc_now()

    return knowledge_base


def add_evidence(
    knowledge_base: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Add evidence item."""
    evidence_id = str(
        evidence.get("evidence_id")
        or evidence.get("id")
        or build_id("evidence", evidence.get("source", evidence.get("feature", "unknown")))
    )

    existing = knowledge_base.setdefault("evidence", {}).get(evidence_id, {})

    merged = {
        **existing,
        **evidence,
        "evidence_id": evidence_id,
        "updated_at": utc_now(),
        "created_at": existing.get("created_at") or utc_now(),
    }

    knowledge_base["evidence"][evidence_id] = merged
    knowledge_base["updated_at"] = utc_now()

    return knowledge_base


def add_relation(
    knowledge_base: dict[str, Any],
    source_id: str,
    target_id: str,
    relation: str,
    *,
    weight: float = 1.0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add relation edge."""
    row = {
        "source": source_id,
        "target": target_id,
        "relation": relation,
        "weight": float(weight),
        "metadata": metadata or {},
        "created_at": utc_now(),
    }

    knowledge_base.setdefault("relations", []).append(row)
    knowledge_base["updated_at"] = utc_now()

    return knowledge_base


def build_id(prefix: str, text: Any) -> str:
    """Build stable simple ID."""
    label = (
        str(text or "unknown")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    label = "".join(char for char in label if char.isalnum() or char == "_")
    return f"{prefix}::{label[:80] or 'unknown'}"


def utc_now() -> str:
    """Return UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
