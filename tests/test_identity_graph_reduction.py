from atlas.acf.builder import build_acf_profile
from atlas.graph import build_identity_graph_v2, reduce_identity_graph


def test_reduce_identity_graph():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    reduced = reduce_identity_graph(graph)

    assert "reduction" in reduced
    assert reduced["reduction"]["raw_node_count"] == len(graph["nodes"])
    assert reduced["reduction"]["raw_edge_count"] == len(graph["edges"])

    assert reduced["reduction"]["reduced_node_count"] <= len(graph["nodes"])
    assert reduced["reduction"]["reduced_edge_count"] <= len(graph["edges"])

    assert "analysis" in reduced
    assert "history" in reduced["reduction"]


def test_reduction_does_not_mutate_original_graph():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    original_node_count = len(graph["nodes"])
    original_edge_count = len(graph["edges"])

    reduce_identity_graph(graph)

    assert len(graph["nodes"]) == original_node_count
    assert len(graph["edges"]) == original_edge_count


def test_reduction_converges_or_stops_safely():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    reduced = reduce_identity_graph(graph, max_iterations=5)

    assert reduced["reduction"]["iterations"] <= 5
    assert "converged" in reduced["reduction"]