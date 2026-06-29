from atlas.acf.builder import build_acf_profile
from atlas.graph import (
    build_identity_graph_v2,
    classify_coherence,
    compute_coherence_field,
)


def test_classify_coherence():
    assert classify_coherence(0.80) == "core"
    assert classify_coherence(0.50) == "adaptive"
    assert classify_coherence(0.10) == "peripheral"


def test_compute_coherence_field():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    coherent = compute_coherence_field(graph)

    assert "coherence" in coherent
    assert coherent["coherence"]["node_count"] == len(coherent["nodes"])
    assert coherent["coherence"]["edge_count"] == len(coherent["edges"])

    node = next(iter(coherent["nodes"].values()))
    edge = next(iter(coherent["edges"].values()))

    assert "coherence" in node
    assert "score" in node["coherence"]
    assert "region" in node["coherence"]

    assert "coherence" in edge
    assert "score" in edge["coherence"]
    assert "region" in edge["coherence"]


def test_coherence_summary_has_regions():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    coherent = compute_coherence_field(graph)
    summary = coherent["coherence"]

    assert "core_node_count" in summary
    assert "adaptive_node_count" in summary
    assert "peripheral_node_count" in summary
    assert "top_nodes" in summary
    assert "top_edges" in summary