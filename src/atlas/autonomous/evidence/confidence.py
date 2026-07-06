
"""Evidence confidence utilities."""

from __future__ import annotations

from typing import Any


def aggregate_evidence_confidence(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate confidence across evidence records."""
    if not records:
        return {
            "record_count": 0,
            "mean_confidence": 0.0,
            "max_confidence": 0.0,
            "active_count": 0,
        }

    confidences = [float(item.get("confidence") or 0.0) for item in records]

    return {
        "record_count": len(records),
        "mean_confidence": round(sum(confidences) / len(confidences), 6),
        "max_confidence": round(max(confidences), 6),
        "active_count": sum(1 for item in records if item.get("status") == "active"),
        "weak_count": sum(1 for item in records if item.get("status") == "weak"),
    }
