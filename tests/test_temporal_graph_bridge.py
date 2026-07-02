"""Tests for temporal CSS to AtlasGraph bridge."""

from __future__ import annotations

from atlas.core.compiler import compile_profile
from atlas.graph import build_temporal_graph
from atlas.temporal_runtime import TemporalRuntimeEngine


def test_build_temporal_graph_from_compiled_css():
    css = compile_profile("nikola_tesla").to_dict()

    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
    )

    payload = graph.to_dict()

    assert graph.node_count > 0
    assert graph.edge_count > 0
    assert payload["metadata"]["graph_type"] == "temporal_semantic_graph"
    assert payload["metadata"]["profile_key"] == "nikola_tesla"
    assert "natal:planet:Sun" in payload["nodes"]
    assert any(
        edge["kind"] == "transit_contact"
        for edge in payload["edges"].values()
    )


def test_build_temporal_graph_includes_runtime_metadata():
    css = compile_profile("nikola_tesla").to_dict()
    runtime_result = TemporalRuntimeEngine().evaluate(
        profile_key="nikola_tesla",
        css=css,
        evaluation_date="2026-07-02",
    )

    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
        runtime_result=runtime_result.to_dict(),
    )

    payload = graph.to_dict()

    assert payload["metadata"]["runtime"]["runtime"] == "atlas.temporal_runtime"
    assert payload["metadata"]["runtime_scoring"]["score_status"] == "computed"
