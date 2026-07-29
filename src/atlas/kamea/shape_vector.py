"""A person's structural shape: the graph invariants of their Kamea traversal.

The sigil is a projection of the underlying graph; the *shape* is the collection
of invariants that survive however the sigil is drawn. This module turns a Kamea
traversal (the ordered cells a subject's inputs visit on a square) into its
transition graph and reduces it to an eight-axis shape vector:

    topology        independent cycles -- how branched/looped the structure is
    symmetry        graph automorphisms -- how much of it maps onto itself
    flow            weight concentration -- one dominant route vs many equal ones
    hierarchy       inequality of dwell -- hub-and-spoke vs flat
    redundancy      retraced moves -- how much the path reuses its own edges
    centralization  degree centralization -- how much one node dominates
    complexity      entropy of visitation -- how spread and varied the walk is
    resilience      non-articulation fraction -- robustness to node removal

Every axis is a deterministic measurement in [0, 1], licensed by mathematics
only. No meaning is attached: the shape vector is what an empirical phase would
compare or cluster, not something to interpret on its own.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Sequence

import networkx as nx


SHAPE_VECTOR_VERSION = "1.0.0"

Coordinate = tuple[int, int]

AXES = (
    "topology",
    "symmetry",
    "flow",
    "hierarchy",
    "redundancy",
    "centralization",
    "complexity",
    "resilience",
)


@dataclass(frozen=True, slots=True)
class ShapeVector:
    """One traversal's eight-axis structural signature, plus raw invariants."""

    topology: float
    symmetry: float
    flow: float
    hierarchy: float
    redundancy: float
    centralization: float
    complexity: float
    resilience: float

    nodes: int
    moving_edges: int
    cyclomatic_number: int
    automorphisms: int
    degenerate: bool

    def axis_vector(self) -> list[float]:
        """Return the eight axes in canonical order."""
        return [getattr(self, axis) for axis in AXES]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return asdict(self)


def transition_graphs(
    coordinates: Sequence[Coordinate],
) -> tuple[nx.Graph, dict[Coordinate, int], dict[frozenset, int], int, int]:
    """Return the undirected transition graph and the walk's weights.

    Self-transitions (dwelling in one cell) are not edges; they are counted as
    dwell in the visit weights. Moving transitions carry a weight = how often the
    walk used that pair.
    """
    visits: dict[Coordinate, int] = {}
    for cell in coordinates:
        visits[cell] = visits.get(cell, 0) + 1

    edge_weights: dict[frozenset, int] = {}
    moving = 0
    for left, right in zip(coordinates, coordinates[1:]):
        if left == right:
            continue
        moving += 1
        key = frozenset((left, right))
        edge_weights[key] = edge_weights.get(key, 0) + 1

    graph = nx.Graph()
    graph.add_nodes_from(visits)
    for key in edge_weights:
        pair = tuple(key)
        if len(pair) == 2:
            graph.add_edge(pair[0], pair[1])

    return graph, visits, edge_weights, moving, len(edge_weights)


def _gini(values: list[float]) -> float:
    if not values or sum(values) == 0:
        return 0.0
    ordered = sorted(values)
    n = len(ordered)
    cumulative = sum((i + 1) * v for i, v in enumerate(ordered))
    return round((2 * cumulative) / (n * sum(ordered)) - (n + 1) / n, 6)


def _normalized_entropy(values: list[int]) -> float:
    total = sum(values)
    if total == 0 or len(values) <= 1:
        return 0.0
    entropy = -sum((v / total) * math.log2(v / total) for v in values if v > 0)
    return round(entropy / math.log2(len(values)), 6)


_AUTOMORPHISM_CAP = 5040  # 1 - 1/5040 ~ 0.9998: the symmetry axis has saturated.


def _automorphism_count(graph: nx.Graph) -> int:
    """Count graph automorphisms, capped.

    A dense traversal graph can have a factorial automorphism group (a
    near-complete graph on k nodes has k! of them), so enumerating them all
    hangs. The symmetry axis is ``1 - 1/count`` and saturates well before the
    cap, so stopping early costs nothing. Very large graphs skip entirely.
    """
    n = graph.number_of_nodes()
    if n > 60:
        return 1
    if graph.number_of_edges() > 3 * n:
        # Dense graph: the automorphism group is large. Skip enumeration and
        # treat symmetry as saturated -- exactly what a capped enumeration yields.
        return _AUTOMORPHISM_CAP
    matcher = nx.algorithms.isomorphism.GraphMatcher(graph, graph)
    count = 0
    for _ in matcher.isomorphisms_iter():
        count += 1
        if count >= _AUTOMORPHISM_CAP:
            break
    return count


def _degree_centralization(graph: nx.Graph) -> float:
    n = graph.number_of_nodes()
    if n < 3:
        return 0.0
    degrees = [d for _, d in graph.degree()]
    d_max = max(degrees)
    numerator = sum(d_max - d for d in degrees)
    denominator = (n - 1) * (n - 2)
    return round(numerator / denominator, 6) if denominator else 0.0


def shape_vector(coordinates: Sequence[Coordinate]) -> ShapeVector:
    """Reduce a Kamea traversal to its eight-axis structural shape."""
    graph, visits, edge_weights, moving, unique_edges = transition_graphs(coordinates)
    n = graph.number_of_nodes()
    components = nx.number_connected_components(graph) if n else 0
    degenerate = n < 2 or unique_edges == 0

    if degenerate:
        return ShapeVector(
            topology=0.0, symmetry=0.0, flow=0.0, hierarchy=0.0, redundancy=0.0,
            centralization=0.0, complexity=0.0, resilience=0.0,
            nodes=n, moving_edges=unique_edges, cyclomatic_number=0,
            automorphisms=1, degenerate=True,
        )

    cyclomatic = unique_edges - n + components
    weights = list(edge_weights.values())
    total_weight = sum(weights)
    automorphisms = _automorphism_count(graph)
    articulation = list(nx.articulation_points(graph))

    topology = round(cyclomatic / unique_edges, 6)
    symmetry = round(1.0 - 1.0 / automorphisms, 6)
    flow = round(sum((w / total_weight) ** 2 for w in weights), 6)
    hierarchy = _gini([float(v) for v in visits.values()])
    redundancy = round((moving - unique_edges) / moving, 6) if moving else 0.0
    centralization = _degree_centralization(graph)
    complexity = _normalized_entropy(list(visits.values()))
    resilience = round(1.0 - len(articulation) / n, 6)

    return ShapeVector(
        topology=topology, symmetry=symmetry, flow=flow, hierarchy=hierarchy,
        redundancy=redundancy, centralization=centralization,
        complexity=complexity, resilience=resilience,
        nodes=n, moving_edges=unique_edges, cyclomatic_number=cyclomatic,
        automorphisms=automorphisms, degenerate=False,
    )
