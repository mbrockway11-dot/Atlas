"""Composite planet vector builder.

Composite vectors combine the three translation/cipher layers for the same
planet feature-by-feature.

The result is one normalized structural vector per planet.
"""

from __future__ import annotations

from statistics import mean
from typing import Any

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

    features = {
        feature: mean(
            [
                vector.features[feature]
                for vector in planet_vectors
            ]
        )
        for feature in VECTOR_FEATURES
    }

    source_ciphers = sorted(
        {
            vector.cipher
            for vector in planet_vectors
        }
    )

    return CompositePlanetVector(
        version=IVE_VERSION,
        name=name,
        planet=planet,
        features=features,
        source_ciphers=source_ciphers,
        source_count=len(source_ciphers),
        normalization_mode=normalization_mode,
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
