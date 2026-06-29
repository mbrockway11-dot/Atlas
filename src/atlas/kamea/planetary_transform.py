"""Planet-specific sequence transforms before Kamea projection.

The purpose of this module is to prevent large Kameas from receiving nearly
identical low-range paths.

Cipher values are first expanded through a deterministic planet-specific
transform, then reduced into the target Kamea range.
"""

from __future__ import annotations


PLANETARY_TRANSFORM_WEIGHTS = {
    "saturn": {
        "multiplier": 1,
        "index_weight": 1,
        "offset": 0,
    },
    "jupiter": {
        "multiplier": 2,
        "index_weight": 3,
        "offset": 1,
    },
    "mars": {
        "multiplier": 3,
        "index_weight": 5,
        "offset": 2,
    },
    "sun": {
        "multiplier": 5,
        "index_weight": 7,
        "offset": 3,
    },
    "venus": {
        "multiplier": 7,
        "index_weight": 11,
        "offset": 4,
    },
    "mercury": {
        "multiplier": 11,
        "index_weight": 13,
        "offset": 5,
    },
    "moon": {
        "multiplier": 13,
        "index_weight": 17,
        "offset": 6,
    },
}


def transform_values_for_planet(
    values: list[int],
    kamea_name: str,
) -> list[int]:
    """Apply deterministic planet-specific expansion before projection."""
    key = kamea_name.lower().strip()

    if key not in PLANETARY_TRANSFORM_WEIGHTS:
        available = ", ".join(sorted(PLANETARY_TRANSFORM_WEIGHTS))
        raise ValueError(
            f"Unknown planetary transform '{kamea_name}'. Available: {available}"
        )

    weights = PLANETARY_TRANSFORM_WEIGHTS[key]

    multiplier = weights["multiplier"]
    index_weight = weights["index_weight"]
    offset = weights["offset"]

    return [
        transform_value(
            value=value,
            index=index,
            multiplier=multiplier,
            index_weight=index_weight,
            offset=offset,
        )
        for index, value in enumerate(values)
    ]


def transform_value(
    *,
    value: int,
    index: int,
    multiplier: int,
    index_weight: int,
    offset: int,
) -> int:
    """Transform one value while keeping it positive."""
    if value <= 0:
        raise ValueError("Planetary transform values must be positive integers.")

    return (value * multiplier) + ((index + 1) * index_weight) + offset