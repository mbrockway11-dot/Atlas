from atlas.fingerprint import build_identity_fingerprint
from atlas.graph.attractor import extract_structural_attractor


def test_structural_attractor_exists_from_fingerprint():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    attractor = fingerprint["structural_attractor"]

    assert attractor["version"] == "1.0"
    assert attractor["definition"]
    assert attractor["selection_rule"]
    assert "nodes" in attractor
    assert "edges" in attractor
    assert "graph" in attractor
    assert "summary" in attractor
    assert "components_considered" in attractor


def test_structural_attractor_is_subset_of_reduced_graph():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    reduced_graph = fingerprint["reduced_identity_graph"]
    attractor = fingerprint["structural_attractor"]

    reduced_nodes = set(reduced_graph["nodes"])
    reduced_edges = set(reduced_graph["edges"])

    attractor_nodes = set(attractor["nodes"])
    attractor_edges = set(attractor["edges"])

    assert attractor_nodes <= reduced_nodes
    assert attractor_edges <= reduced_edges


def test_structural_attractor_edges_only_use_attractor_nodes():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    attractor = fingerprint["structural_attractor"]
    attractor_nodes = set(attractor["nodes"])

    for edge in attractor["edges"].values():
        assert edge["source"] in attractor_nodes
        assert edge["target"] in attractor_nodes


def test_structural_attractor_summary_metrics_are_coherent():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    attractor = fingerprint["structural_attractor"]
    summary = attractor["summary"]

    assert summary["node_count"] == len(attractor["nodes"])
    assert summary["edge_count"] == len(attractor["edges"])

    assert summary["source_node_count"] >= summary["node_count"]
    assert summary["source_edge_count"] >= summary["edge_count"]

    assert 0.0 <= summary["node_retention_ratio"] <= 1.0
    assert 0.0 <= summary["edge_retention_ratio"] <= 1.0
    assert 0.0 <= summary["mean_node_coherence"] <= 1.0
    assert 0.0 <= summary["mean_edge_coherence"] <= 1.0
    assert 0.0 <= summary["density"] <= 1.0

    assert summary["diameter"] >= 0
    assert summary["radius"] >= 0
    assert summary["average_path_length"] >= 0.0
    assert summary["component_count_considered"] >= 0


def test_structural_attractor_is_deterministic():
    first = build_identity_fingerprint("Michael Elvis Brockway")
    second = build_identity_fingerprint("Michael Elvis Brockway")

    assert first["structural_attractor"]["summary"] == second["structural_attractor"]["summary"]
    assert first["structural_attractor"]["nodes"] == second["structural_attractor"]["nodes"]
    assert first["structural_attractor"]["edges"] == second["structural_attractor"]["edges"]


def test_structural_attractor_empty_graph_does_not_crash():
    graph = {
        "name": "Empty",
        "version": "2.0",
        "nodes": {},
        "edges": {},
        "construction_passes": [],
        "summary": {},
    }

    attractor = extract_structural_attractor(graph)

    assert attractor["version"] == "1.0"
    assert attractor["nodes"] == {}
    assert attractor["edges"] == {}
    assert attractor["summary"]["node_count"] == 0
    assert attractor["summary"]["edge_count"] == 0
    assert attractor["summary"]["node_retention_ratio"] == 0.0
    assert attractor["summary"]["edge_retention_ratio"] == 0.0