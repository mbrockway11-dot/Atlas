from atlas.identity import build_identity_graph, build_identity_layers


def test_build_identity_layers():
    layers = build_identity_layers("Michael Elvis Brockway")

    assert len(layers) == 21
    assert "layer_id" in layers[0]
    assert "cipher" in layers[0]
    assert "planet" in layers[0]
    assert "features" in layers[0]
    assert "subtype" in layers[0]


def test_build_identity_graph():
    graph = build_identity_graph("Michael Elvis Brockway")

    assert graph["name"] == "Michael Elvis Brockway"
    assert graph["layer_count"] == 21
    assert len(graph["layers"]) == 21

    # Complete undirected graph over 21 layers = 21 * 20 / 2 = 210 edges.
    assert len(graph["layer_edges"]) == 210

    assert "summary" in graph
    assert "strongest_layer" in graph["summary"]
    assert "average_inter_layer_similarity" in graph["summary"]