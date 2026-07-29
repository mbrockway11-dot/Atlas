"""The normalized composite shape fingerprint.

Structural guarantees only: eight axes in [0,1], contributions that partition each
axis across the seven planets, and determinism.
"""

from __future__ import annotations

import math

from atlas.kamea.composite_shape import (
    PLANET_ORDER,
    composite_distance,
    composite_shape_from_name,
    composite_shape_from_values,
)
from atlas.kamea.shape_vector import AXES


def test_composite_has_eight_axes_in_unit_range() -> None:
    cs = composite_shape_from_name("Ada Lovelace")
    vec = cs.vector()
    assert len(vec) == 8
    assert set(cs.composite) == set(AXES)
    assert all(0.0 <= v <= 1.0 for v in vec)


def test_contributions_partition_each_axis() -> None:
    """Per axis, the seven planetary shares sum to 1 (or to 0 when the axis is 0)."""
    cs = composite_shape_from_name("Nikola Tesla")
    for axis in AXES:
        shares = cs.contributions[axis]
        assert set(shares) == set(PLANET_ORDER)
        total = sum(shares.values())
        assert math.isclose(total, 1.0, abs_tol=1e-6) or math.isclose(total, 0.0, abs_tol=1e-6)


def test_dominant_planet_is_the_largest_contributor() -> None:
    cs = composite_shape_from_name("Thomas Edison")
    for axis in AXES:
        dom = cs.dominant_planet(axis)
        assert cs.contributions[axis][dom] == max(cs.contributions[axis].values())


def test_composite_is_deterministic_and_self_distance_zero() -> None:
    a = composite_shape_from_values([13, 9, 3, 8, 1, 5, 12])
    b = composite_shape_from_values([13, 9, 3, 8, 1, 5, 12])
    assert a.to_dict() == b.to_dict()
    assert composite_distance(a, b) == 0.0
