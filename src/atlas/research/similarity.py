"""Research similarity helpers."""

from math import sqrt
from typing import Any


def cosine_similarity(
    vector_a: dict[str, float],
    vector_b: dict[str, float],
) -> float:
    """Calculate cosine similarity between sparse dictionaries."""
    keys = set(vector_a) | set(vector_b)

    if not keys:
        return 0.0

    dot = sum(vector_a.get(key, 0.0) * vector_b.get(key, 0.0) for key in keys)
    mag_a = sqrt(sum(vector_a.get(key, 0.0) ** 2 for key in keys))
    mag_b = sqrt(sum(vector_b.get(key, 0.0) ** 2 for key in keys))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


def absolute_distance(
    vector_a: dict[str, float],
    vector_b: dict[str, float],
) -> dict[str, float]:
    """Return absolute difference by key."""
    keys = set(vector_a) | set(vector_b)

    return {
        key: abs(vector_a.get(key, 0.0) - vector_b.get(key, 0.0))
        for key in sorted(keys)
    }


def mean_absolute_distance(
    vector_a: dict[str, float],
    vector_b: dict[str, float],
) -> float:
    """Return mean absolute distance."""
    distances = absolute_distance(vector_a, vector_b)

    if not distances:
        return 0.0

    return sum(distances.values()) / len(distances)


def similarity_from_distance(distance: float) -> float:
    """Convert distance to bounded similarity."""
    return max(0.0, min(1.0, 1.0 - distance))


def extract_subtype_vector(acf: dict[str, Any]) -> dict[str, float]:
    """Extract invariant subtype score vector from ACF."""
    return acf["invariant_analysis"]["subtype"]["scores"]


def extract_planetary_vector(acf: dict[str, Any]) -> dict[str, float]:
    """Extract invariant planetary weight vector from ACF."""
    return acf["invariant_analysis"]["planetary_weights"]


def extract_essence_function_vector(acf: dict[str, Any]) -> dict[str, float]:
    """Extract essence function vector from ACF."""
    function = acf["essence"]["classification"]["function"]

    return {
        "driver": function["driver"],
        "amplifier": function["amplifier"],
        "regulator": function["regulator"],
    }