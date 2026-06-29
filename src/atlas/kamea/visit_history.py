"""Kamea node visit history with z-axis depth."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NodeVisit:
    """One visit to a wrapped Kamea node."""

    node: int
    coordinate: tuple[int, int]
    sequence_index: int
    visit_depth: int


def build_node_visit_history(kamea_path: Any) -> dict:
    """Build visit history for a KameaPath.

    Repeated nodes are preserved as visits with increasing z-depth.
    """
    wrapped_values = list(kamea_path.reduced_values)
    coordinates = [tuple(coord) for coord in kamea_path.coordinates]

    depth_counter: dict[int, int] = defaultdict(int)
    visits: list[NodeVisit] = []

    for sequence_index, (node, coordinate) in enumerate(
        zip(wrapped_values, coordinates)
    ):
        visit_depth = depth_counter[node]

        visits.append(
            NodeVisit(
                node=node,
                coordinate=coordinate,
                sequence_index=sequence_index,
                visit_depth=visit_depth,
            )
        )

        depth_counter[node] += 1

    histories: dict[int, list[NodeVisit]] = defaultdict(list)

    for visit in visits:
        histories[visit.node].append(visit)

    return {
        "visits": [node_visit_to_dict(visit) for visit in visits],
        "node_histories": {
            str(node): [node_visit_to_dict(visit) for visit in node_visits]
            for node, node_visits in histories.items()
        },
        "node_weights": {
            str(node): len(node_visits)
            for node, node_visits in histories.items()
        },
        "max_depth": max((visit.visit_depth for visit in visits), default=0),
    }


def node_visit_to_dict(visit: NodeVisit) -> dict:
    """Convert NodeVisit to JSON-safe dictionary."""
    return {
        "node": visit.node,
        "coordinate": list(visit.coordinate),
        "sequence_index": visit.sequence_index,
        "visit_depth": visit.visit_depth,
    }