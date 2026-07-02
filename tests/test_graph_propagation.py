"""Tests for AtlasGraph activation propagation."""

from __future__ import annotations

import pytest

from atlas.core.compiler import compile_profile
from atlas.graph import (
    AtlasEdge,
    AtlasGraph,
    AtlasNode,
    build_graph_activation,
    build_temporal_graph,
    propagate_activation,
)


def test_propagate_activation_on_simple_graph():
    graph = AtlasGraph(
        nodes=(
            AtlasNode(id="a", kind="test", label="A", weight=2.0),
            AtlasNode(id="b", kind="test", label="B", weight=0.0),
        ),
        edges=(
            AtlasEdge(
                id="a-b",
                source="a",
                target="b",
                kind="link",
                weight=1.0,
            ),
        ),
    )

    activation = build_graph_activation(graph)
    result = propagate_activation(
        graph=graph,
        activation=activation,
        iterations=1,
        decay=0.5,
    )

    payload = result.to_dict()

    assert payload["summary"]["propagation_status"] == "computed"
    assert payload["summary"]["top_node"] == "a"
    assert result.node_scores["a"] == 1.0
    assert result.node_scores["b"] > 0


def test_propagate_activation_rejects_invalid_inputs():
    graph = AtlasGraph(nodes=(), edges=())
    activation = build_graph_activation(graph)

    with pytest.raises(ValueError, match="iterations"):
        propagate_activation(
            graph=graph,
            activation=activation,
            iterations=-1,
        )

    with pytest.raises(ValueError, match="decay"):
        propagate_activation(
            graph=graph,
            activation=activation,
            decay=-0.1,
        )


def test_propagate_activation_on_temporal_graph():
    css = compile_profile("nikola_tesla").to_dict()
    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
    )
    activation = build_graph_activation(graph)

    result = propagate_activation(
        graph=graph,
        activation=activation,
        iterations=2,
        decay=0.5,
    )

    assert result.summary["propagation_status"] == "computed"
    assert result.summary["node_count"] == graph.node_count
    assert result.summary["top_node"] is not None
    assert len(result.top_nodes) <= 10
