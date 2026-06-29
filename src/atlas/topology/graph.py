"""Domain-agnostic topology graph objects."""

from dataclasses import dataclass, field


Node = tuple[int, int]
Edge = tuple[Node, Node]


@dataclass(frozen=True)
class TopologyGraph:
    """Immutable directed weighted graph."""

    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    node_weights: dict[Node, int] = field(default_factory=dict)
    edge_weights: dict[Edge, int] = field(default_factory=dict)

    @property
    def node_count(self) -> int:
        """Total number of unique active nodes."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Total number of unique active edges."""
        return len(self.edges)

    @property
    def total_node_weight(self) -> int:
        """Total accumulated node weight."""
        return sum(self.node_weights.values())

    @property
    def total_edge_weight(self) -> int:
        """Total accumulated edge weight."""
        return sum(self.edge_weights.values())

    def has_node(self, node: Node) -> bool:
        """Return True if the graph contains a node."""
        return node in self.nodes

    def has_edge(self, edge: Edge) -> bool:
        """Return True if the graph contains an edge."""
        return edge in self.edges

    def outgoing_edges(self, node: Node) -> tuple[Edge, ...]:
        """Return all outgoing edges from a node."""
        return tuple(edge for edge in self.edges if edge[0] == node)

    def incoming_edges(self, node: Node) -> tuple[Edge, ...]:
        """Return all incoming edges to a node."""
        return tuple(edge for edge in self.edges if edge[1] == node)