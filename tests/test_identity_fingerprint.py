from atlas.fingerprint import build_identity_fingerprint


def test_build_identity_fingerprint():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    assert "raw_identity_graph" in fingerprint
    assert "analyzed_identity_graph" in fingerprint
    assert "coherence_field" in fingerprint
    assert "reduced_identity_graph" in fingerprint
    assert "motifs" in fingerprint
    assert "structural_attractor" in fingerprint
    assert "classification" in fingerprint
    assert "source_acf" in fingerprint

    assert fingerprint["raw_identity_graph"]["version"] == "2.0"
    assert fingerprint["classification"]["version"] == "2.0"
    assert fingerprint["classification"]["scale"] == "Individual"
    assert fingerprint["classification"]["population_free"] is True


def test_identity_fingerprint_pipeline_counts_are_coherent():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    raw_nodes = len(fingerprint["raw_identity_graph"]["nodes"])
    analyzed_nodes = len(fingerprint["analyzed_identity_graph"]["nodes"])
    coherence_nodes = len(fingerprint["coherence_field"]["nodes"])
    reduced_nodes = len(fingerprint["reduced_identity_graph"]["nodes"])
    attractor_nodes = fingerprint["structural_attractor"]["summary"]["node_count"]

    raw_edges = len(fingerprint["raw_identity_graph"]["edges"])
    analyzed_edges = len(fingerprint["analyzed_identity_graph"]["edges"])
    coherence_edges = len(fingerprint["coherence_field"]["edges"])
    reduced_edges = len(fingerprint["reduced_identity_graph"]["edges"])
    attractor_edges = fingerprint["structural_attractor"]["summary"]["edge_count"]

    assert raw_nodes == analyzed_nodes
    assert analyzed_nodes == coherence_nodes
    assert reduced_nodes <= raw_nodes
    assert attractor_nodes <= reduced_nodes

    assert raw_edges == analyzed_edges
    assert analyzed_edges == coherence_edges
    assert reduced_edges <= raw_edges
    assert attractor_edges <= reduced_edges


def test_identity_fingerprint_structural_attractor():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    attractor = fingerprint["structural_attractor"]

    assert attractor["version"] == "1.0"
    assert attractor["definition"]
    assert attractor["selection_rule"]
    assert "nodes" in attractor
    assert "edges" in attractor
    assert "summary" in attractor

    summary = attractor["summary"]

    assert summary["node_count"] >= 0
    assert summary["edge_count"] >= 0
    assert 0.0 <= summary["node_retention_ratio"] <= 1.0
    assert 0.0 <= summary["edge_retention_ratio"] <= 1.0
    assert 0.0 <= summary["density"] <= 1.0


def test_identity_fingerprint_classification_is_individual_only():
    fingerprint = build_identity_fingerprint("Michael Elvis Brockway")

    classification = fingerprint["classification"]

    assert classification["scale"] == "Individual"
    assert classification["population_free"] is True
    assert "structural_state" in classification
    assert "functional_role" in classification
    assert "reduction_profile" in classification
    assert "drivers" in classification
    assert "summary" in classification


def test_identity_fingerprint_is_deterministic():
    first = build_identity_fingerprint("Michael Elvis Brockway").to_dict()
    second = build_identity_fingerprint("Michael Elvis Brockway").to_dict()

    assert first["classification"] == second["classification"]
    assert first["structural_attractor"]["summary"] == second["structural_attractor"]["summary"]
    assert first["reduced_identity_graph"]["summary"] == second["reduced_identity_graph"]["summary"]