
"""Population Intelligence v4 cluster metrics."""

from __future__ import annotations

from typing import Any


CLUSTER_METRICS_VERSION = "4.0.0"


def build_cluster_metrics(clustering: dict[str, Any]) -> dict[str, Any]:
    """Build metrics for cluster set."""
    clusters = clustering.get("clusters", []) or []

    rows = []

    for cluster in clusters:
        rows.append(
            {
                "cluster_id": cluster.get("cluster_id"),
                "member_count": cluster.get("member_count", 0),
                "cohesion": cluster.get("cohesion", 0.0),
                "dominant_class": first_label(cluster.get("dominant_system_classes", [])),
                "dominant_architecture": first_label(cluster.get("dominant_architectures", [])),
                "dominant_theme": first_label(cluster.get("dominant_themes", [])),
                "label": cluster.get("label"),
                "quality": cluster_quality(cluster),
            }
        )

    return {
        "success": True,
        "version": CLUSTER_METRICS_VERSION,
        "cluster_count": len(rows),
        "metrics": rows,
        "summary": build_metrics_summary(rows),
    }


def cluster_quality(cluster: dict[str, Any]) -> str:
    """Label cluster quality."""
    member_count = int(cluster.get("member_count") or 0)
    cohesion = float(cluster.get("cohesion") or 0.0)

    if member_count == 1:
        return "singleton"

    if cohesion >= 0.75:
        return "high_cohesion"

    if cohesion >= 0.55:
        return "moderate_cohesion"

    return "loose_cluster"


def build_metrics_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build metrics summary."""
    if not rows:
        return {
            "cluster_count": 0,
            "high_cohesion_count": 0,
            "singleton_count": 0,
        }

    return {
        "cluster_count": len(rows),
        "high_cohesion_count": sum(1 for row in rows if row.get("quality") == "high_cohesion"),
        "moderate_cohesion_count": sum(1 for row in rows if row.get("quality") == "moderate_cohesion"),
        "singleton_count": sum(1 for row in rows if row.get("quality") == "singleton"),
        "loose_cluster_count": sum(1 for row in rows if row.get("quality") == "loose_cluster"),
    }


def first_label(rows: list[dict[str, Any]]) -> str:
    """Return first label from count rows."""
    if not rows:
        return ""

    return str(rows[0].get("label") or "")
