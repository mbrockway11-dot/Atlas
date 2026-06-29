from atlas.acf.builder import build_acf_profile
from atlas.graph import analyze_identity_graph, build_identity_graph_v2


def test_analyze_identity_graph():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    analyzed = analyze_identity_graph(graph)

    assert "analysis" in analyzed
    assert analyzed["analysis"]["component_count"] >= 1
    assert analyzed["analysis"]["largest_component_size"] > 0

    first_node = next(iter(analyzed["nodes"].values()))

    assert "degree" in first_node
    assert "in_degree" in first_node
    assert "out_degree" in first_node
    assert "neighbors" in first_node
    assert "component" in first_node
    assert "is_leaf" in first_node
    assert "is_hub" in first_node
    assert "is_articulation" in first_node


def test_analyze_identity_graph_edges():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    analyzed = analyze_identity_graph(graph)

    first_edge = next(iter(analyzed["edges"].values()))

    assert "is_bridge" in first_edge


def test_identity_graph_analysis_counts():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)

    analyzed = analyze_identity_graph(graph)
    analysis = analyzed["analysis"]

    assert "bridge_count" in analysis
    assert "articulation_point_count" in analysis
    assert "leaf_count" in analysis
    assert "hub_count" in analysis