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
    """One planet-level structural comparison row."""

    planet: str
    similarity: float
    distance: float
    confidence: float
    strongest_matches: list[str]
    strongest_differences: list[str]
    feature_distances: dict[str, float]


@dataclass(frozen=True)
class PlanetAgreementMatrix:
    """Planet-by-planet agreement summary."""

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
    return str(value).strip().lower()


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
        _normalize_planet_key(planet): float(value)
        for planet, value in confidence.items()
    }


def _distance_similarity(
    a: Mapping[str, float],
    b: Mapping[str, float],
) -> float:
    """Return bounded similarity from normalized Euclidean distance.

    Planet fingerprints are expected to contain bounded, non-negative
    measurements. Distance-based similarity is less forgiving than raw cosine
    similarity for vectors that all occupy the positive measurement space.
    """

    shared = sorted(set(a) & set(b))

    if not shared:
        return 0.0

    squared_distance = sum(
        (float(a[feature]) - float(b[feature])) ** 2
        for feature in shared
    )

    normalized_distance = (
        squared_distance ** 0.5
    ) / (len(shared) ** 0.5)

    return _clamp_01(1.0 - normalized_distance)


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


def _rank_features_by_distance(
    distances: Mapping[str, float],
    *,
    reverse: bool,
    top_n: int,
) -> list[str]:
    return [
        feature
        for feature, _distance in sorted(
            distances.items(),
            key=lambda item: (item[1], item[0]),
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
    """Compare two fingerprints planet by planet.

    Planet names are normalized case-insensitively.
    Missing planets receive zero similarity and retain their confidence score.
    """

    if top_n_features < 1:
        raise ValueError("top_n_features must be at least 1.")

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

        similarity = _distance_similarity(features_a, features_b)
        distance = 1.0 - similarity

        confidence = mean(
            (
                _clamp_01(normalized_confidence_a.get(planet, 1.0)),
                _clamp_01(normalized_confidence_b.get(planet, 1.0)),
            )
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

    overall_similarity = mean(similarities) if similarities else 0.0
    planet_variance = pstdev(similarities) if len(similarities) > 1 else 0.0
    planet_agreement = 1.0 - planet_variance

    dominant_match = max(
        PLANETS,
        key=lambda planet: planet_similarity[planet],
    )

    dominant_divergence = min(
        PLANETS,
        key=lambda planet: planet_similarity[planet],
    )

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
