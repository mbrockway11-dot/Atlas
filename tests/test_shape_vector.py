"""The eight-axis structural shape vector of a Kamea traversal.

Deterministic graph facts: a 4-cycle, a path, and a degenerate single cell have
known invariants, so these lock the axis definitions.
"""

from __future__ import annotations

import math

from atlas.kamea.shape_vector import shape_vector


def test_four_cycle_has_one_independent_cycle_and_full_resilience() -> None:
    """A square loop: one cycle, no articulation point, high symmetry."""
    coords = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]
    sv = shape_vector(coords)
    assert not sv.degenerate
    assert sv.nodes == 4
    assert sv.moving_edges == 4
    assert sv.cyclomatic_number == 1
    assert math.isclose(sv.topology, 0.25, abs_tol=1e-6)
    assert math.isclose(sv.resilience, 1.0, abs_tol=1e-6)  # no articulation points
    assert sv.automorphisms == 8  # dihedral group of C4
    assert math.isclose(sv.symmetry, 1 - 1 / 8, abs_tol=1e-6)


def test_path_has_no_cycle_and_interior_articulation() -> None:
    """A straight path: zero cycles, the middle node is a cut vertex."""
    coords = [(0, 0), (0, 1), (0, 2)]
    sv = shape_vector(coords)
    assert sv.cyclomatic_number == 0
    assert math.isclose(sv.topology, 0.0, abs_tol=1e-6)
    # 1 of 3 nodes is an articulation point.
    assert math.isclose(sv.resilience, 1 - 1 / 3, abs_tol=1e-6)


def test_stationary_traversal_is_degenerate() -> None:
    """A walk that never leaves its cell has no shape."""
    sv = shape_vector([(2, 2), (2, 2), (2, 2)])
    assert sv.degenerate
    assert sv.axis_vector() == [0.0] * 8


def test_redundancy_counts_retraced_moves() -> None:
    """Retracing an edge raises redundancy above zero."""
    # out and back twice on the same edge: 2 moving transitions, 1 unique edge.
    sv = shape_vector([(0, 0), (0, 1), (0, 0)])
    assert sv.moving_edges == 1
    assert math.isclose(sv.redundancy, 0.5, abs_tol=1e-6)
