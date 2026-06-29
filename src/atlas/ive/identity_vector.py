"""Identity Vector builder."""

from __future__ import annotations

from statistics import mean, pvariance
from typing import Any

from atlas.ive.composite import PLANET_ORDER, build_composite_planet_vectors
from atlas.ive.feature_vector import build_planet_feature_vector
from atlas.ive.normalizer import normalize_planet_vectors
from atlas.ive.schema import (
    IDENTITY_GLOBAL_FEATURES,
    IVE_VERSION,
    VECTOR_FEATURES,
    CompositePlanetVector,
    IdentityVector,
)


def build_identity_vector(
    acf: dict[str, Any],
    calibration_acfs: list[dict[str, Any]] | None = None,
    normalization_mode: str = "percentile",
) -> IdentityVector:
    """Build a canonical IdentityVector from an ACF profile."""
    raw_vectors = build_raw_vectors_from_acf(acf)

    calibration_vectors = raw_vectors

    if calibration_acfs:
        calibration_vectors = []

        for calibration_acf in calibration_acfs:
            calibration_vectors.extend(build_raw_vectors_from_acf(calibration_acf))

    normalized_vectors = normalize_planet_vectors(
        vectors=raw_vectors,
        calibration_vectors=calibration_vectors,
        mode=normalization_mode,
    )

    composite_vectors = build_composite_planet_vectors(normalized_vectors)

    planets = {
        vector.planet: vector
        for vector in composite_vectors
    }

    global_features = build_identity_global_features(planets)
    quality = build_identity_quality(planets, normalized_vectors, normalization_mode)
    diagnostics = build_identity_diagnostics(planets, global_features)

    return IdentityVector(
        version=IVE_VERSION,
        name=acf["identity"]["name"],
        planets=planets,
        global_features=global_features,
        quality=quality,
        diagnostics=diagnostics,
    )


def build_raw_vectors_from_acf(
    acf: dict[str, Any],
) -> list:
    """Build raw PlanetFeatureVectors from an ACF profile."""
    return [
        build_planet_feature_vector(
            layer=layer,
            profile_name=acf["identity"]["name"],
        )
        for layer in acf["identity_graph"]["layers"]
    ]


def build_identity_global_features(
    planets: dict[str, CompositePlanetVector],
) -> dict[str, float]:
    """Build identity-level global features from seven planet vectors."""
    planet_vectors = ordered_planet_vectors(planets)

    feature_means = {
        f"mean_{feature}": mean_feature(planet_vectors, feature)
        for feature in VECTOR_FEATURES
    }

    planet_variance = mean(
        [
            feature_variance(planet_vectors, feature)
            for feature in VECTOR_FEATURES
        ]
    )

    global_features = {
        **feature_means,
        "planet_balance_index": clamp(1.0 - planet_variance),
        "planet_variance_index": clamp(planet_variance),
        "structural_complexity_index": average(
            [
                feature_means["mean_entropy"],
                feature_means["mean_node_coverage"],
                feature_means["mean_reduction_entropy"],
                feature_means["mean_articulation_ratio"],
                feature_means["mean_bridge_ratio"],
            ]
        ),
        "structural_stability_index": average(
            [
                feature_means["mean_graph_coherence"],
                feature_means["mean_core_survival_score"],
                feature_means["mean_topology_stability"],
                feature_means["mean_attractor_stability"],
                feature_means["mean_node_survival_auc"],
                feature_means["mean_edge_survival_auc"],
            ]
        ),
    }

    return {
        feature: clamp(global_features.get(feature, 0.0))
        for feature in IDENTITY_GLOBAL_FEATURES
    }


def build_identity_quality(
    planets: dict[str, CompositePlanetVector],
    normalized_vectors: list,
    normalization_mode: str,
) -> dict[str, float | int | str]:
    """Build quality metadata for an IdentityVector."""
    source_counts = [
        planet.source_count
        for planet in planets.values()
    ]

    calibration_sizes = [
        vector.calibration_size
        for vector in normalized_vectors
    ]

    return {
        "planet_count": len(planets),
        "expected_planet_count": 7,
        "completeness": clamp(len(planets) / 7.0),
        "mean_source_count": mean(source_counts) if source_counts else 0.0,
        "expected_source_count": 3,
        "source_completeness": clamp(
            (mean(source_counts) if source_counts else 0.0) / 3.0
        ),
        "normalization_mode": normalization_mode,
        "mean_calibration_size": mean(calibration_sizes) if calibration_sizes else 0.0,
        "minimum_calibration_size": min(calibration_sizes) if calibration_sizes else 0,
    }


def build_identity_diagnostics(
    planets: dict[str, CompositePlanetVector],
    global_features: dict[str, float],
) -> dict[str, Any]:
    """Build identity vector diagnostics."""
    planet_vectors = ordered_planet_vectors(planets)

    coherence_by_planet = {
        vector.planet: vector.features["graph_coherence"]
        for vector in planet_vectors
    }

    stability_by_planet = {
        vector.planet: vector.features["attractor_stability"]
        for vector in planet_vectors
    }

    entropy_by_planet = {
        vector.planet: vector.features["entropy"]
        for vector in planet_vectors
    }

    return {
        "dominant_coherence_planet": max_key(coherence_by_planet),
        "weakest_coherence_planet": min_key(coherence_by_planet),
        "dominant_stability_planet": max_key(stability_by_planet),
        "weakest_stability_planet": min_key(stability_by_planet),
        "dominant_entropy_planet": max_key(entropy_by_planet),
        "weakest_entropy_planet": min_key(entropy_by_planet),
        "identity_balance_index": global_features["planet_balance_index"],
        "identity_complexity_index": global_features[
            "structural_complexity_index"
        ],
        "identity_stability_index": global_features[
            "structural_stability_index"
        ],
    }


def ordered_planet_vectors(
    planets: dict[str, CompositePlanetVector],
) -> list[CompositePlanetVector]:
    """Return planet vectors in canonical planet order."""
    return [
        planets[planet]
        for planet in PLANET_ORDER
        if planet in planets
    ]


def mean_feature(
    vectors: list[CompositePlanetVector],
    feature: str,
) -> float:
    """Average one feature across planet vectors."""
    if not vectors:
        return 0.0

    return mean(
        [
            vector.features[feature]
            for vector in vectors
        ]
    )


def feature_variance(
    vectors: list[CompositePlanetVector],
    feature: str,
) -> float:
    """Population variance for one feature across planets."""
    if len(vectors) < 2:
        return 0.0

    return pvariance(
        [
            vector.features[feature]
            for vector in vectors
        ]
    )


def average(values: list[float]) -> float:
    """Average values safely."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def max_key(values: dict[str, float]) -> str | None:
    """Return key with max value."""
    if not values:
        return None

    return max(values, key=values.get)


def min_key(values: dict[str, float]) -> str | None:
    """Return key with min value."""
    if not values:
        return None

    return min(values, key=values.get)


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, float(value)))