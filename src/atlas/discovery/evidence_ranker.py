
"""Discovery evidence ranking."""

from __future__ import annotations

from typing import Any


def rank_discovery_evidence(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank hypotheses/evidence by confidence and sample size."""
    rows = []

    for item in hypotheses:
        rows.append(
            {
                "hypothesis_id": item.get("hypothesis_id"),
                "hypothesis": item.get("hypothesis"),
                "rank_score": rank_score(item),
                "confidence": item.get("confidence"),
                "strength": item.get("strength"),
                "direction": item.get("direction"),
                "correlation": item.get("correlation"),
                "sample_size": item.get("sample_size"),
            }
        )

    return sorted(rows, key=lambda item: item.get("rank_score", 0.0), reverse=True)


def rank_score(item: dict[str, Any]) -> float:
    """Score ranked evidence."""
    confidence = float(item.get("confidence") or 0.0)
    correlation = abs(float(item.get("correlation") or 0.0))
    sample_size = min(1.0, float(item.get("sample_size") or 0.0) / 100)

    return round(confidence * 0.55 + correlation * 0.30 + sample_size * 0.15, 6)
