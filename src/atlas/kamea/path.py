"""Kamea path objects."""

from dataclasses import dataclass
from collections import Counter


Coordinate = tuple[int, int]
Edge = tuple[Coordinate, Coordinate]


@dataclass(frozen=True)
class KameaPath:
    raw_values: tuple[int, ...]
    reduced_values: tuple[int, ...]
    coordinates: tuple[Coordinate, ...]

    @property
    def length(self) -> int:
        return len(self.coordinates)

    @property
    def edges(self) -> tuple[Edge, ...]:
        return tuple(
            (self.coordinates[i], self.coordinates[i + 1])
            for i in range(len(self.coordinates) - 1)
        )

    @property
    def node_counts(self) -> dict[Coordinate, int]:
        return dict(Counter(self.coordinates))

    @property
    def edge_counts(self) -> dict[Edge, int]:
        return dict(Counter(self.edges))

    @property
    def repeated_nodes(self) -> dict[Coordinate, int]:
        return {
            node: count
            for node, count in self.node_counts.items()
            if count > 1
        }

    @property
    def repeated_edges(self) -> dict[Edge, int]:
        return {
            edge: count
            for edge, count in self.edge_counts.items()
            if count > 1
        }