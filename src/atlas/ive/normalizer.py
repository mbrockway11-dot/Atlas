"""Planet vector normalization.

The normalizer converts raw bounded PlanetFeatureVector records into
population-normalized vectors.

Normalization happens within a comparable measurement group. By default that
group is cipher x planet, so Saturn/ordinal is compared to other Saturn/ordinal
vectors instead of being compared directly to Moon/ordinal raw values.
"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from atlas.ive.schema import (
    IVE_VERSION,
    VECTOR_FEATURES,
    NormalizedPlanetVector,
    PlanetFeatureVector,
)


DEFAULT_NORMALIZATION_MODE = "percentile"

# Version of the normalization implementation. Bump this whenever the
# numerical behaviour of any mode changes (formula, clamping, tie handling),
# even if no schema field moves. It feeds the feature-schema hash so that a
# purely algorithmic change still invalidates derived artifacts.
NORMALIZATION_VERSION = "1.0.0"

# The population modes this implementation supports, in a stable order. Part
# of the schema identity: adding or removing a mode changes it.
NORMALIZATION_MODES = ("raw", "percentile", "minmax", "zscore")


def normalize_planet_vector(
    vector: PlanetFeatureVector,
    calibration_vectors: list[PlanetFeatureVector],
    mode: str = DEFAULT_NORMALIZATION_MODE,
) -> NormalizedPlanetVector:
    """Normalize one planet vector against comparable calibration vectors."""
    comparable = comparable_vectors(vector, calibration_vectors)

    if not comparable:
        comparable = [vector]

    normalized_features = {
        feature: normalize_feature_value(
            value=vector.features[feature],
            feature=feature,
            calibration_vectors=comparable,
            mode=mode,
        )
        for feature in VECTOR_FEATURES
    }

    return NormalizedPlanetVector(
        version=IVE_VERSION,
        name=vector.name,
        cipher=vector.cipher,
        planet=vector.planet,
        kamea=vector.kamea,
        grid_size=vector.grid_size,
        features=normalized_features,
        raw_features=dict(vector.features),
        normalization_mode=mode,
        calibration_size=len(comparable),
    )


def normalize_planet_vectors(
    vectors: list[PlanetFeatureVector],
    calibration_vectors: list[PlanetFeatureVector] | None = None,
    mode: str = DEFAULT_NORMALIZATION_MODE,
) -> list[NormalizedPlanetVector]:
    """Normalize a list of vectors."""
    calibration = calibration_vectors if calibration_vectors is not None else vectors

    return [
        normalize_planet_vector(
            vector=vector,
            calibration_vectors=calibration,
            mode=mode,
        )
        for vector in vectors
    ]


def comparable_vectors(
    vector: PlanetFeatureVector,
    calibration_vectors: list[PlanetFeatureVector],
) -> list[PlanetFeatureVector]:
    """Return calibration vectors matching cipher and planet."""
    return [
        item
        for item in calibration_vectors
        if item.cipher == vector.cipher and item.planet == vector.planet
    ]


def normalize_feature_value(
    *,
    value: float,
    feature: str,
    calibration_vectors: list[PlanetFeatureVector],
    mode: str,
) -> float:
    """Normalize one feature value."""
    values = [
        item.features[feature]
        for item in calibration_vectors
        if feature in item.features
    ]

    if not values:
        return clamp(value)

    if mode == "percentile":
        return percentile_rank(value, values)

    if mode == "minmax":
        return minmax_scale(value, values)

    if mode == "zscore":
        return zscore_to_unit(value, values)

    if mode == "raw":
        return clamp(value)

    raise ValueError(f"Unknown normalization mode: {mode}")


def percentile_rank(value: float, values: list[float]) -> float:
    """Return percentile rank of value within values as 0-1."""
    if not values:
        return 0.0

    less = len(
        [
            item
            for item in values
            if item < value
        ]
    )

    equal = len(
        [
            item
            for item in values
            if item == value
        ]
    )

    return clamp((less + 0.5 * equal) / len(values))


def minmax_scale(value: float, values: list[float]) -> float:
    """Scale value by min/max of calibration values."""
    minimum = min(values)
    maximum = max(values)

    if maximum == minimum:
        return 0.5

    return clamp((value - minimum) / (maximum - minimum))


def zscore_to_unit(value: float, values: list[float]) -> float:
    """Convert z-score into a bounded 0-1 value."""
    if len(values) < 2:
        return 0.5

    avg = mean(values)
    std = pstdev(values)

    if std == 0:
        return 0.5

    z_score = (value - avg) / std

    # Soft clamp z-scores: -3 -> 0, 0 -> .5, +3 -> 1.
    return clamp((z_score + 3.0) / 6.0)


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, float(value)))