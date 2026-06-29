from atlas.acf.builder import build_acf_profile
from atlas.graph import build_identity_graph_v2


def test_build_identity_graph_v2():
    acf = build_acf_profile("Michael Elvis Brockway")

    graph = build_identity_graph_v2(acf)

    assert graph["name"] == "Michael Elvis Brockway"
    assert graph["version"] == "2.0"

    assert graph["nodes"]
    assert graph["edges"]
    assert graph["construction_passes"]

    assert graph["summary"]["construction_pass_count"] == 21
    assert graph["summary"]["node_count"] > 0
    assert graph["summary"]["edge_count"] > 0


def test_identity_graph_v2_merges_nodes():
    acf = build_acf_profile("Michael Elvis Brockway")

    graph = build_identity_graph_v2(acf)

    node_ids = list(graph["nodes"].keys())

    assert len(node_ids) == len(set(node_ids))

    node = graph["summary"]["top_nodes"][0]

    assert "weight" in node
    assert "construction_history" in node
    assert "ciphers" in node
    assert "planets" in node
    assert "cipher_count" in node
    assert "planet_count" in node


def test_identity_graph_v2_merges_edges():
    acf = build_acf_profile("Michael Elvis Brockway")

    graph = build_identity_graph_v2(acf)

    edge_ids = list(graph["edges"].keys())

    assert len(edge_ids) == len(set(edge_ids))

    edge = graph["summary"]["top_edges"][0]

    assert "source" in edge
    assert "target" in edge
    assert "weight" in edge
    assert "construction_history" in edge
    assert "ciphers" in edge
    assert "planets" in edge