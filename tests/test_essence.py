from atlas.essence.builder import build_essence_graph
from atlas.essence.profile import build_essence_profile


def test_build_essence_graph():
    graph = build_essence_graph("Michael Elvis Brockway")

    assert graph.node_count > 0
    assert graph.edge_count > 0
    assert graph.total_node_weight > 20
    assert graph.total_edge_weight > 20


def test_build_essence_profile(tmp_path):
    paths = build_essence_profile("Michael Elvis Brockway", tmp_path)

    assert paths["json"].exists()
    assert paths["svg"].exists()