"""Simple deterministic clustering utilities for topology graphs."""

from dataclasses import dataclass

from atlas.resonance.resonance import calculate_resonance
from atlas.topology.graph import TopologyGraph


@dataclass(frozen=True)
class GraphCluster:
    """Cluster of graph labels."""

    label: str
    members: tuple[str, ...]


def cluster_by_resonance(
    graphs: dict[str, TopologyGraph],
    threshold: float = 0.75,
) -> tuple[GraphCluster, ...]:
    """Cluster graphs by pairwise resonance threshold.

    This is a simple deterministic connected-component clustering
    over a resonance similarity network.
    """
    labels = tuple(graphs.keys())

    adjacency = {label: set() for label in labels}

    for index, label_a in enumerate(labels):
        for label_b in labels[index + 1:]:
            resonance = calculate_resonance(graphs[label_a], graphs[label_b])

            if resonance.overall >= threshold:
                adjacency[label_a].add(label_b)
                adjacency[label_b].add(label_a)

    unvisited = set(labels)
    clusters = []

    for label in labels:
        if label not in unvisited:
            continue

        members = _walk_cluster(label, adjacency)
        unvisited -= members

        ordered_members = tuple(
            candidate for candidate in labels
            if candidate in members
        )

        clusters.append(
            GraphCluster(
                label=ordered_members[0],
                members=ordered_members,
            )
        )

    return tuple(clusters)


def _walk_cluster(
    start: str,
    adjacency: dict[str, set[str]],
) -> set[str]:
    """Walk one cluster."""
    visited = set()
    stack = [start]

    while stack:
        label = stack.pop()

        if label in visited:
            continue

        visited.add(label)

        for neighbor in adjacency[label]:
            if neighbor not in visited:
                stack.append(neighbor)

    return visited