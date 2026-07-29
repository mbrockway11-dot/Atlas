"""Composite planet vector builder.

Composite vectors combine the three translation/cipher layers for the same
planet feature-by-feature.

The result is one normalized structural vector per planet.
"""

from __future__ import annotations

from statistics import mean, pvariance
from typing import Any

from atlas.fusion.translation import EXPECTED_CIPHERS, variance_to_agreement
from atlas.ive.schema import (
    IVE_VERSION,
    VECTOR_FEATURES,
    CompositePlanetVector,
    NormalizedPlanetVector,
)


PLANET_ORDER = [
    "Saturn",
    "Jupiter",
    "Mars",
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
]


def build_composite_planet_vector(
    planet: str,
    vectors: list[NormalizedPlanetVector],
) -> CompositePlanetVector:
    """Build one composite planet vector from normalized source vectors."""
    planet_vectors = [
        vector
        for vector in vectors
        if vector.planet == planet
    ]

    if not planet_vectors:
        raise ValueError(f"No normalized vectors supplied for planet: {planet}")

    name = planet_vectors[0].name
    normalization_mode = planet_vectors[0].normalization_mode

    feature_values = {
        feature: [vector.features[feature] for vector in planet_vectors]
        for feature in VECTOR_FEATURES
    }

    features = {
        feature: mean(values)
        for feature, values in feature_values.items()
    }

    # Cross-cipher agreement: 1 / (1 + variance) per feature, so features the
    # ciphers converged on score near 1 and features they scattered on drop
    # toward 0. A single cipher has no disagreement to measure -> agreement 1.0.
    feature_agreement = {
        feature: (
            variance_to_agreement(pvariance(values)) if len(values) > 1 else 1.0
        )
        for feature, values in feature_values.items()
    }

    source_ciphers = sorted(
        {
            vector.cipher
            for vector in planet_vectors
        }
    )

    agreement_score = (
        mean(feature_agreement.values()) if feature_agreement else 1.0
    )
    # Completeness penalises missing ciphers; confidence combines the two, so a
    # planet built from one cipher is not treated as a confident consensus.
    completeness = len(source_ciphers) / len(EXPECTED_CIPHERS)
    confidence_score = agreement_score * completeness

    return CompositePlanetVector(
        version=IVE_VERSION,
        name=name,
        planet=planet,
        features=features,
        source_ciphers=source_ciphers,
        source_count=len(source_ciphers),
        normalization_mode=normalization_mode,
        feature_agreement=feature_agreement,
        agreement_score=agreement_score,
        completeness=completeness,
        confidence_score=confidence_score,
    )


def build_composite_planet_vectors(
    vectors: list[NormalizedPlanetVector],
) -> list[CompositePlanetVector]:
    """Build all available composite planet vectors."""
    planets = ordered_planets(
        {
            vector.planet
            for vector in vectors
        }
    )

    return [
        build_composite_planet_vector(
            planet=planet,
            vectors=vectors,
        )
        for planet in planets
    ]


def composite_vectors_to_feature_table(
    vectors: list[CompositePlanetVector],
) -> list[dict[str, Any]]:
    """Convert composite vectors into table rows."""
    rows = []

    for vector in vectors:
        row = {
            "name": vector.name,
            "planet": vector.planet,
            "source_count": vector.source_count,
            "source_ciphers": ", ".join(vector.source_ciphers),
            "normalization_mode": vector.normalization_mode,
        }
        row.update(vector.features)
        rows.append(row)

    return rows


def ordered_planets(planets: set[str]) -> list[str]:
    """Sort planets by canonical order first, then alphabetically."""
    known = [
        planet
        for planet in PLANET_ORDER
        if planet in planets
    ]

    unknown = sorted(
        planet
        for planet in planets
        if planet not in PLANET_ORDER
    )

    return known + unknown