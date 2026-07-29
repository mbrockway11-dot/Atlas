"""The normalized composite shape: one structural fingerprint from all seven Kameas.

Each planet is a structural operator that turns the same input into its own graph
(Saturn 9 nodes, Moon 81). Their raw measurements are not comparable, so each
planet's traversal is first reduced to the dimensionless eight-axis shape vector
(``shape_vector``), already in [0, 1]. The composite then aggregates across the
seven planets on each axis, giving a single size-independent fingerprint that can
be compared between people regardless of graph size or planet count.

The composite is also *decomposable*: for each axis, the planetary contributions
(each planet's normalized share of that axis) say which operator drives that
structural dimension -- planet as contributor to structure, not as a symbol.

No interpretation is attached. The composite is a canonical structural object; any
comparison with an independently licensed tradition is a later, separate hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from atlas.ciphers import english_ordinal_sequence
from atlas.kamea.projection import project_values_to_all_kameas
from atlas.kamea.shape_vector import AXES, shape_vector

PLANET_ORDER = ("saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon")


@dataclass(frozen=True, slots=True)
class CompositeShape:
    """A person's normalized composite structural fingerprint."""

    composite: dict[str, float]
    contributions: dict[str, dict[str, float]]
    per_planet: dict[str, list[float]]
    degenerate_planets: tuple[str, ...]

    def vector(self) -> list[float]:
        """Return the composite as the eight axes in canonical order."""
        return [self.composite[axis] for axis in AXES]

    def dominant_planet(self, axis: str) -> str:
        """Return the planet contributing most to a given axis."""
        shares = self.contributions[axis]
        return max(shares, key=shares.get)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "composite": self.composite,
            "contributions": self.contributions,
            "per_planet": self.per_planet,
            "degenerate_planets": list(self.degenerate_planets),
        }


def composite_shape_from_values(values: Sequence[int]) -> CompositeShape:
    """Build the normalized composite shape from a raw value sequence."""
    paths = project_values_to_all_kameas(list(values), use_planetary_transform=True)
    per_planet: dict[str, list[float]] = {}
    degenerate: list[str] = []
    for planet in PLANET_ORDER:
        sv = shape_vector(paths[planet].coordinates)
        per_planet[planet] = sv.axis_vector()
        if sv.degenerate:
            degenerate.append(planet)

    matrix = np.array([per_planet[p] for p in PLANET_ORDER])  # 7 x 8
    composite: dict[str, float] = {}
    contributions: dict[str, dict[str, float]] = {}
    for index, axis in enumerate(AXES):
        column = matrix[:, index]
        composite[axis] = round(float(column.mean()), 6)
        total = float(column.sum())
        if total > 0:
            # Not rounded: contributions must partition the axis exactly (sum to 1).
            contributions[axis] = {
                p: float(column[i] / total) for i, p in enumerate(PLANET_ORDER)
            }
        else:
            contributions[axis] = {p: 0.0 for p in PLANET_ORDER}

    return CompositeShape(
        composite=composite,
        contributions=contributions,
        per_planet=per_planet,
        degenerate_planets=tuple(degenerate),
    )


def composite_shape_from_name(name: str) -> CompositeShape:
    """Build the normalized composite shape from a name (ordinal cipher)."""
    return composite_shape_from_values(english_ordinal_sequence(name))


def composite_distance(left: CompositeShape, right: CompositeShape) -> float:
    """Euclidean distance between two composite fingerprints in shape space."""
    a = np.array(left.vector())
    b = np.array(right.vector())
    return round(float(np.sqrt(((a - b) ** 2).sum())), 6)
