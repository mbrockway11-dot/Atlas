"""Static structural invariants of the planetary Kamea squares.

Determinism and known values only: given a fixed square, the invariants are
fixed, so these lock the measured constants and the honest structural facts
(uniform grid symmetry, Mercury's broken diagonal).
"""

from __future__ import annotations

import math

from atlas.kamea.square_invariants import (
    all_square_invariants,
    square_invariants,
    grid_graph,
)
from atlas.kamea.squares import KAMEAS


def test_saturn_grid_topology_matches_known_constants() -> None:
    """The 3x3 Lo Shu grid has textbook topology."""
    s = square_invariants(KAMEAS["saturn"])
    assert s.grid_nodes == 9
    assert s.grid_edges == 12
    assert s.grid_diameter == 4
    # Spectral radius of the 3x3 grid graph is 2*sqrt(2).
    assert math.isclose(s.grid_spectral_radius, 2.0 * math.sqrt(2.0), abs_tol=1e-6)


def test_grid_automorphisms_are_uniform_dihedral() -> None:
    """Every square board carries the same order-8 dihedral symmetry.

    Graph symmetry therefore cannot distinguish the squares -- the honest point
    the module documents.
    """
    inv = all_square_invariants()
    assert {s.grid_automorphisms for s in inv.values()} == {8}


def test_all_squares_semimagic_only_mercury_not_fully_magic() -> None:
    """Rows and columns always sum; Mercury alone has a broken diagonal."""
    inv = all_square_invariants()
    assert all(s.semimagic for s in inv.values())
    not_fully_magic = {key for key, s in inv.items() if not s.fully_magic}
    assert not_fully_magic == {"mercury"}


def test_invariants_are_deterministic() -> None:
    """Same square -> identical fingerprint, twice."""
    first = square_invariants(KAMEAS["mars"]).to_dict()
    second = square_invariants(KAMEAS["mars"]).to_dict()
    assert first == second


def test_grid_graph_has_value_attributes() -> None:
    """Every node carries its magic value; values are all distinct."""
    graph = grid_graph(KAMEAS["jupiter"])
    values = sorted(data["value"] for _, data in graph.nodes(data=True))
    assert values == list(range(1, 17))
