
"""Population Intelligence v4 structural impact engine."""

from __future__ import annotations

from typing import Any

from atlas.population_v4.neighbors import find_neighbors_for_all


IMPACT_VERSION = "4.0.0"


def build_structural_impact_report(
    corpus: dict[str, Any],
    cluster_report: dict[str, Any] | None = None,
    archetypes: dict[str, Any] | None = None,
    *,
    neighbor_limit: int = 5,
) -> dict[str, Any]:
    """Build structural impact report for a population corpus."""
    records = corpus.get("records", []) or []
    profile_lookup = {record.get("profile_key"): record for record in records if record.get("profile_key")}

    neighbor_reports = find_neighbors_for_all(corpus, limit=neighbor_limit)
    inbound_counts = build_inbound_neighbor_counts(neighbor_reports)

    cluster_lookup = build_cluster_lookup(cluster_report or {})
    archetype_lookup = (archetypes or {}).get("profile_assignments", {}) or {}

    feature_frequencies = build_feature_frequencies(records)

    rows = []

    for profile_key, record in profile_lookup.items():
        rows.append(
            build_impact_row(
                record,
                inbound_counts,
                cluster_lookup.get(profile_key, {}),
                archetype_lookup.get(profile_key, {}),
                feature_frequencies,
                len(records),
            )
        )

    rows.sort(key=lambda item: item.get("impact_score", 0.0), reverse=True)

    return {
        "success": True,
        "version": IMPACT_VERSION,
        "profile_count": len(records),
        "impact_rows": rows,
        "summary": build_impact_summary(rows),
    }


def build_impact_row(
    record: dict[str, Any],
    inbound_counts: dict[str, int],
    cluster: dict[str, Any],
    archetype: dict[str, Any],
    feature_frequencies: dict[str, int],
    population_size: int,
) -> dict[str, Any]:
    """Build one profile impact row."""
    profile_key = record.get("profile_key")

    inbound_neighbor_count = inbound_counts.get(profile_key, 0)
    neighbor_centrality = inbound_neighbor_count / max(1, population_size - 1)

    cluster_size = int(cluster.get("member_count") or 1)
    cluster_cohesion = float(cluster.get("cohesion") or 0.0)
    cluster_centrality = min(1.0, (cluster_size / max(1, population_size)) + (cluster_cohesion * 0.35))

    archetype_quality = str(archetype.get("quality") or "unassigned")
    archetype_score = archetype_representativeness(archetype_quality, cluster_size, population_size)

    common_feature_score = feature_influence_score(record, feature_frequencies, population_size)
    reach_score = min(1.0, neighbor_centrality + common_feature_score * 0.45)

    impact_score = (
        neighbor_centrality * 0.30
        + cluster_centrality * 0.20
        + archetype_score * 0.20
        + common_feature_score * 0.20
        + reach_score * 0.10
    )

    return {
        "profile_key": profile_key,
        "impact_score": round(impact_score, 6),
        "impact_label": impact_label(impact_score),
        "neighbor_centrality": round(neighbor_centrality, 6),
        "inbound_neighbor_count": inbound_neighbor_count,
        "cluster_centrality": round(cluster_centrality, 6),
        "cluster_id": cluster.get("cluster_id"),
        "cluster_size": cluster_size,
        "cluster_cohesion": round(cluster_cohesion, 6),
        "archetype_score": round(archetype_score, 6),
        "archetype_id": archetype.get("archetype_id"),
        "archetype_name": archetype.get("archetype_name"),
        "archetype_quality": archetype_quality,
        "feature_influence": round(common_feature_score, 6),
        "population_reach": round(reach_score, 6),
        "representative_features": representative_features(record, feature_frequencies, population_size),
        "reasoning": build_impact_reasoning(
            profile_key,
            impact_score,
            inbound_neighbor_count,
            cluster_size,
            archetype_quality,
        ),
    }


def build_inbound_neighbor_counts(neighbor_reports: dict[str, Any]) -> dict[str, int]:
    """Count how often each profile appears as another profile's neighbor."""
    counts: dict[str, int] = {}

    reports = neighbor_reports.get("reports", {}) or {}

    for report in reports.values():
        for neighbor in report.get("neighbors", []) or []:
            key = neighbor.get("profile_key")
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1

    return counts


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


def build_feature_frequencies(records: list[dict[str, Any]]) -> dict[str, int]:
    """Build active vector feature frequencies."""
    frequencies: dict[str, int] = {}

    for record in records:
        for feature in active_vector_features(record):
            frequencies[feature] = frequencies.get(feature, 0) + 1

    return frequencies


def active_vector_features(record: dict[str, Any]) -> list[str]:
    """Return active non-zero vector features."""
    vector = record.get("vector", {}) or {}

    features = []

    for feature, value in vector.items():
        try:
            numeric = float(value)
        except Exception:
            numeric = 0.0

        if numeric != 0.0:
            features.append(feature)

    return features


def feature_influence_score(
    record: dict[str, Any],
    feature_frequencies: dict[str, int],
    population_size: int,
) -> float:
    """Score how much a profile carries population-common features."""
    features = active_vector_features(record)

    if not features:
        return 0.0

    scores = []

    for feature in features:
        frequency = feature_frequencies.get(feature, 0) / max(1, population_size)
        scores.append(frequency)

    return min(1.0, sum(scores) / len(scores))


def representative_features(
    record: dict[str, Any],
    feature_frequencies: dict[str, int],
    population_size: int,
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Return profile features that most strongly represent the population."""
    rows = []

    for feature in active_vector_features(record):
        count = feature_frequencies.get(feature, 0)
        frequency = count / max(1, population_size)

        rows.append(
            {
                "feature": feature,
                "count": count,
                "frequency": round(frequency, 6),
            }
        )

    return sorted(rows, key=lambda item: (-item["frequency"], item["feature"]))[:limit]


def archetype_representativeness(
    quality: str,
    cluster_size: int,
    population_size: int,
) -> float:
    """Score archetype representativeness."""
    base = {
        "strong_archetype": 0.95,
        "emerging_archetype": 0.72,
        "loose_archetype": 0.45,
        "single_case_archetype": 0.20,
        "unassigned": 0.10,
    }.get(quality, 0.10)

    size_bonus = min(0.20, cluster_size / max(1, population_size))

    return min(1.0, base + size_bonus)


def impact_label(score: float) -> str:
    """Label impact score."""
    if score >= 0.78:
        return "high_structural_influence"

    if score >= 0.60:
        return "moderate_structural_influence"

    if score >= 0.42:
        return "localized_structural_influence"

    if score >= 0.25:
        return "low_structural_influence"

    return "minimal_structural_influence"


def build_impact_reasoning(
    profile_key: str,
    impact_score: float,
    inbound_neighbor_count: int,
    cluster_size: int,
    archetype_quality: str,
) -> str:
    """Build human-readable impact reasoning."""
    return (
        f"{profile_key} receives an impact score of {impact_score:.3f}. "
        f"It appears as a neighbor for {inbound_neighbor_count} profile(s), "
        f"belongs to a cluster of size {cluster_size}, and has archetype quality "
        f"{archetype_quality}."
    )


def build_impact_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build structural impact summary."""
    if not rows:
        return {
            "high_impact_count": 0,
            "top_impact_profiles": [],
            "mean_impact_score": 0.0,
        }

    return {
        "high_impact_count": count_label(rows, "high_structural_influence"),
        "moderate_impact_count": count_label(rows, "moderate_structural_influence"),
        "localized_impact_count": count_label(rows, "localized_structural_influence"),
        "low_impact_count": count_label(rows, "low_structural_influence"),
        "minimal_impact_count": count_label(rows, "minimal_structural_influence"),
        "mean_impact_score": round(
            sum(float(row.get("impact_score") or 0.0) for row in rows) / len(rows),
            6,
        ),
        "top_impact_profiles": rows[:20],
    }


def count_label(rows: list[dict[str, Any]], label: str) -> int:
    """Count impact labels."""
    return sum(1 for row in rows if row.get("impact_label") == label)
