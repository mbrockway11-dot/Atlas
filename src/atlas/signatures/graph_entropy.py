"""Graph entropy utilities."""

import math

from atlas.topology.graph import TopologyGraph


def node_weight_entropy(graph: TopologyGraph) -> float:
    """Compute normalized entropy of node weight distribution."""
    weights = list(graph.node_weights.values())

    if not weights:
        return 0.0

    total = sum(weights)

    if total == 0:
        return 0.0

    probabilities = [weight / total for weight in weights if weight > 0]

    if len(probabilities) <= 1:
        return 0.0

    entropy = -sum(probability * math.log2(probability) for probability in probabilities)
    max_entropy = math.log2(len(probabilities))

    if max_entropy == 0:
        return 0.0

    return entropy / max_entropy