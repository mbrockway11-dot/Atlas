"""Fractal / self-similarity measures of a traversal.

Known-geometry checks: a line is one-dimensional, a filled grid two-dimensional,
and the measures are deterministic.
"""

from __future__ import annotations

import math

from atlas.kamea.fractal_shape import (
    box_counting_dimension,
    correlation_dimension,
    fractal_signature,
)


def test_line_is_one_dimensional() -> None:
    line = [[i / 200, 0.0] for i in range(201)]
    d, r2 = box_counting_dimension(line)
    assert math.isclose(d, 1.0, abs_tol=0.15)
    assert r2 > 0.98


def test_filled_grid_is_two_dimensional() -> None:
    grid = [[x / 30, y / 30] for x in range(31) for y in range(31)]
    d, r2 = box_counting_dimension(grid)
    assert math.isclose(d, 2.0, abs_tol=0.15)
    assert r2 > 0.98


def test_correlation_dimension_of_line() -> None:
    line = [[i / 200, 0.0] for i in range(201)]
    d, r2 = correlation_dimension(line)
    assert math.isclose(d, 1.0, abs_tol=0.2)


def test_signature_is_deterministic() -> None:
    pts = [[x / 10, (x * x % 7) / 7] for x in range(40)]
    assert fractal_signature(pts).to_dict() == fractal_signature(pts).to_dict()


def test_degenerate_inputs_do_not_crash() -> None:
    sig = fractal_signature([[0.0, 0.0], [0.0, 0.0]])
    # A single distinct point: dimensions are nan, not an exception.
    assert sig.box_dimension != sig.box_dimension or sig.box_dimension == 0.0
