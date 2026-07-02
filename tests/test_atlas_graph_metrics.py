"""Tests for AtlasGraph metrics."""

from __future__ import annotations

from atlas.graph import (
    AtlasEdge,
    AtlasGraph,
    AtlasNode,
    compute_graph_metrics,
)


def test_compute_graph_metrics_for_semantic_graph():
    graph = AtlasGraph(
        nodes=(
            AtlasNode(id="a", kind="test", label="A"),
            AtlasNode(id="b", kind="test", label="B"),
            AtlasNode(id="c", kind="test", label="C"),
        ),
        edges=(
            AtlasEdge(id="a-b", source="a", target="b", kind="link"),
            AtlasEdge(id="a-c", source="a", target="c", kind="link"),
        ),
    )

    metrics = compute_graph_metrics(graph)
    payload = metrics.to_dict()

    assert metrics.node_count == 3
    assert metrics.edge_count == 2
    assert metrics.max_degree == 2
    assert metrics.hub_nodes == ("a",)
    assert metrics.isolated_nodes == ()
    assert metrics.degree_by_node["a"] == 2
    assert payload["version"] == "0.1"


def test_compute_graph_metrics_detects_isolated_nodes():
    graph = AtlasGraph(
        nodes=(
            AtlasNode(id="a", kind="test", label="A"),
            AtlasNode(id="b", kind="test", label="B"),
        ),
        edges=(),
    )

    metrics = compute_graph_metrics(graph)

    assert metrics.node_count == 2
    assert metrics.edge_count == 0
    assert metrics.max_degree == 0
    assert metrics.hub_nodes == ()
    assert metrics.isolated_nodes == ("a", "b")
