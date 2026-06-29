from atlas.identity import build_identity_graph, build_identity_persistence


def test_build_identity_persistence():
    identity_graph = build_identity_graph("Michael Elvis Brockway")
    persistence = build_identity_persistence(identity_graph, threshold=0.50)

    assert persistence["name"] == "Michael Elvis Brockway"
    assert persistence["layer_count"] == 21
    assert persistence["threshold"] == 0.50

    assert "persistent_nodes" in persistence
    assert "residual_nodes" in persistence
    assert "persistent_edges" in persistence
    assert "residual_edges" in persistence
    assert "summary" in persistence

    assert persistence["summary"]["layer_count"] == 21
    assert "node_persistence_ratio" in persistence["summary"]
    assert "edge_persistence_ratio" in persistence["summary"]


def test_persistent_nodes_include_trajectory_metrics():
    identity_graph = build_identity_graph("Michael Elvis Brockway")
    persistence = build_identity_persistence(identity_graph, threshold=0.10)

    assert persistence["persistent_nodes"]

    node = persistence["persistent_nodes"][0]

    assert "average_depth" in node
    assert "max_depth" in node
    assert "average_revisit_interval" in node