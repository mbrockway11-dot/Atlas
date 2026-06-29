"""Normalized structural role measurements."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass


Coordinate = tuple[int, int]
Edge = tuple[Coordinate, Coordinate]


STRUCTURAL_ROLES = [
    "core",
    "hub",
    "bridge",
    "attractor",
    "gateway",
    "exit",
    "oscillator",
    "loop_anchor",
    "leaf",
    "isolate",
]


@dataclass(frozen=True)
class StructuralRoleMeasurement:
    """Normalized structural role distribution."""

    roles: dict[str, float]


def measure_structural_roles(
    path: list[Coordinate],
    nodes: Counter[Coordinate],
    edges: Counter[Edge],
) -> StructuralRoleMeasurement:
    """Measure normalized structural role probabilities."""
    incoming = incoming_counts(edges)
    outgoing = outgoing_counts(edges)
    degree = degree_counts(edges)

    total_node_visits = sum(nodes.values())
    total_edges = sum(edges.values())

    roles = {
        "core": core_score(nodes, total_node_visits),
        "hub": hub_score(degree),
        "bridge": bridge_score(edges, total_edges),
        "attractor": attractor_score(incoming, nodes),
        "gateway": gateway_score(path, nodes),
        "exit": exit_score(path, nodes),
        "oscillator": oscillator_score(path),
        "loop_anchor": loop_anchor_score(edges, total_edges),
        "leaf": leaf_score(degree, nodes),
        "isolate": isolate_score(degree, nodes),
    }

    return StructuralRoleMeasurement(
        roles={
            role: clamp(value)
            for role, value in roles.items()
        }
    )


def incoming_counts(edges: Counter[Edge]) -> dict[Coordinate, int]:
    """Count incoming weighted edges."""
    counts: dict[Coordinate, int] = defaultdict(int)

    for (_, target), weight in edges.items():
        counts[target] += weight

    return dict(counts)


def outgoing_counts(edges: Counter[Edge]) -> dict[Coordinate, int]:
    """Count outgoing weighted edges."""
    counts: dict[Coordinate, int] = defaultdict(int)

    for (source, _), weight in edges.items():
        counts[source] += weight

    return dict(counts)


def degree_counts(edges: Counter[Edge]) -> dict[Coordinate, int]:
    """Count weighted in/out degree."""
    counts: dict[Coordinate, int] = defaultdict(int)

    for (source, target), weight in edges.items():
        counts[source] += weight
        counts[target] += weight

    return dict(counts)


def core_score(
    nodes: Counter[Coordinate],
    total_node_visits: int,
) -> float:
    """Estimate core concentration."""
    if not nodes or total_node_visits == 0:
        return 0.0

    strongest = max(nodes.values())

    return strongest / total_node_visits


def hub_score(degree: dict[Coordinate, int]) -> float:
    """Estimate hub dominance."""
    if not degree:
        return 0.0

    total = sum(degree.values())

    if total == 0:
        return 0.0

    return max(degree.values()) / total


def bridge_score(
    edges: Counter[Edge],
    total_edges: int,
) -> float:
    """Estimate bridge concentration."""
    if not edges or total_edges == 0:
        return 0.0

    return max(edges.values()) / total_edges


def attractor_score(
    incoming: dict[Coordinate, int],
    nodes: Counter[Coordinate],
) -> float:
    """Estimate attractor strength from incoming flow and revisits."""
    if not incoming or not nodes:
        return 0.0

    total_incoming = sum(incoming.values())

    if total_incoming == 0:
        return 0.0

    strongest_incoming = max(incoming.values())
    repeated_nodes = sum(1 for value in nodes.values() if value > 1)

    return average(
        [
            strongest_incoming / total_incoming,
            safe_ratio(repeated_nodes, len(nodes)),
        ]
    )


def gateway_score(
    path: list[Coordinate],
    nodes: Counter[Coordinate],
) -> float:
    """Estimate gateway strength from first-entry uniqueness."""
    if not path or not nodes:
        return 0.0

    first = path[0]

    return 1.0 - safe_ratio(nodes[first] - 1, max(sum(nodes.values()) - 1, 1))


def exit_score(
    path: list[Coordinate],
    nodes: Counter[Coordinate],
) -> float:
    """Estimate terminal sink / exit strength."""
    if not path or not nodes:
        return 0.0

    last = path[-1]

    return 1.0 - safe_ratio(nodes[last] - 1, max(sum(nodes.values()) - 1, 1))


def oscillator_score(path: list[Coordinate]) -> float:
    """Measure A-B-A oscillation patterns."""
    if len(path) < 3:
        return 0.0

    oscillations = 0

    for index in range(2, len(path)):
        if path[index] == path[index - 2] and path[index] != path[index - 1]:
            oscillations += 1

    return safe_ratio(oscillations, len(path) - 2)


def loop_anchor_score(
    edges: Counter[Edge],
    total_edges: int,
) -> float:
    """Measure self-loop anchoring."""
    if not edges or total_edges == 0:
        return 0.0

    loops = sum(
        weight
        for (source, target), weight in edges.items()
        if source == target
    )

    return loops / total_edges


def leaf_score(
    degree: dict[Coordinate, int],
    nodes: Counter[Coordinate],
) -> float:
    """Measure leaf/dead-end ratio."""
    if not nodes:
        return 0.0

    leaves = sum(
        1
        for node in nodes
        if degree.get(node, 0) == 1
    )

    return leaves / len(nodes)


def isolate_score(
    degree: dict[Coordinate, int],
    nodes: Counter[Coordinate],
) -> float:
    """Measure isolated visited nodes."""
    if not nodes:
        return 0.0

    isolates = sum(
        1
        for node in nodes
        if degree.get(node, 0) == 0
    )

    return isolates / len(nodes)


def average(values: list[float]) -> float:
    """Average values safely."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def safe_ratio(a: float, b: float) -> float:
    """Safely divide."""
    if b == 0:
        return 0.0

    return float(a) / float(b)


def clamp(value: float) -> float:
    """Clamp 0-1."""
    return max(0.0, min(1.0, float(value)))