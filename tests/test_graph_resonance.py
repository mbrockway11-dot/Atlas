"""Tests for AtlasGraph resonance."""

from __future__ import annotations

from atlas.core.compiler import compile_profile
from atlas.graph import (
    AtlasEdge,
    AtlasGraph,
    AtlasNode,
    build_graph_activation,
    build_temporal_graph,
    compute_graph_resonance,
    propagate_activation,
)


def _propagate(graph: AtlasGraph):
    activation = build_graph_activation(graph)
    return propagate_activation(
        graph=graph,
        activation=activation,
        iterations=1,
        decay=0.5,
    )


def test_graph_resonance_identical_fields_score_one():
    graph = AtlasGraph(
        nodes=(
            AtlasNode(id="a", kind="test", label="A", weight=1.0),
            AtlasNode(id="b", kind="test", label="B", weight=1.0),
        ),
        edges=(
            AtlasEdge(id="a-b", source="a", target="b", kind="link"),
        ),
    )

    left = _propagate(graph)
    right = _propagate(graph)

    resonance = compute_graph_resonance(left, right)

    assert resonance.overall_score == 1.0
    assert resonance.node_overlap == 1.0
    assert resonance.activation_overlap == 1.0
    assert resonance.summary["resonance_status"] == "computed"


def test_graph_resonance_disjoint_fields_score_zero_node_overlap():
    left_graph = AtlasGraph(
        nodes=(AtlasNode(id="a", kind="test", label="A"),),
        edges=(),
    )
    right_graph = AtlasGraph(
        nodes=(AtlasNode(id="b", kind="test", label="B"),),
        edges=(),
    )

    left = _propagate(left_graph)
    right = _propagate(right_graph)

    resonance = compute_graph_resonance(left, right)

    assert resonance.node_overlap == 0.0
    assert resonance.activation_overlap == 0.0
    assert resonance.overall_score == 0.0
    assert resonance.unique_left == ("a",)
    assert resonance.unique_right == ("b",)


def test_graph_resonance_is_symmetric():
    left_graph = AtlasGraph(
        nodes=(
            AtlasNode(id="a", kind="test", label="A"),
            AtlasNode(id="b", kind="test", label="B"),
        ),
        edges=(),
    )
    right_graph = AtlasGraph(
        nodes=(
            AtlasNode(id="b", kind="test", label="B"),
            AtlasNode(id="c", kind="test", label="C"),
        ),
        edges=(),
    )

    left = _propagate(left_graph)
    right = _propagate(right_graph)

    ab = compute_graph_resonance(left, right)
    ba = compute_graph_resonance(right, left)

    assert ab.overall_score == ba.overall_score
    assert ab.node_overlap == ba.node_overlap
    assert ab.activation_overlap == ba.activation_overlap


def test_graph_resonance_temporal_graph_against_itself():
    css = compile_profile("nikola_tesla").to_dict()
    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
    )

    propagation = _propagate(graph)

    resonance = compute_graph_resonance(
        propagation,
        propagation,
    )

    payload = resonance.to_dict()

    assert payload["overall_score"] == 1.0
    assert payload["summary"]["shared_node_count"] == graph.node_count
    assert payload["summary"]["resonance_status"] == "computed"
