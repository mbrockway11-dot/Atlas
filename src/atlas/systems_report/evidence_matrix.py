
"""Evidence matrix section."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_evidence_matrix(payload: dict[str, Any]) -> dict[str, Any]:
    """Build evidence matrix grouped by engine and feature."""
    evidence = payload.get("synthesis", {}).get("evidence", {}).get("evidence", [])

    by_engine = defaultdict(list)
    by_feature = defaultdict(list)
    by_category = defaultdict(list)

    for item in evidence:
        by_engine[item.get("engine", "unknown")].append(item)
        by_feature[item.get("feature", "unknown")].append(item)
        by_category[item.get("category", "unknown")].append(item)

    return {
        "evidence_count": len(evidence),
        "engine_count": len(by_engine),
        "feature_count": len(by_feature),
        "category_count": len(by_category),
        "by_engine": dict(by_engine),
        "by_feature": dict(by_feature),
        "by_category": dict(by_category),
    }
