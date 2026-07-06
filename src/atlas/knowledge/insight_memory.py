
"""Insight Memory.

Converts Discovery results into persistent insight records.
"""

from __future__ import annotations

from typing import Any

from atlas.knowledge.knowledge_base import add_insight, add_relation


INSIGHT_MEMORY_VERSION = "1.0.0"


def store_discovery_insights(
    knowledge_base: dict[str, Any],
    discovery_report: dict[str, Any],
) -> dict[str, Any]:
    """Store ranked Discovery evidence as insights."""
    ranked = discovery_report.get("ranked_evidence", []) or []

    for index, item in enumerate(ranked, start=1):
        insight_id = f"insight::{item.get('hypothesis_id')}"

        knowledge_base = add_insight(
            knowledge_base,
            {
                "insight_id": insight_id,
                "source": "discovery_engine",
                "rank": index,
                "rank_score": item.get("rank_score"),
                "confidence": item.get("confidence"),
                "summary": item.get("hypothesis"),
                "hypothesis_id": item.get("hypothesis_id"),
                "strength": item.get("strength"),
                "direction": item.get("direction"),
                "correlation": item.get("correlation"),
                "sample_size": item.get("sample_size"),
                "memory_version": INSIGHT_MEMORY_VERSION,
            },
        )

        knowledge_base = add_relation(
            knowledge_base,
            insight_id,
            item.get("hypothesis_id"),
            "summarizes",
            weight=float(item.get("rank_score") or 0.0),
        )

    return knowledge_base


def recall_top_insights(
    knowledge_base: dict[str, Any],
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Recall strongest stored insights."""
    rows = list((knowledge_base.get("insights", {}) or {}).values())

    rows.sort(
        key=lambda item: (
            -float(item.get("rank_score") or 0.0),
            str(item.get("insight_id") or ""),
        )
    )

    return rows[:limit]
