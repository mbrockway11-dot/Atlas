
"""Population Intelligence v4 structural similarity engine."""

from __future__ import annotations

import math
from typing import Any


SIMILARITY_VERSION = "4.0.0"


DEFAULT_WEIGHTS = {
    "architecture": 0.18,
    "system_class": 0.14,
    "themes": 0.22,
    "inferences": 0.18,
    "tensions": 0.08,
    "evidence_engines": 0.08,
    "vector": 0.12,
}


def compare_population_records(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compare two Population v4 feature records."""
    active_weights = weights or DEFAULT_WEIGHTS

    component_scores = {
        "architecture": exact_match_score(
            nested(left, ["summary", "primary_architecture"]),
            nested(right, ["summary", "primary_architecture"]),
        ),
        "system_class": exact_match_score(
            nested(left, ["summary", "system_class"]),
            nested(right, ["summary", "system_class"]),
        ),
        "themes": jaccard_score(
            set(left.get("themes", []) or []),
            set(right.get("themes", []) or []),
        ),
        "inferences": jaccard_score(
            set(left.get("inferences", []) or []),
            set(right.get("inferences", []) or []),
        ),
        "tensions": jaccard_score(
            set(left.get("tensions", []) or []),
            set(right.get("tensions", []) or []),
            empty_score=0.5,
        ),
        "evidence_engines": jaccard_score(
            set(nested(left, ["evidence", "engines"]) or []),
            set(nested(right, ["evidence", "engines"]) or []),
        ),
        "vector": cosine_similarity(
            left.get("vector", {}) or {},
            right.get("vector", {}) or {},
        ),
    }

    total_weight = sum(active_weights.values()) or 1.0
    similarity = sum(
        component_scores.get(component, 0.0) * weight
        for component, weight in active_weights.items()
    ) / total_weight

    return {
        "version": SIMILARITY_VERSION,
        "left_profile_key": left.get("profile_key"),
        "right_profile_key": right.get("profile_key"),
        "similarity": round(similarity, 6),
        "distance": round(1.0 - similarity, 6),
        "label": similarity_label(similarity),
        "component_scores": {
            key: round(value, 6)
            for key, value in component_scores.items()
        },
        "shared": shared_features(left, right),
        "differences": difference_features(left, right),
    }


def build_similarity_matrix(
    corpus: dict[str, Any],
    *,
    limit: int | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build pairwise similarity matrix for a Population v4 corpus."""
    records = corpus.get("records", []) or []

    if limit is not None:
        records = records[:limit]

    comparisons = []

    for left_index, left in enumerate(records):
        for right_index, right in enumerate(records):
            if right_index <= left_index:
                continue

            comparisons.append(
                compare_population_records(
                    left,
                    right,
                    weights=weights,
                )
            )

    return {
        "success": True,
        "version": SIMILARITY_VERSION,
        "profile_count": len(records),
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "summary": build_similarity_summary(comparisons),
    }


def find_structural_neighbors(
    corpus: dict[str, Any],
    profile_key: str,
    *,
    limit: int = 10,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Find nearest structural neighbors for one profile."""
    records = corpus.get("records", []) or []
    target = next(
        (record for record in records if record.get("profile_key") == profile_key),
        None,
    )

    if not target:
        return {
            "success": False,
            "profile_key": profile_key,
            "neighbors": [],
            "errors": [f"Profile not found in corpus: {profile_key}"],
        }

    neighbors = []

    for record in records:
        if record.get("profile_key") == profile_key:
            continue

        neighbors.append(
            compare_population_records(
                target,
                record,
                weights=weights,
            )
        )

    neighbors.sort(key=lambda item: item.get("similarity", 0.0), reverse=True)

    return {
        "success": True,
        "version": SIMILARITY_VERSION,
        "profile_key": profile_key,
        "neighbor_count": len(neighbors),
        "neighbors": neighbors[:limit],
    }


def build_similarity_summary(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    """Build summary for similarity comparisons."""
    if not comparisons:
        return {
            "mean_similarity": 0.0,
            "max_similarity": 0.0,
            "min_similarity": 0.0,
            "strong_pair_count": 0,
        }

    values = [float(item.get("similarity") or 0.0) for item in comparisons]

    strongest = max(comparisons, key=lambda item: item.get("similarity", 0.0))
    weakest = min(comparisons, key=lambda item: item.get("similarity", 0.0))

    return {
        "mean_similarity": round(sum(values) / len(values), 6),
        "max_similarity": round(max(values), 6),
        "min_similarity": round(min(values), 6),
        "strong_pair_count": sum(1 for value in values if value >= 0.70),
        "strongest_pair": pair_summary(strongest),
        "weakest_pair": pair_summary(weakest),
    }


def pair_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    """Build compact pair summary."""
    return {
        "left_profile_key": comparison.get("left_profile_key"),
        "right_profile_key": comparison.get("right_profile_key"),
        "similarity": comparison.get("similarity"),
        "label": comparison.get("label"),
    }


def exact_match_score(left: Any, right: Any) -> float:
    """Score exact normalized match."""
    left_label = normalize(left)
    right_label = normalize(right)

    if not left_label or not right_label:
        return 0.0

    return 1.0 if left_label == right_label else 0.0


def jaccard_score(left: set[str], right: set[str], *, empty_score: float = 0.0) -> float:
    """Compute Jaccard score."""
    if not left and not right:
        return empty_score

    return len(left & right) / max(1, len(left | right))


def cosine_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Compute sparse cosine similarity."""
    keys = set(left.keys()) | set(right.keys())

    if not keys:
        return 0.0

    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0

    for key in keys:
        left_value = float_or_zero(left.get(key))
        right_value = float_or_zero(right.get(key))

        dot += left_value * right_value
        left_norm += left_value * left_value
        right_norm += right_value * right_value

    denominator = math.sqrt(left_norm) * math.sqrt(right_norm)

    if denominator == 0.0:
        return 0.0

    return dot / denominator


def shared_features(left: dict[str, Any], right: dict[str, Any]) -> dict[str, list[str]]:
    """Return shared structural features."""
    return {
        "themes": sorted(set(left.get("themes", []) or []) & set(right.get("themes", []) or [])),
        "inferences": sorted(set(left.get("inferences", []) or []) & set(right.get("inferences", []) or [])),
        "tensions": sorted(set(left.get("tensions", []) or []) & set(right.get("tensions", []) or [])),
        "evidence_engines": sorted(
            set(nested(left, ["evidence", "engines"]) or [])
            & set(nested(right, ["evidence", "engines"]) or [])
        ),
        "vector_features": sorted(
            set(active_vector_features(left))
            & set(active_vector_features(right))
        ),
    }


def difference_features(left: dict[str, Any], right: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Return differentiated structural features."""
    return {
        "themes": difference_sets(left.get("themes", []) or [], right.get("themes", []) or []),
        "inferences": difference_sets(left.get("inferences", []) or [], right.get("inferences", []) or []),
        "tensions": difference_sets(left.get("tensions", []) or [], right.get("tensions", []) or []),
        "vector_features": difference_sets(active_vector_features(left), active_vector_features(right)),
    }


def difference_sets(left: list[str], right: list[str]) -> dict[str, list[str]]:
    """Return left/right unique features."""
    left_set = set(left)
    right_set = set(right)

    return {
        "left_unique": sorted(left_set - right_set),
        "right_unique": sorted(right_set - left_set),
    }


def active_vector_features(record: dict[str, Any]) -> list[str]:
    """Return active vector feature names."""
    vector = record.get("vector", {}) or {}

    return [
        feature
        for feature, value in vector.items()
        if float_or_zero(value) != 0.0
    ]


def similarity_label(value: float) -> str:
    """Label similarity score."""
    if value >= 0.82:
        return "very_high_similarity"

    if value >= 0.68:
        return "high_similarity"

    if value >= 0.50:
        return "moderate_similarity"

    if value >= 0.32:
        return "low_similarity"

    return "distinct"


def nested(source: dict[str, Any], path: list[str]) -> Any:
    """Read nested value."""
    value: Any = source

    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)

    return value


def normalize(value: Any) -> str:
    """Normalize label."""
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def float_or_zero(value: Any) -> float:
    """Convert to float or zero."""
    try:
        return float(value)
    except Exception:
        return 0.0
