
"""Population Intelligence v4 neighbor engine."""

from __future__ import annotations

from typing import Any

from atlas.population_v4.similarity import compare_population_records


NEIGHBOR_VERSION = "4.0.0"


def find_population_neighbors(
    corpus: dict[str, Any],
    profile_key: str,
    *,
    limit: int = 10,
    min_similarity: float = 0.0,
) -> dict[str, Any]:
    """Find ranked structural neighbors for one profile."""
    records = corpus.get("records", []) or []

    target = next(
        (record for record in records if record.get("profile_key") == profile_key),
        None,
    )

    if not target:
        return {
            "success": False,
            "version": NEIGHBOR_VERSION,
            "profile_key": profile_key,
            "errors": [f"Profile not found in corpus: {profile_key}"],
            "neighbors": [],
        }

    neighbors = []

    for record in records:
        if record.get("profile_key") == profile_key:
            continue

        comparison = compare_population_records(target, record)

        if comparison.get("similarity", 0.0) < min_similarity:
            continue

        neighbors.append(build_neighbor_row(target, record, comparison))

    neighbors.sort(key=lambda item: item.get("similarity", 0.0), reverse=True)

    return {
        "success": True,
        "version": NEIGHBOR_VERSION,
        "profile_key": profile_key,
        "neighbor_count": len(neighbors),
        "neighbors": neighbors[:limit],
        "summary": build_neighbor_summary(profile_key, neighbors[:limit]),
    }


def build_neighbor_row(
    target: dict[str, Any],
    neighbor: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    """Build one neighbor row."""
    return {
        "profile_key": neighbor.get("profile_key"),
        "similarity": comparison.get("similarity"),
        "distance": comparison.get("distance"),
        "label": comparison.get("label"),
        "system_class": nested(neighbor, ["summary", "system_class"]),
        "subtype": nested(neighbor, ["summary", "subtype"]),
        "primary_architecture": nested(neighbor, ["summary", "primary_architecture"]),
        "component_scores": comparison.get("component_scores", {}),
        "shared": comparison.get("shared", {}),
        "differences": comparison.get("differences", {}),
        "why_close": explain_neighbor_similarity(target, neighbor, comparison),
    }


def explain_neighbor_similarity(
    target: dict[str, Any],
    neighbor: dict[str, Any],
    comparison: dict[str, Any],
) -> list[str]:
    """Build human-readable neighbor explanation."""
    shared = comparison.get("shared", {}) or {}
    components = comparison.get("component_scores", {}) or {}

    reasons = []

    if components.get("architecture", 0.0) >= 1.0:
        reasons.append(
            "Shares the same primary architecture."
        )

    if components.get("system_class", 0.0) >= 1.0:
        reasons.append(
            "Shares the same system class."
        )

    if shared.get("themes"):
        reasons.append(
            "Shared themes: "
            + ", ".join(shared.get("themes", [])[:5])
        )

    if shared.get("inferences"):
        reasons.append(
            "Shared inference patterns: "
            + ", ".join(shared.get("inferences", [])[:5])
        )

    if shared.get("vector_features"):
        reasons.append(
            "Shared vector features: "
            + ", ".join(shared.get("vector_features", [])[:5])
        )

    if not reasons:
        reasons.append(
            "Similarity is driven by weaker distributed overlap across the feature vector."
        )

    return reasons


def find_neighbors_for_all(
    corpus: dict[str, Any],
    *,
    limit: int = 5,
    min_similarity: float = 0.0,
) -> dict[str, Any]:
    """Build neighbor reports for every profile in the corpus."""
    records = corpus.get("records", []) or {}
    reports = {}

    for record in records:
        profile_key = record.get("profile_key")
        if not profile_key:
            continue

        reports[profile_key] = find_population_neighbors(
            corpus,
            profile_key,
            limit=limit,
            min_similarity=min_similarity,
        )

    return {
        "success": True,
        "version": NEIGHBOR_VERSION,
        "profile_count": len(reports),
        "reports": reports,
        "summary": build_global_neighbor_summary(reports),
    }


def build_neighbor_summary(profile_key: str, neighbors: list[dict[str, Any]]) -> dict[str, Any]:
    """Build compact neighbor summary."""
    if not neighbors:
        return {
            "profile_key": profile_key,
            "top_neighbor": None,
            "mean_similarity": 0.0,
            "max_similarity": 0.0,
        }

    similarities = [
        float(item.get("similarity") or 0.0)
        for item in neighbors
    ]

    top = neighbors[0]

    return {
        "profile_key": profile_key,
        "top_neighbor": {
            "profile_key": top.get("profile_key"),
            "similarity": top.get("similarity"),
            "label": top.get("label"),
        },
        "mean_similarity": round(sum(similarities) / len(similarities), 6),
        "max_similarity": round(max(similarities), 6),
    }


def build_global_neighbor_summary(reports: dict[str, Any]) -> dict[str, Any]:
    """Build global neighbor summary."""
    top_pairs = []

    for profile_key, report in reports.items():
        summary = report.get("summary", {})
        top = summary.get("top_neighbor")

        if not top:
            continue

        top_pairs.append(
            {
                "profile_key": profile_key,
                "neighbor_key": top.get("profile_key"),
                "similarity": top.get("similarity"),
                "label": top.get("label"),
            }
        )

    top_pairs.sort(key=lambda item: item.get("similarity", 0.0), reverse=True)

    return {
        "top_pair_count": len(top_pairs),
        "strongest_neighbor_pairs": top_pairs[:20],
    }


def nested(source: dict[str, Any], path: list[str]) -> Any:
    """Read nested dictionary value."""
    value: Any = source

    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)

    return value
