"""Planet-level agreement matrix for Atlas identity comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Mapping


PLANETS: tuple[str, ...] = (
    "saturn",
    "jupiter",
    "mars",
    "sun",
    "venus",
    "mercury",
    "moon",
)


@dataclass(frozen=True)
class PlanetAgreementRow:
    planet: str
    similarity: float
    distance: float
    confidence: float
    strongest_matches: list[str]
    strongest_differences: list[str]
    feature_distances: dict[str, float]


@dataclass(frozen=True)
class PlanetAgreementMatrix:
    overall_similarity: float
    planet_similarity: dict[str, float]
    planet_confidence: dict[str, float]
    planet_variance: float
    planet_agreement: float
    dominant_match: str
    dominant_divergence: str
    rows: list[PlanetAgreementRow]


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_planet_key(value: str) -> str:
    return value.strip().lower()


def _normalize_fingerprint(
    fingerprint: Mapping[str, Mapping[str, float]],
) -> dict[str, Mapping[str, float]]:
    return {
        _normalize_planet_key(planet): features
        for planet, features in fingerprint.items()
    }


def _normalize_confidence(
    confidence: Mapping[str, float],
) -> dict[str, float]:
    return {
        _normalize_planet_key(planet): value
        for planet, value in confidence.items()
    }



    shared = sorted(set(a) & set(b))

    if not shared:
        return 0.0

    dot = sum(float(a[k]) * float(b[k]) for k in shared)
    mag_a = sum(float(a[k]) ** 2 for k in shared) ** 0.5
    mag_b = sum(float(b[k]) ** 2 for k in shared) ** 0.5

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    raw = dot / (mag_a * mag_b)
    return _clamp_01((raw + 1.0) / 2.0)


def _feature_distances(
    a: Mapping[str, float],
    b: Mapping[str, float],
) -> dict[str, float]:
    """Return absolute feature-level distances for shared features."""
    shared = sorted(set(a) & set(b))

    return {
        feature: abs(float(a[feature]) - float(b[feature]))
        for feature in shared
    }
def _cosine_similarity(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """Return distance-based similarity for bounded feature vectors.

    Atlas feature vectors are non-negative normalized measurements. Pure cosine
    similarity is too forgiving for this space because unrelated all-positive
    vectors can still point in a similar direction. For planet agreement, we use
    normalized Euclidean distance and convert it to similarity.

    A result of 1.0 means identical shared features.
    A result near 0.0 means maximally separated shared features.
    """
    shared = sorted(set(a) & set(b))

    if not shared:
        return 0.0

    squared = sum(
        (float(a[key]) - float(b[key])) ** 2
        for key in shared
    )

    distance = (squared ** 0.5) / (len(shared) ** 0.5)

    return _clamp_01(1.0 - distance)


def _rank_features_by_distance(
    distances: Mapping[str, float],
    *,
    reverse: bool,
    top_n: int,
) -> list[str]:
    return [
        feature
        for feature, _ in sorted(
            distances.items(),
            key=lambda item: item[1],
            reverse=reverse,
        )[:top_n]
    ]


def compare_planet_agreement(
    fingerprint_a: Mapping[str, Mapping[str, float]],
    fingerprint_b: Mapping[str, Mapping[str, float]],
    confidence_a: Mapping[str, float] | None = None,
    confidence_b: Mapping[str, float] | None = None,
    top_n_features: int = 3,
) -> PlanetAgreementMatrix:
    """Compare two fingerprints planet-by-planet.

    Planet names are normalized case-insensitively, so both ``Saturn`` and
    ``saturn`` resolve to the same canonical planet.
    """

    normalized_a = _normalize_fingerprint(fingerprint_a)
    normalized_b = _normalize_fingerprint(fingerprint_b)

    normalized_confidence_a = _normalize_confidence(confidence_a or {})
    normalized_confidence_b = _normalize_confidence(confidence_b or {})

    rows: list[PlanetAgreementRow] = []
    planet_similarity: dict[str, float] = {}
    planet_confidence: dict[str, float] = {}

    for planet in PLANETS:
        features_a = normalized_a.get(planet, {})
        features_b = normalized_b.get(planet, {})

        similarity = _cosine_similarity(features_a, features_b)
        distance = 1.0 - similarity

        confidence = mean(
            [
                _clamp_01(normalized_confidence_a.get(planet, 1.0)),
                _clamp_01(normalized_confidence_b.get(planet, 1.0)),
            ]
        )

        distances = _feature_distances(features_a, features_b)

        strongest_matches = _rank_features_by_distance(
            distances,
            reverse=False,
            top_n=top_n_features,
        )

        strongest_differences = _rank_features_by_distance(
            distances,
            reverse=True,
            top_n=top_n_features,
        )

        planet_similarity[planet] = similarity
        planet_confidence[planet] = confidence

        rows.append(
            PlanetAgreementRow(
                planet=planet,
                similarity=similarity,
                distance=distance,
                confidence=confidence,
                strongest_matches=strongest_matches,
                strongest_differences=strongest_differences,
                feature_distances=distances,
            )
        )

    similarities = list(planet_similarity.values())

    overall_similarity = mean(similarities)
    planet_variance = pstdev(similarities) if len(similarities) > 1 else 0.0
    planet_agreement = 1.0 - planet_variance

    dominant_match = max(planet_similarity, key=planet_similarity.get)
    dominant_divergence = min(planet_similarity, key=planet_similarity.get)

    return PlanetAgreementMatrix(
        overall_similarity=_clamp_01(overall_similarity),
        planet_similarity=planet_similarity,
        planet_confidence=planet_confidence,
        planet_variance=_clamp_01(planet_variance),
        planet_agreement=_clamp_01(planet_agreement),
        dominant_match=dominant_match,
        dominant_divergence=dominant_divergence,
        rows=rows,
    )