
"""Population Intelligence v4 outlier detection."""

from __future__ import annotations

from typing import Any

from atlas.population_v4.neighbors import find_population_neighbors


OUTLIER_VERSION = "4.0.0"


def build_population_outliers(
    corpus: dict[str, Any],
    cluster_report: dict[str, Any] | None = None,
    archetypes: dict[str, Any] | None = None,
    *,
    neighbor_limit: int = 5,
) -> dict[str, Any]:
    """Detect population outliers using neighbors, clusters, and archetypes."""
    records = corpus.get("records", []) or []
    cluster_lookup = build_cluster_lookup(cluster_report or {})
    archetype_lookup = (archetypes or {}).get("profile_assignments", {}) or {}

    rows = []

    for record in records:
        profile_key = record.get("profile_key")

        if not profile_key:
            continue

        neighbors = find_population_neighbors(
            corpus,
            profile_key,
            limit=neighbor_limit,
        )

        row = build_outlier_row(
            record,
            neighbors,
            cluster_lookup.get(profile_key, {}),
            archetype_lookup.get(profile_key, {}),
        )
        rows.append(row)

    rows.sort(key=lambda item: item.get("outlier_score", 0.0), reverse=True)

    return {
        "success": True,
        "version": OUTLIER_VERSION,
        "profile_count": len(records),
        "outlier_count": len(rows),
        "outliers": rows,
        "summary": build_outlier_summary(rows),
    }


def build_outlier_row(
    record: dict[str, Any],
    neighbors: dict[str, Any],
    cluster: dict[str, Any],
    archetype: dict[str, Any],
) -> dict[str, Any]:
    """Build one outlier row."""
    nearest = neighbors.get("neighbors", []) or []
    nearest_similarity = float(nearest[0].get("similarity") or 0.0) if nearest else 0.0
    mean_neighbor_similarity = float((neighbors.get("summary") or {}).get("mean_similarity") or 0.0)

    cluster_size = int(cluster.get("member_count") or 1)
    cluster_cohesion = float(cluster.get("cohesion") or 0.0)
    archetype_quality = str(archetype.get("quality") or "unassigned")

    isolation_score = 1.0 - nearest_similarity
    weak_neighbor_score = 1.0 - mean_neighbor_similarity
    singleton_score = 1.0 if cluster_size <= 1 else 0.0
    weak_cluster_score = 1.0 - cluster_cohesion

    archetype_score = archetype_outlier_score(archetype_quality)

    outlier_score = (
        isolation_score * 0.30
        + weak_neighbor_score * 0.25
        + singleton_score * 0.20
        + weak_cluster_score * 0.15
        + archetype_score * 0.10
    )

    return {
        "profile_key": record.get("profile_key"),
        "outlier_score": round(outlier_score, 6),
        "label": outlier_label(outlier_score),
        "nearest_similarity": round(nearest_similarity, 6),
        "mean_neighbor_similarity": round(mean_neighbor_similarity, 6),
        "cluster_id": cluster.get("cluster_id"),
        "cluster_size": cluster_size,
        "cluster_cohesion": round(cluster_cohesion, 6),
        "archetype_id": archetype.get("archetype_id"),
        "archetype_name": archetype.get("archetype_name"),
        "archetype_quality": archetype_quality,
        "drivers": build_outlier_drivers(
            isolation_score=isolation_score,
            weak_neighbor_score=weak_neighbor_score,
            singleton_score=singleton_score,
            weak_cluster_score=weak_cluster_score,
            archetype_score=archetype_score,
        ),
    }


def build_cluster_lookup(cluster_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build profile -> cluster lookup."""
    lookup = {}
    clusters = cluster_report.get("clustering", {}).get("clusters", []) or cluster_report.get("clusters", []) or []

    for cluster in clusters:
        for profile_key in cluster.get("members", []) or []:
            lookup[profile_key] = {
                "cluster_id": cluster.get("cluster_id"),
                "member_count": cluster.get("member_count"),
                "cohesion": cluster.get("cohesion"),
                "label": cluster.get("label"),
            }

    return lookup


def archetype_outlier_score(quality: str) -> float:
    """Score archetype quality as outlier pressure."""
    if quality == "strong_archetype":
        return 0.0

    if quality == "emerging_archetype":
        return 0.25

    if quality == "loose_archetype":
        return 0.55

    if quality == "single_case_archetype":
        return 0.85

    return 0.65


def build_outlier_drivers(
    *,
    isolation_score: float,
    weak_neighbor_score: float,
    singleton_score: float,
    weak_cluster_score: float,
    archetype_score: float,
) -> list[str]:
    """Build human-readable outlier drivers."""
    drivers = []

    if isolation_score >= 0.65:
        drivers.append("low nearest-neighbor similarity")

    if weak_neighbor_score >= 0.65:
        drivers.append("weak average neighbor similarity")

    if singleton_score >= 1.0:
        drivers.append("singleton cluster membership")

    if weak_cluster_score >= 0.65:
        drivers.append("low cluster cohesion")

    if archetype_score >= 0.65:
        drivers.append("weak or single-case archetype assignment")

    if not drivers:
        drivers.append("mild distributed distinctiveness")

    return drivers


def outlier_label(score: float) -> str:
    """Label outlier score."""
    if score >= 0.75:
        return "extreme_outlier"

    if score >= 0.60:
        return "strong_outlier"

    if score >= 0.42:
        return "moderate_outlier"

    if score >= 0.25:
        return "mild_outlier"

    return "population_embedded"


def build_outlier_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build outlier summary."""
    if not rows:
        return {
            "extreme_outlier_count": 0,
            "strong_outlier_count": 0,
            "moderate_outlier_count": 0,
            "top_outliers": [],
        }

    return {
        "extreme_outlier_count": count_label(rows, "extreme_outlier"),
        "strong_outlier_count": count_label(rows, "strong_outlier"),
        "moderate_outlier_count": count_label(rows, "moderate_outlier"),
        "mild_outlier_count": count_label(rows, "mild_outlier"),
        "embedded_count": count_label(rows, "population_embedded"),
        "top_outliers": rows[:20],
        "mean_outlier_score": round(
            sum(float(row.get("outlier_score") or 0.0) for row in rows) / len(rows),
            6,
        ),
    }


def count_label(rows: list[dict[str, Any]], label: str) -> int:
    """Count rows with label."""
    return sum(1 for row in rows if row.get("label") == label)
