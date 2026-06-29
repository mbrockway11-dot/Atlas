"""Layer-level structural reduction metrics for Atlas research rows."""

from __future__ import annotations

from math import log2
from typing import Any

from atlas.research.coherence_metrics import build_layer_coherence_metrics
from atlas.research.graph_metrics import (
    build_undirected_adjacency,
    connected_component_sizes,
    safe_ratio,
)


def build_layer_reduction_metrics(layer: dict[str, Any]) -> dict[str, Any]:
    """Build reduction summary metrics for one construction layer."""
    graph = build_layer_reduction_graph(layer)
    initial_node_count = len(graph["nodes"])
    initial_edge_count = len(graph["edges"])

    if initial_node_count == 0:
        return empty_reduction_metrics()

    history = reduce_graph_iteratively(graph)

    final_state = history[-1] if history else graph_state(graph, 0, False)
    collapse_iteration = find_collapse_iteration(history)

    surviving_node_ratio = safe_ratio(
        final_state["node_count"],
        initial_node_count,
    )
    surviving_edge_ratio = safe_ratio(
        final_state["edge_count"],
        initial_edge_count,
    )

    return {
        "reduction_iterations": len(history),
        "surviving_node_ratio": surviving_node_ratio,
        "surviving_edge_ratio": surviving_edge_ratio,
        "collapse_iteration": collapse_iteration,
        "collapse_ratio": safe_ratio(collapse_iteration, len(history)),
        "core_survival_score": core_survival_score(history),
        "topology_stability": topology_stability(history),
        "reduction_entropy": reduction_entropy(history),
        "node_survival_auc": node_survival_auc(history),
        "edge_survival_auc": edge_survival_auc(history),
        "edge_loss_rate": edge_loss_rate(history),
        "collapse_slope": collapse_slope(history),
    }


def build_layer_reduction_graph(layer: dict[str, Any]) -> dict[str, Any]:
    """Build a simple graph object for reduction from one layer."""
    path = layer["features"]["path_views"]["analysis_path"]
    visits = path["visit_history"]["visits"]
    node_weights = path["node_weights"]

    nodes = {
        str(visit["node"])
        for visit in visits
    }

    directed_edges = [
        (
            str(source["node"]),
            str(target["node"]),
        )
        for source, target in zip(visits[:-1], visits[1:])
    ]

    edges = {
        tuple(sorted((source, target)))
        for source, target in directed_edges
        if source != target
    }

    coherence = build_layer_coherence_metrics(layer)

    node_scores = estimate_node_scores(
        nodes=nodes,
        node_weights=node_weights,
        edges=edges,
    )

    return {
        "nodes": set(nodes),
        "edges": set(edges),
        "node_scores": node_scores,
        "graph_coherence": coherence["graph_coherence"],
    }


def estimate_node_scores(
    *,
    nodes: set[str],
    node_weights: dict[Any, Any],
    edges: set[tuple[str, str]],
) -> dict[str, float]:
    """Estimate node importance for deterministic reduction."""
    adjacency = adjacency_from_edges(nodes, edges)
    max_weight = max([float(value) for value in node_weights.values()], default=1.0)
    max_degree = max([len(adjacency[node]) for node in nodes], default=1)

    scores = {}

    for node in nodes:
        weight = float(node_weights.get(node, node_weights.get(int_or_self(node), 0)))
        degree = len(adjacency[node])

        weight_score = safe_ratio(weight, max_weight)
        degree_score = safe_ratio(degree, max_degree)

        scores[node] = (
            weight_score * 0.60
            + degree_score * 0.40
        )

    return scores


def reduce_graph_iteratively(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Iteratively remove the weakest node while recording full trajectory."""
    working_nodes = set(graph["nodes"])
    working_edges = set(graph["edges"])
    node_scores = dict(graph["node_scores"])

    history = []
    iteration = 0

    while working_nodes:
        state = graph_state_from_parts(
            nodes=working_nodes,
            edges=working_edges,
            iteration=iteration,
            collapsed=is_collapsed(working_nodes, working_edges),
            removed_node=None,
            removed_node_score=None,
        )
        history.append(state)

        if len(working_nodes) <= 1:
            break

        weakest_node = min(
            working_nodes,
            key=lambda node: (
                node_scores.get(node, 0.0),
                node,
            ),
        )

        weakest_score = node_scores.get(weakest_node, 0.0)

        working_nodes.remove(weakest_node)
        working_edges = {
            edge
            for edge in working_edges
            if weakest_node not in edge
        }

        iteration += 1

        post_state = graph_state_from_parts(
            nodes=working_nodes,
            edges=working_edges,
            iteration=iteration,
            collapsed=is_collapsed(working_nodes, working_edges),
            removed_node=weakest_node,
            removed_node_score=weakest_score,
        )
        history.append(post_state)

        if post_state["collapsed"]:
            break

    return dedupe_iteration_history(history)


def dedupe_iteration_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one state per iteration, preferring states with removal metadata."""
    indexed: dict[int, dict[str, Any]] = {}

    for state in history:
        iteration = int(state["iteration"])

        if iteration not in indexed:
            indexed[iteration] = state
            continue

        if state.get("removed_node") is not None:
            indexed[iteration] = state

    return [
        indexed[key]
        for key in sorted(indexed)
    ]


def graph_state(graph: dict[str, Any], iteration: int, collapsed: bool) -> dict[str, Any]:
    """Return graph state from graph object."""
    return graph_state_from_parts(
        nodes=graph["nodes"],
        edges=graph["edges"],
        iteration=iteration,
        collapsed=collapsed,
        removed_node=None,
        removed_node_score=None,
    )


def graph_state_from_parts(
    *,
    nodes: set[str],
    edges: set[tuple[str, str]],
    iteration: int,
    collapsed: bool,
    removed_node: str | None,
    removed_node_score: float | None,
) -> dict[str, Any]:
    """Return graph state from node and edge sets."""
    adjacency = adjacency_from_edges(nodes, edges)
    component_sizes = connected_component_sizes(nodes, adjacency)

    return {
        "iteration": iteration,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "component_count": len(component_sizes),
        "largest_component_size": max(component_sizes, default=0),
        "collapsed": collapsed,
        "removed_node": removed_node,
        "removed_node_score": removed_node_score,
    }


def adjacency_from_edges(
    nodes: set[str],
    edges: set[tuple[str, str]],
) -> dict[str, set[str]]:
    """Build adjacency from undirected edge set."""
    return build_undirected_adjacency(
        nodes=nodes,
        directed_edges=list(edges),
    )


def is_collapsed(
    nodes: set[str],
    edges: set[tuple[str, str]],
) -> bool:
    """Return whether the graph has structurally collapsed."""
    if len(nodes) <= 1:
        return True

    adjacency = adjacency_from_edges(nodes, edges)
    component_sizes = connected_component_sizes(nodes, adjacency)

    if not component_sizes:
        return True

    return len(component_sizes) > 1


def find_collapse_iteration(history: list[dict[str, Any]]) -> int:
    """Return first collapse iteration, or 0 if no collapse occurs."""
    for state in history:
        if state["collapsed"]:
            return int(state["iteration"])

    return 0


def core_survival_score(history: list[dict[str, Any]]) -> float:
    """Score how much structure survives across reduction."""
    if not history:
        return 0.0

    initial_nodes = history[0]["node_count"]

    if initial_nodes == 0:
        return 0.0

    survival_values = [
        safe_ratio(state["largest_component_size"], initial_nodes)
        for state in history
    ]

    return sum(survival_values) / len(survival_values)


def topology_stability(history: list[dict[str, Any]]) -> float:
    """Score how long topology remains uncollapsed."""
    if not history:
        return 0.0

    stable_states = [
        state
        for state in history
        if not state["collapsed"]
    ]

    return safe_ratio(len(stable_states), len(history))


def reduction_entropy(history: list[dict[str, Any]]) -> float:
    """Compute entropy of node survival trajectory."""
    if not history:
        return 0.0

    counts = [
        state["node_count"]
        for state in history
        if state["node_count"] > 0
    ]

    total = sum(counts)

    if total == 0:
        return 0.0

    probabilities = [
        count / total
        for count in counts
    ]

    entropy = -sum(
        probability * log2(probability)
        for probability in probabilities
        if probability > 0
    )

    max_entropy = log2(len(probabilities)) if len(probabilities) > 1 else 1.0

    return safe_ratio(entropy, max_entropy)


def node_survival_auc(history: list[dict[str, Any]]) -> float:
    """Compute normalized area under the node survival curve."""
    if not history:
        return 0.0

    initial_nodes = history[0]["node_count"]

    if initial_nodes == 0:
        return 0.0

    ratios = [
        safe_ratio(state["node_count"], initial_nodes)
        for state in history
    ]

    return sum(ratios) / len(ratios)


def edge_survival_auc(history: list[dict[str, Any]]) -> float:
    """Compute normalized area under the edge survival curve."""
    if not history:
        return 0.0

    initial_edges = history[0]["edge_count"]

    if initial_edges == 0:
        return 0.0

    ratios = [
        safe_ratio(state["edge_count"], initial_edges)
        for state in history
    ]

    return sum(ratios) / len(ratios)


def edge_loss_rate(history: list[dict[str, Any]]) -> float:
    """Compute average edge loss per reduction step."""
    if len(history) < 2:
        return 0.0

    initial_edges = history[0]["edge_count"]

    if initial_edges == 0:
        return 0.0

    losses = []

    for previous, current in zip(history[:-1], history[1:]):
        loss = previous["edge_count"] - current["edge_count"]
        losses.append(max(0, loss))

    return safe_ratio(sum(losses), initial_edges * len(losses))


def collapse_slope(history: list[dict[str, Any]]) -> float:
    """Estimate how sharply the graph collapses."""
    if len(history) < 2:
        return 0.0

    initial_largest = history[0]["largest_component_size"]

    if initial_largest == 0:
        return 0.0

    start_ratio = 1.0
    end_ratio = safe_ratio(history[-1]["largest_component_size"], initial_largest)
    steps = max(1, history[-1]["iteration"] - history[0]["iteration"])

    return safe_ratio(start_ratio - end_ratio, steps)


def empty_reduction_metrics() -> dict[str, Any]:
    """Return empty reduction metrics."""
    return {
        "reduction_iterations": 0,
        "surviving_node_ratio": 0.0,
        "surviving_edge_ratio": 0.0,
        "collapse_iteration": 0,
        "collapse_ratio": 0.0,
        "core_survival_score": 0.0,
        "topology_stability": 0.0,
        "reduction_entropy": 0.0,
        "node_survival_auc": 0.0,
        "edge_survival_auc": 0.0,
        "edge_loss_rate": 0.0,
        "collapse_slope": 0.0,
    }


def int_or_self(value: str) -> int | str:
    """Convert numeric strings to int when possible."""
    try:
        return int(value)
    except ValueError:
        return value