
"""Theory clustering."""

from __future__ import annotations

from typing import Any


def cluster_theories(theories: list[dict[str, Any]]) -> dict[str, Any]:
    """Cluster theories by variable overlap."""
    clusters = []

    remaining = list(theories)
    cluster_id = 1

    while remaining:
        seed = remaining.pop(0)
        seed_vars = set(seed.get("variables", []) or [])
        members = [seed]
        rest = []

        for item in remaining:
            vars_ = set(item.get("variables", []) or [])
            overlap = len(seed_vars & vars_) / max(1, len(seed_vars | vars_))

            if overlap >= 0.25:
                members.append(item)
            else:
                rest.append(item)

        clusters.append(
            {
                "cluster_id": f"theory_cluster_{cluster_id:03d}",
                "member_count": len(members),
                "members": [item.get("theory_id") for item in members],
                "dominant_variables": sorted({
                    var for item in members for var in item.get("variables", []) or []
                }),
                "mean_theory_score": mean([item.get("theory_score", 0.0) for item in members]),
            }
        )

        remaining = rest
        cluster_id += 1

    return {
        "success": True,
        "cluster_count": len(clusters),
        "clusters": clusters,
    }


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
