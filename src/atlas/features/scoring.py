"""Deterministic topology scoring."""

from dataclasses import dataclass

from atlas.features.metrics import (
    connected_components,
    edge_density,
    graph_symmetry,
    repeated_edges,
    repeated_nodes,
    weighted_in_degree,
    weighted_out_degree,
)
from atlas.topology.graph import TopologyGraph


@dataclass(frozen=True)
class TopologyScores:
    """Normalized topology score bundle."""

    driver: float
    amplifier: float
    regulator: float


def score_graph(graph: TopologyGraph) -> TopologyScores:
    """Score a topology graph deterministically.

    Driver:
        outward directional force.

    Amplifier:
        repetition, reinforcement, and density.

    Regulator:
        balance, reciprocity, and structural containment.
    """
    if graph.node_count == 0:
        return TopologyScores(driver=0.0, amplifier=0.0, regulator=0.0)

    driver = _score_driver(graph)
    amplifier = _score_amplifier(graph)
    regulator = _score_regulator(graph)

    return TopologyScores(
        driver=_clamp(driver),
        amplifier=_clamp(amplifier),
        regulator=_clamp(regulator),
    )


def _score_driver(graph: TopologyGraph) -> float:
    """Compute outward directional force."""
    weighted_out = weighted_out_degree(graph)

    if not weighted_out:
        return 0.0

    total_out = sum(weighted_out.values())

    if total_out == 0:
        return 0.0

    max_out = max(weighted_out.values())

    return max_out / total_out


def _score_amplifier(graph: TopologyGraph) -> float:
    """Compute repetition and reinforcement score."""
    repeated_node_count = len(repeated_nodes(graph))
    repeated_edge_count = len(repeated_edges(graph))

    node_repeat_ratio = repeated_node_count / graph.node_count if graph.node_count else 0.0
    edge_repeat_ratio = repeated_edge_count / graph.edge_count if graph.edge_count else 0.0

    density = edge_density(graph)

    return (node_repeat_ratio + edge_repeat_ratio + density) / 3


def _score_regulator(graph: TopologyGraph) -> float:
    """Compute balance and containment score."""
    weighted_in = weighted_in_degree(graph)
    weighted_out = weighted_out_degree(graph)

    balance = _in_out_balance(weighted_in, weighted_out)
    symmetry = graph_symmetry(graph)
    containment = _component_containment(graph)

    return (balance + symmetry + containment) / 3


def _in_out_balance(
    weighted_in: dict,
    weighted_out: dict,
) -> float:
    """Return how balanced weighted in/out flow is."""
    nodes = set(weighted_in) | set(weighted_out)

    if not nodes:
        return 0.0

    balances = []

    for node in nodes:
        incoming = weighted_in.get(node, 0)
        outgoing = weighted_out.get(node, 0)
        total = incoming + outgoing

        if total == 0:
            balances.append(0.0)
        else:
            balances.append(1 - abs(incoming - outgoing) / total)

    return sum(balances) / len(balances)


def _component_containment(graph: TopologyGraph) -> float:
    """Return containment based on few connected components."""
    if graph.node_count == 0:
        return 0.0

    components = connected_components(graph)

    if not components:
        return 0.0

    return 1 / len(components)


def _clamp(value: float) -> float:
    """Clamp a float into 0.0-1.0 range."""
    return max(0.0, min(1.0, value))