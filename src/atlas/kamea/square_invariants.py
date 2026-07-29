"""Static structural invariants of a planetary Kamea square.

The Structural Plane of Representation 1E, made concrete: a magic square carries
no history and no meaning, only geometry. This module turns each of the seven
canonical squares into a graph and measures it. The measurements are licensed by
mathematics -- given the same square, anyone computes the same values -- so they
stop at measurement and never cross into interpretation.

Two connection rules, both deterministic, are made explicit here because a
square does not come with a graph attached:

* **grid graph** -- cells are nodes, orthogonally adjacent cells are edges. This
  is the positional rule. Its pure-topology invariants depend only on the board
  size ``n`` (every n x n grid is the same shape), so they order the squares by
  size and nothing more. The square's own arrangement enters only through the
  *value-layer* invariants computed over the same edges.
* **sigil** -- the traditional seal, the path 1 -> 2 -> ... -> n^2 through the
  cells. This is the value-order rule; its geometry (length, self-crossings,
  turning entropy) is genuinely specific to how the square was constructed.

Honest note on symmetry: because every value in a magic square is distinct, the
value-labelled automorphism group is always trivial (order 1), and the unlabelled
grid's automorphism group is always the board's dihedral group (order 8). Graph
symmetry therefore does not distinguish the squares; their value arrangement and
sigil geometry do.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import networkx as nx
import numpy as np

from atlas.kamea.base import PlanetaryKamea
from atlas.kamea.squares import KAMEAS
from atlas.kamea_flow.shape import count_self_intersections, turning_angles


SQUARE_INVARIANTS_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class SquareInvariants:
    """One planetary square's static structural fingerprint.

    Fields are grouped by what they actually reflect: ``grid_*`` topology is
    size-driven; ``value_*`` and ``sigil_*`` are specific to the arrangement.
    """

    key: str
    planet: str
    size: int

    # Grid topology -- canonical, but size-driven (same shape for a given n).
    grid_nodes: int
    grid_edges: int
    grid_density: float
    grid_diameter: int
    grid_radius: int
    grid_average_shortest_path: float
    grid_mean_degree: float
    grid_degree_entropy: float
    grid_clustering: float
    grid_spectral_radius: float
    grid_algebraic_connectivity: float
    grid_automorphisms: int

    # Value arrangement over the grid edges -- specific to this square.
    value_mean_abs_neighbor_delta: float
    value_var_abs_neighbor_delta: float
    value_max_neighbor_delta: int
    value_neighbor_assortativity: float
    value_consecutive_edge_fraction: float
    # Rows and columns always sum to the magic constant; the traditional Mercury
    # square has a broken anti-diagonal, so fully_magic distinguishes it.
    semimagic: bool
    fully_magic: bool

    # Sigil (the seal, 1 -> n^2) geometry -- specific to this square.
    sigil_length: float
    sigil_mean_step: float
    sigil_self_intersections: int
    sigil_turning_entropy: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return asdict(self)


def grid_graph(kamea: PlanetaryKamea) -> nx.Graph:
    """Return the orthogonal grid graph of a square, values as node attributes."""
    size = kamea.size
    graph = nx.grid_2d_graph(size, size)
    for row in range(size):
        for col in range(size):
            graph.nodes[(row, col)]["value"] = kamea.square[row][col]
    return graph


def sigil_coordinates(kamea: PlanetaryKamea) -> list[list[float]]:
    """Return the seal path: cell of value 1, then 2, ... up to n^2."""
    return [
        [float(col), float(row)]
        for value in range(1, kamea.max_value + 1)
        for (row, col) in (kamea.coordinate_lookup[value],)
    ]


def _degree_entropy(graph: nx.Graph) -> float:
    degrees = [degree for _, degree in graph.degree()]
    total = len(degrees)
    counts: dict[int, int] = {}
    for degree in degrees:
        counts[degree] = counts.get(degree, 0) + 1
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)
    return round(entropy, 6)


def _spectral_radius(graph: nx.Graph) -> float:
    adjacency = nx.to_numpy_array(graph, nodelist=sorted(graph.nodes()))
    eigenvalues = np.linalg.eigvalsh(adjacency)
    return round(float(np.max(np.abs(eigenvalues))), 6)


def _algebraic_connectivity(graph: nx.Graph) -> float:
    # Laplacian L = D - A built in numpy (networkx's needs scipy, unavailable).
    adjacency = nx.to_numpy_array(graph, nodelist=sorted(graph.nodes()))
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    eigenvalues = np.sort(np.linalg.eigvalsh(laplacian))
    return round(float(eigenvalues[1]), 6)


def _automorphism_count(graph: nx.Graph) -> int:
    matcher = nx.algorithms.isomorphism.GraphMatcher(graph, graph)
    return sum(1 for _ in matcher.isomorphisms_iter())


def _value_edge_stats(graph: nx.Graph) -> tuple[float, float, int, float, float]:
    left: list[int] = []
    right: list[int] = []
    deltas: list[int] = []
    for u, v in graph.edges():
        vu = graph.nodes[u]["value"]
        vv = graph.nodes[v]["value"]
        deltas.append(abs(vu - vv))
        # Symmetric edge: contribute both orientations for assortativity.
        left.extend((vu, vv))
        right.extend((vv, vu))
    delta_array = np.array(deltas, dtype=float)
    consecutive = float(np.mean(delta_array == 1.0))
    assortativity = float(np.corrcoef(left, right)[0, 1]) if len(deltas) > 1 else 0.0
    return (
        round(float(delta_array.mean()), 6),
        round(float(delta_array.var()), 6),
        int(delta_array.max()),
        round(assortativity, 6),
        round(consecutive, 6),
    )


def _magic_structure(kamea: PlanetaryKamea) -> tuple[bool, bool]:
    """Return ``(semimagic, fully_magic)``.

    ``semimagic`` -- every row and column sums to the magic constant.
    ``fully_magic`` -- both diagonals do as well. The traditional Mercury Kamea
    is semimagic but not fully magic (its anti-diagonal is broken).
    """
    size, target, square = kamea.size, kamea.magic_sum, kamea.square
    rows = [sum(row) for row in square]
    cols = [sum(square[r][c] for r in range(size)) for c in range(size)]
    main = sum(square[i][i] for i in range(size))
    anti = sum(square[i][size - 1 - i] for i in range(size))
    semimagic = all(line == target for line in rows + cols)
    fully_magic = semimagic and main == target and anti == target
    return semimagic, fully_magic


def _sigil_geometry(kamea: PlanetaryKamea) -> tuple[float, float, int, float]:
    points = sigil_coordinates(kamea)
    steps = [
        math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)
    ]
    length = sum(steps)
    mean_step = length / len(steps) if steps else 0.0
    crossings = count_self_intersections(points)
    # Entropy of turning direction, binned into eight sectors.
    angles = turning_angles(points)
    if angles:
        bins = np.zeros(8)
        for angle in angles:
            index = int((angle + math.pi) / (2 * math.pi) * 8) % 8
            bins[index] += 1
        probabilities = bins[bins > 0] / bins.sum()
        turning_entropy = float(-(probabilities * np.log2(probabilities)).sum())
    else:
        turning_entropy = 0.0
    return round(length, 6), round(mean_step, 6), crossings, round(turning_entropy, 6)


def square_invariants(kamea: PlanetaryKamea) -> SquareInvariants:
    """Measure one planetary square's static structural fingerprint."""
    graph = grid_graph(kamea)
    degrees = [degree for _, degree in graph.degree()]
    mean_delta, var_delta, max_delta, assortativity, consecutive = _value_edge_stats(
        graph
    )
    length, mean_step, crossings, turning_entropy = _sigil_geometry(kamea)
    semimagic, fully_magic = _magic_structure(kamea)

    return SquareInvariants(
        key=kamea.key,
        planet=kamea.planet,
        size=kamea.size,
        grid_nodes=graph.number_of_nodes(),
        grid_edges=graph.number_of_edges(),
        grid_density=round(nx.density(graph), 6),
        grid_diameter=nx.diameter(graph),
        grid_radius=nx.radius(graph),
        grid_average_shortest_path=round(nx.average_shortest_path_length(graph), 6),
        grid_mean_degree=round(sum(degrees) / len(degrees), 6),
        grid_degree_entropy=_degree_entropy(graph),
        grid_clustering=round(nx.average_clustering(graph), 6),
        grid_spectral_radius=_spectral_radius(graph),
        grid_algebraic_connectivity=_algebraic_connectivity(graph),
        grid_automorphisms=_automorphism_count(graph),
        value_mean_abs_neighbor_delta=mean_delta,
        value_var_abs_neighbor_delta=var_delta,
        value_max_neighbor_delta=max_delta,
        value_neighbor_assortativity=assortativity,
        value_consecutive_edge_fraction=consecutive,
        semimagic=semimagic,
        fully_magic=fully_magic,
        sigil_length=length,
        sigil_mean_step=mean_step,
        sigil_self_intersections=crossings,
        sigil_turning_entropy=turning_entropy,
    )


def all_square_invariants() -> dict[str, SquareInvariants]:
    """Measure every canonical planetary square, keyed by Kamea key."""
    return {key: square_invariants(kamea) for key, kamea in KAMEAS.items()}
