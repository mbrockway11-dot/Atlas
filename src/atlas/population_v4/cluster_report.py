
"""Population Intelligence v4 cluster report."""

from __future__ import annotations

from typing import Any

from atlas.population_v4.cluster_metrics import build_cluster_metrics
from atlas.population_v4.clustering import build_hierarchical_clusters
from atlas.population_v4.dendrogram import build_cluster_dendrogram


CLUSTER_REPORT_VERSION = "4.0.0"


def build_population_cluster_report(
    corpus: dict[str, Any],
    *,
    threshold: float = 0.55,
) -> dict[str, Any]:
    """Build full Population v4 cluster report."""
    clustering = build_hierarchical_clusters(
        corpus,
        threshold=threshold,
    )
    metrics = build_cluster_metrics(clustering)
    dendrogram = build_cluster_dendrogram(clustering)

    return {
        "success": True,
        "version": CLUSTER_REPORT_VERSION,
        "threshold": threshold,
        "profile_count": clustering.get("profile_count", 0),
        "cluster_count": clustering.get("cluster_count", 0),
        "clustering": clustering,
        "metrics": metrics,
        "dendrogram": dendrogram,
        "summary": build_report_summary(clustering, metrics),
    }


def build_report_summary(
    clustering: dict[str, Any],
    metrics: dict[str, Any],
) -> str:
    """Build human-readable cluster report summary."""
    cluster_summary = clustering.get("summary", {}) or {}
    metric_summary = metrics.get("summary", {}) or {}

    return (
        f"Population clustering produced {clustering.get('cluster_count', 0)} cluster(s) "
        f"across {clustering.get('profile_count', 0)} profile(s). "
        f"Largest cluster size: {cluster_summary.get('largest_cluster_size', 0)}. "
        f"High-cohesion clusters: {metric_summary.get('high_cohesion_count', 0)}. "
        f"Singletons: {metric_summary.get('singleton_count', 0)}."
    )
