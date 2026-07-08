
"""Alpha strategy promotion rules."""

from __future__ import annotations

from typing import Any


def promote_alpha_strategies(validations: list[dict[str, Any]]) -> dict[str, Any]:
    promoted = []
    rejected = []

    for item in validations:
        confidence = item.get("confidence", {})
        robust = item.get("validation", {}).get("robustness", {})
        metrics = item.get("metrics", {})

        passes = (
            confidence.get("alpha_confidence", 0) >= 0.70
            and robust.get("trade_count", 0) >= 30
            and robust.get("asset_concentration", 1.0) <= 0.75
            and (metrics.get("non_overlap_avg_return") or metrics.get("avg_return") or 0) > 0
        )

        item["promoted"] = bool(passes)

        if passes:
            promoted.append(item)
        else:
            rejected.append(item)

    return {
        "success": True,
        "promoted_count": len(promoted),
        "rejected_count": len(rejected),
        "promoted": promoted,
        "rejected": rejected,
        "summary": f"Promoted {len(promoted)} alpha strategy/strategies. Rejected {len(rejected)}.",
    }
