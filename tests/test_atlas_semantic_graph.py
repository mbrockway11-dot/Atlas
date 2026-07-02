"""Tests for Atlas unified semantic graph primitives."""

from __future__ import annotations

from atlas.graph import AtlasEdge, AtlasGraph, AtlasNode


def test_atlas_graph_serializes_to_identity_graph_shape():
    graph = AtlasGraph(
        nodes=(
            AtlasNode(
                id="planet:sun",
                kind="planet",
                label="Sun",
                weight=2.0,
                attributes={"sign": "Cancer"},
            ),
            AtlasNode(
                id="planet:moon",
                kind="planet",
                label="Moon",
                weight=1.0,
                attributes={"sign": "Libra"},
            ),
        ),
        edges=(
            AtlasEdge(
                id="aspect:sun:moon",
                source="planet:sun",
                target="planet:moon",
                kind="aspect",
                weight=1.0,
                attributes={"aspect_type": "7th"},
            ),
        ),
        metadata={"graph_type": "semantic_test"},
    )

    payload = graph.to_dict()

    assert graph.node_count == 2
    assert graph.edge_count == 1
    assert payload["summary"]["node_count"] == 2
    assert payload["summary"]["edge_count"] == 1
    assert payload["nodes"]["planet:sun"]["weight"] == 2.0
    assert payload["edges"]["aspect:sun:moon"]["kind"] == "aspect"
    assert payload["metadata"]["graph_type"] == "semantic_test"
