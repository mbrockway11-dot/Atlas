"""Tests for AtlasGraph activation."""

from __future__ import annotations

from atlas.core.compiler import compile_profile
from atlas.graph import (
    AtlasEdge,
    AtlasGraph,
    AtlasNode,
    build_graph_activation,
    build_temporal_graph,
)


def test_build_graph_activation_from_simple_graph():
    graph = AtlasGraph(
        nodes=(
            AtlasNode(id="a", kind="test", label="A", weight=2.0),
            AtlasNode(id="b", kind="test", label="B", weight=1.0),
        ),
        edges=(
            AtlasEdge(
                id="a-b",
                source="a",
                target="b",
                kind="link",
                weight=2.0,
            ),
        ),
    )

    activation = build_graph_activation(graph)
    payload = activation.to_dict()

    assert payload["summary"]["activated_node_count"] == 2
    assert payload["summary"]["activated_edge_count"] == 1
    assert payload["summary"]["activation_center"] == "a"
    assert payload["edge_activations"][0]["activation"] == 2.0


def test_build_graph_activation_from_temporal_graph():
    css = compile_profile("nikola_tesla").to_dict()
    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
    )

    activation = build_graph_activation(graph)
    payload = activation.to_dict()

    assert payload["summary"]["activated_node_count"] > 0
    assert payload["summary"]["activated_edge_count"] == graph.edge_count
    assert payload["summary"]["activation_center"] is not None
    assert payload["metadata"]["graph_type"] == "temporal_semantic_graph"
    assert payload["metadata"]["profile_key"] == "nikola_tesla"
