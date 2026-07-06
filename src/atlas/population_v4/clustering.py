
"""Population Intelligence v4 hierarchical clustering."""

from __future__ import annotations

from typing import Any

from atlas.population_v4.similarity import compare_population_records


CLUSTERING_VERSION = "4.0.0"


def build_hierarchical_clusters(
    corpus: dict[str, Any],
    *,
    threshold: float = 0.55,
) -> dict[str, Any]:
    """Build deterministic similarity-threshold clusters."""
    records = corpus.get("records", []) or []
    profile_keys = [record.get("profile_key") for record in records if record.get("profile_key")]
    record_map = {record.get("profile_key"): record for record in records if record.get("profile_key")}

    adjacency = {key: set() for key in profile_keys}
    pair_scores = {}

    for left_index, left_key in enumerate(profile_keys):
        for right_key in profile_keys[left_index + 1:]:
            comparison = compare_population_records(record_map[left_key], record_map[right_key])
            similarity = float(comparison.get("similarity") or 0.0)
            pair_scores[(left_key, right_key)] = similarity

            if similarity >= threshold:
                adjacency[left_key].add(right_key)
                adjacency[right_key].add(left_key)

    clusters = connected_components(adjacency)
    cluster_rows = []

    for index, members in enumerate(clusters, start=1):
        cluster_id = f"cluster_{index:03d}"
        cluster_rows.append(
            build_cluster_row(
                cluster_id,
                sorted(members),
                record_map,
                pair_scores,
            )
        )

    cluster_rows.sort(
        key=lambda item: (-item["member_count"], item["cluster_id"])
    )

    return {
        "success": True,
        "version": CLUSTERING_VERSION,
        "threshold": threshold,
        "profile_count": len(profile_keys),
        "cluster_count": len(cluster_rows),
        "clusters": cluster_rows,
        "summary": build_cluster_summary(cluster_rows),
    }


def connected_components(adjacency: dict[str, set[str]]) -> list[list[str]]:
    """Find connected components in deterministic order."""
    visited = set()
    components = []

    for node in sorted(adjacency):
        if node in visited:
            continue

        stack = [node]
        component = []

        while stack:
            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            component.append(current)

            for neighbor in sorted(adjacency.get(current, set()), reverse=True):
                if neighbor not in visited:
                    stack.append(neighbor)

        components.append(sorted(component))

    return components


def build_cluster_row(
    cluster_id: str,
    members: list[str],
    record_map: dict[str, dict[str, Any]],
    pair_scores: dict[tuple[str, str], float],
) -> dict[str, Any]:
    """Build one cluster row."""
    records = [record_map[key] for key in members if key in record_map]

    themes = count_values(
        theme
        for record in records
        for theme in record.get("themes", []) or []
    )

    inferences = count_values(
        inference
        for record in records
        for inference in record.get("inferences", []) or []
    )

    architectures = count_values(
        nested(record, ["summary", "primary_architecture"])
        for record in records
    )

    classes = count_values(
        nested(record, ["summary", "system_class"])
        for record in records
    )

    cohesion = cluster_cohesion(members, pair_scores)

    return {
        "cluster_id": cluster_id,
        "member_count": len(members),
        "members": members,
        "cohesion": cohesion,
        "dominant_system_classes": top_counts(classes),
        "dominant_architectures": top_counts(architectures),
        "dominant_themes": top_counts(themes),
        "dominant_inferences": top_counts(inferences),
        "label": build_cluster_label(classes, architectures, themes),
    }


def cluster_cohesion(
    members: list[str],
    pair_scores: dict[tuple[str, str], float],
) -> float:
    """Compute average internal pair similarity."""
    if len(members) <= 1:
        return 1.0

    scores = []

    for left_index, left in enumerate(members):
        for right in members[left_index + 1:]:
            key = (left, right) if (left, right) in pair_scores else (right, left)
            scores.append(float(pair_scores.get(key, 0.0)))

    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 6)


def build_cluster_summary(clusters: list[dict[str, Any]]) -> dict[str, Any]:
    """Build clustering summary."""
    if not clusters:
        return {
            "largest_cluster_size": 0,
            "singleton_count": 0,
            "mean_cluster_size": 0.0,
            "mean_cohesion": 0.0,
        }

    sizes = [cluster.get("member_count", 0) for cluster in clusters]
    cohesions = [float(cluster.get("cohesion") or 0.0) for cluster in clusters]

    return {
        "largest_cluster_size": max(sizes),
        "singleton_count": sum(1 for size in sizes if size == 1),
        "mean_cluster_size": round(sum(sizes) / len(sizes), 6),
        "mean_cohesion": round(sum(cohesions) / len(cohesions), 6),
        "largest_clusters": clusters[:10],
    }


def build_cluster_label(
    classes: dict[str, int],
    architectures: dict[str, int],
    themes: dict[str, int],
) -> str:
    """Build compact cluster label."""
    architecture = top_label(architectures)
    system_class = top_label(classes)
    theme = top_label(themes)

    parts = [
        item for item in [architecture, system_class, theme]
        if item and item != "unresolved"
    ]

    return " / ".join(parts[:3]) if parts else "Unresolved Cluster"


def count_values(values) -> dict[str, int]:
    """Count normalized values."""
    counts = {}

    for value in values:
        label = normalize(value)

        if not label:
            continue

        counts[label] = counts.get(label, 0) + 1

    return counts


def top_counts(counts: dict[str, int], *, limit: int = 10) -> list[dict[str, Any]]:
    """Return top count rows."""
    rows = [
        {"label": label, "count": count}
        for label, count in counts.items()
    ]

    return sorted(rows, key=lambda item: (-item["count"], item["label"]))[:limit]


def top_label(counts: dict[str, int]) -> str:
    """Return highest count label."""
    rows = top_counts(counts, limit=1)
    return rows[0]["label"] if rows else ""


def nested(source: dict[str, Any], path: list[str]) -> Any:
    """Read nested dict path."""
    value: Any = source

    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)

    return value


def normalize(value: Any) -> str:
    """Normalize labels."""
    label = (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    if label in {"", "none", "null", "unknown"}:
        return ""

    return label
