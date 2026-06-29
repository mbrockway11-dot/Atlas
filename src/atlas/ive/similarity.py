"""Identity Vector similarity engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any

from atlas.ive.composite import PLANET_ORDER
from atlas.ive.relationship_matrix import (
    build_planet_relationship_matrix,
    cosine_similarity,
    euclidean_distance,
    feature_agreement,
)
from atlas.ive.schema import IVE_VERSION, VECTOR_FEATURES, IdentityVector


@dataclass(frozen=True)
class IdentityVectorSimilarity:
    """Similarity comparison between two IdentityVectors."""

    version: str
    name_a: str
    name_b: str
    global_similarity: float
    global_distance: float
    planet_similarity: dict[str, float]
    planet_distance: dict[str, float]
    planet_agreement: dict[str, float]
    relationship_similarity: float
    composite_similarity: float
    diagnostics: dict[str, Any]


def compare_identity_vectors(
    vector_a: IdentityVector,
    vector_b: IdentityVector,
) -> IdentityVectorSimilarity:
    """Compare two IdentityVectors."""
    global_similarity = cosine_similarity(
        vector_a.global_features,
        vector_b.global_features,
    )
    global_distance = global_feature_distance(vector_a, vector_b)

    planet_similarity = {}
    planet_distance = {}
    planet_agreement = {}

    for planet in PLANET_ORDER:
        if planet not in vector_a.planets or planet not in vector_b.planets:
            continue

        features_a = vector_a.planets[planet].features
        features_b = vector_b.planets[planet].features

        planet_similarity[planet] = cosine_similarity(features_a, features_b)
        planet_distance[planet] = euclidean_distance(features_a, features_b)
        planet_agreement[planet] = feature_agreement(features_a, features_b)

    relationship_similarity = compare_relationships(vector_a, vector_b)

    composite_similarity = average(
        [
            global_similarity,
            average(list(planet_similarity.values())),
            average(list(planet_agreement.values())),
            relationship_similarity,
            1.0 - global_distance,
        ]
    )

    diagnostics = {
        "strongest_planet_match": max_key(planet_similarity),
        "weakest_planet_match": min_key(planet_similarity),
        "most_divergent_planet": max_key(planet_distance),
        "shared_planet_count": len(planet_similarity),
        "global_similarity": global_similarity,
        "relationship_similarity": relationship_similarity,
    }

    return IdentityVectorSimilarity(
        version=IVE_VERSION,
        name_a=vector_a.name,
        name_b=vector_b.name,
        global_similarity=global_similarity,
        global_distance=global_distance,
        planet_similarity=planet_similarity,
        planet_distance=planet_distance,
        planet_agreement=planet_agreement,
        relationship_similarity=relationship_similarity,
        composite_similarity=clamp(composite_similarity),
        diagnostics=diagnostics,
    )


def compare_relationships(
    vector_a: IdentityVector,
    vector_b: IdentityVector,
) -> float:
    """Compare relationship matrices between two IdentityVectors."""
    matrix_a = build_planet_relationship_matrix(vector_a)
    matrix_b = build_planet_relationship_matrix(vector_b)

    values_a = []
    values_b = []

    for planet_a in PLANET_ORDER:
        for planet_b in PLANET_ORDER:
            if planet_a == planet_b:
                continue

            if (
                planet_a in matrix_a.similarity
                and planet_b in matrix_a.similarity[planet_a]
                and planet_a in matrix_b.similarity
                and planet_b in matrix_b.similarity[planet_a]
            ):
                values_a.append(matrix_a.similarity[planet_a][planet_b])
                values_b.append(matrix_b.similarity[planet_a][planet_b])

    if not values_a or not values_b:
        return 0.0

    return cosine_similarity_from_lists(values_a, values_b)


def global_feature_distance(
    vector_a: IdentityVector,
    vector_b: IdentityVector,
) -> float:
    """Compute normalized global-feature distance."""
    features = sorted(
        set(vector_a.global_features)
        & set(vector_b.global_features)
    )

    if not features:
        return 0.0

    squared = sum(
        (
            float(vector_a.global_features[feature])
            - float(vector_b.global_features[feature])
        )
        ** 2
        for feature in features
    )

    return clamp(sqrt(squared) / sqrt(len(features)))


def cosine_similarity_from_lists(
    values_a: list[float],
    values_b: list[float],
) -> float:
    """Compute cosine similarity from numeric lists."""
    if len(values_a) != len(values_b):
        raise ValueError("Similarity lists must have the same length.")

    dot = sum(a * b for a, b in zip(values_a, values_b))
    norm_a = sqrt(sum(a * a for a in values_a))
    norm_b = sqrt(sum(b * b for b in values_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return clamp(dot / (norm_a * norm_b))


def identity_similarity_to_dict(
    similarity: IdentityVectorSimilarity,
) -> dict[str, Any]:
    """Convert similarity result to JSON-safe dictionary."""
    return asdict(similarity)


def validate_identity_similarity(
    similarity: IdentityVectorSimilarity,
) -> bool:
    """Validate similarity result."""
    if similarity.version != IVE_VERSION:
        return False

    bounded = [
        similarity.global_similarity,
        similarity.global_distance,
        similarity.relationship_similarity,
        similarity.composite_similarity,
        *similarity.planet_similarity.values(),
        *similarity.planet_distance.values(),
        *similarity.planet_agreement.values(),
    ]

    return all(0.0 <= value <= 1.0 for value in bounded)


def average(values: list[float]) -> float:
    """Average values safely."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def max_key(values: dict[str, float]) -> str | None:
    """Return max key."""
    if not values:
        return None

    return max(values, key=values.get)


def min_key(values: dict[str, float]) -> str | None:
    """Return min key."""
    if not values:
        return None

    return min(values, key=values.get)


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, float(value)))