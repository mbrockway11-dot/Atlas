"""Measured constraints on any planetary→Kamea mapping.

These are not tests of a mapping -- none exists yet. They pin the properties
of the machinery a mapping would have to use, because Temporal 1C's declared
invariants can only be assessed against measurements, not against intuition
about what a magic square "should" do.

The headline is that Kamea projection is discontinuous by construction. A
magic square scatters consecutive values so that rows, columns and diagonals
sum equally, so adjacent inputs do not land in adjacent cells. Any mapping
built on the existing machinery inherits that, whatever quantizer it chooses.
"""

from __future__ import annotations

import numpy as np
import pytest

from atlas.kamea.planetary_transform import PLANETARY_TRANSFORM_WEIGHTS
from atlas.kamea.squares import KAMEAS


def _mean_consecutive_step(kamea) -> float:
    """Return the mean grid distance between consecutively valued cells."""
    steps = [
        abs(kamea.coordinate_lookup[value][0]
            - kamea.coordinate_lookup[value + 1][0])
        + abs(kamea.coordinate_lookup[value][1]
              - kamea.coordinate_lookup[value + 1][1])
        for value in range(1, kamea.max_value)
    ]

    return float(np.mean(steps))


def _mean_random_step(kamea) -> float:
    """Return the mean grid distance between arbitrary cell pairs."""
    cells = [(r, c) for r in range(kamea.size) for c in range(kamea.size)]

    return float(
        np.mean(
            [
                abs(a[0] - b[0]) + abs(a[1] - b[1])
                for a in cells
                for b in cells
            ]
        )
    )


@pytest.mark.parametrize("key", sorted(KAMEAS))
def test_consecutive_values_are_not_neighbours(key: str) -> None:
    """Adjacent inputs do not land in adjacent cells.

    This is the measured basis for Temporal 1C's continuity finding. If a
    Kamea preserved locality, consecutive values would sit far closer than
    random pairs; they do not.
    """
    kamea = KAMEAS[key]

    consecutive = _mean_consecutive_step(kamea)
    random_pairs = _mean_random_step(kamea)

    # Locality would mean consecutive steps are a small fraction of random.
    # Observed ratios run 0.59 to 1.27 across the seven squares.
    assert consecutive > 0.5 * random_pairs


def test_no_kamea_preserves_locality() -> None:
    """Not one of the seven squares is locality-preserving.

    Stated as a single fact because it is the constraint that decides
    whether Temporal 1C's invariant 2 is satisfiable by this machinery at
    all. It is not.
    """
    ratios = {
        key: _mean_consecutive_step(kamea) / _mean_random_step(kamea)
        for key, kamea in KAMEAS.items()
    }

    assert all(ratio > 0.5 for ratio in ratios.values()), ratios
    assert min(ratios.values()) > 0.5
    assert max(ratios.values()) > 1.0


def test_reduction_is_modulo() -> None:
    """The existing reduction is already modular.

    Recorded because Temporal 1C listed "modular mapping" as a candidate
    when it is in fact what reduce_value does, so it is not a choice
    available to be made.
    """
    kamea = KAMEAS["saturn"]

    assert kamea.reduce_value(1) == 1
    assert kamea.reduce_value(kamea.max_value) == kamea.max_value
    assert kamea.reduce_value(kamea.max_value + 1) == 1
    assert kamea.reduce_value(2 * kamea.max_value + 3) == 3


def test_projection_consumes_an_ordered_sequence() -> None:
    """A Kamea path is a traversal, so a mapping must supply an order.

    A name gives one naturally: letters in sequence. Planetary positions at
    an instant are simultaneous and have no intrinsic order, so any temporal
    mapping must choose one. That choice is the second open question in 1C.
    """
    kamea = KAMEAS["saturn"]

    forward = kamea.project_values([1, 2, 3])
    reversed_path = kamea.project_values([3, 2, 1])

    assert forward.coordinates != reversed_path.coordinates
    assert forward.coordinates == tuple(reversed(reversed_path.coordinates))


def test_planetary_transform_covers_only_classical_bodies() -> None:
    """Uranus, Neptune and Pluto have no weights and no square.

    So a mapping built on this machinery covers 7 of the 10 bodies the
    temporal state records. That is a scope decision 1C must make
    explicitly rather than inherit by omission.
    """
    assert set(PLANETARY_TRANSFORM_WEIGHTS) == set(KAMEAS)
    assert len(KAMEAS) == 7

    for modern in ("uranus", "neptune", "pluto"):
        assert modern not in KAMEAS
        assert modern not in PLANETARY_TRANSFORM_WEIGHTS
