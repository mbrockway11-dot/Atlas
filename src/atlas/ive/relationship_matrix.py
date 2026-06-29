"""Identity Vector planet relationship matrix."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any

from atlas.ive.composite import PLANET_ORDER
from atlas.ive.schema import IVE_VERSION, VECTOR_FEATURES, IdentityVector


@dataclass(frozen=True)
class PlanetRelationshipMatrix:
    """Pairwise relationship matrix between composite planet vectors."""

    version: str
    name: str
    planets: list[str]
    similarity: dict[str, dict[str, float]]
    distance: dict[str, dict[str, float]]
    agreement: dict[str, dict[str, float]]
    diagnostics: dict[str, Any]


def build_planet_relationship_matrix(
    identity_vector: IdentityVector,
) -> PlanetRelationshipMatrix:
    """Build planet-to-planet relationship matrix."""
    planets = [
        planet
        for planet in PLANET_ORDER
        if planet in identity_vector.planets
    ]

    similarity = {}
    distance = {}
    agreement = {}

    for planet_a in planets:
        similarity[planet_a] = {}
        distance[planet_a] = {}
        agreement[planet_a] = {}

        vector_a = identity_vector.planets[planet_a].features

        for planet_b in planets:
            vector_b = identity_vector.planets[planet_b].features

            similarity_value = cosine_similarity(vector_a, vector_b)
            distance_value = euclidean_distance(vector_a, vector_b)
            agreement_value = feature_agreement(vector_a, vector_b)

            similarity[planet_a][planet_b] = similarity_value
            distance[planet_a][planet_b] = distance_value
            agreement[planet_a][planet_b] = agreement_value

    diagnostics = build_relationship_diagnostics(
        planets=planets,
        similarity=similarity,
        distance=distance,
        agreement=agreement,
    )

    return PlanetRelationshipMatrix(
        version=IVE_VERSION,
        name=identity_vector.name,
        planets=planets,
        similarity=similarity,
        distance=distance,
        agreement=agreement,
        diagnostics=diagnostics,
    )


def cosine_similarity(
    features_a: dict[str, float],
    features_b: dict[str, float],
) -> float:
    """Compute bounded cosine similarity between two feature dictionaries."""
    values_a = [
        float(features_a.get(feature, 0.0))
        for feature in VECTOR_FEATURES
    ]
    values_b = [
        float(features_b.get(feature, 0.0))
        for feature in VECTOR_FEATURES
    ]

    dot = sum(a * b for a, b in zip(values_a, values_b))
    norm_a = sqrt(sum(a * a for a in values_a))
    norm_b = sqrt(sum(b * b for b in values_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return clamp(dot / (norm_a * norm_b))


def euclidean_distance(
    features_a: dict[str, float],
    features_b: dict[str, float],
) -> float:
    """Compute normalized Euclidean distance between two feature dictionaries."""
    squared = sum(
        (
            float(features_a.get(feature, 0.0))
            - float(features_b.get(feature, 0.0))
        )
        ** 2
        for feature in VECTOR_FEATURES
    )

    max_distance = sqrt(len(VECTOR_FEATURES))

    if max_distance == 0:
        return 0.0

    return clamp(sqrt(squared) / max_distance)


def feature_agreement(
    features_a: dict[str, float],
    features_b: dict[str, float],
) -> float:
    """Compute mean feature agreement as 1 - absolute difference."""
    agreements = [
        1.0
        - abs(
            float(features_a.get(feature, 0.0))
            - float(features_b.get(feature, 0.0))
        )
        for feature in VECTOR_FEATURES
    ]

    if not agreements:
        return 0.0

    return clamp(sum(agreements) / len(agreements))


def build_relationship_diagnostics(
    *,
    planets: list[str],
    similarity: dict[str, dict[str, float]],
    distance: dict[str, dict[str, float]],
    agreement: dict[str, dict[str, float]],
) -> dict[str, Any]:
    """Build diagnostics for a relationship matrix."""
    pair_records = []

    for index_a, planet_a in enumerate(planets):
        for planet_b in planets[index_a + 1:]:
            pair_records.append(
                {
                    "planet_a": planet_a,
                    "planet_b": planet_b,
                    "similarity": similarity[planet_a][planet_b],
                    "distance": distance[planet_a][planet_b],
                    "agreement": agreement[planet_a][planet_b],
                }
            )

    if not pair_records:
        return {
            "pair_count": 0,
            "mean_similarity": 0.0,
            "mean_distance": 0.0,
            "mean_agreement": 0.0,
            "strongest_pair": None,
            "weakest_pair": None,
            "most_divergent_pair": None,
        }

    strongest_pair = max(
        pair_records,
        key=lambda record: record["similarity"],
    )
    weakest_pair = min(
        pair_records,
        key=lambda record: record["similarity"],
    )
    most_divergent_pair = max(
        pair_records,
        key=lambda record: record["distance"],
    )

    return {
        "pair_count": len(pair_records),
        "mean_similarity": average([record["similarity"] for record in pair_records]),
        "mean_distance": average([record["distance"] for record in pair_records]),
        "mean_agreement": average([record["agreement"] for record in pair_records]),
        "strongest_pair": strongest_pair,
        "weakest_pair": weakest_pair,
        "most_divergent_pair": most_divergent_pair,
    }


def relationship_matrix_to_dict(
    matrix: PlanetRelationshipMatrix,
) -> dict[str, Any]:
    """Convert relationship matrix to JSON-safe dictionary."""
    return asdict(matrix)


def validate_relationship_matrix(
    matrix: PlanetRelationshipMatrix,
) -> bool:
    """Validate relationship matrix shape and bounds."""
    if matrix.version != IVE_VERSION:
        return False

    if len(matrix.planets) != 7:
        return False

    for table_name in ["similarity", "distance", "agreement"]:
        table = getattr(matrix, table_name)

        for planet_a in matrix.planets:
            if planet_a not in table:
                return False

            for planet_b in matrix.planets:
                if planet_b not in table[planet_a]:
                    return False

                value = table[planet_a][planet_b]

                if not isinstance(value, int | float):
                    return False

                if value < 0.0 or value > 1.0:
                    return False

    return True


def average(values: list[float]) -> float:
    """Average values safely."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, float(value)))