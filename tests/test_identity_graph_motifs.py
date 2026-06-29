from atlas.acf.builder import build_acf_profile
from atlas.graph import build_identity_graph_v2, compute_coherence_field
from atlas.motifs import detect_identity_graph_motifs


def test_detect_identity_graph_motifs():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)
    coherent = compute_coherence_field(graph)

    result = detect_identity_graph_motifs(coherent)

    assert "motifs" in result
    assert "summary" in result

    assert "chains" in result["motifs"]
    assert "hubs" in result["motifs"]
    assert "leaves" in result["motifs"]
    assert "bridges" in result["motifs"]
    assert "articulations" in result["motifs"]
    assert "reciprocal_pairs" in result["motifs"]

    assert "total_motifs" in result["summary"]
    assert "counts" in result["summary"]
    assert "dominant_motif" in result["summary"]


def test_identity_motif_records_have_structure():
    acf = build_acf_profile("Michael Elvis Brockway")
    graph = build_identity_graph_v2(acf)
    coherent = compute_coherence_field(graph)

    result = detect_identity_graph_motifs(coherent)

    all_motifs = []
    for records in result["motifs"].values():
        all_motifs.extend(records)

    assert all_motifs

    motif = all_motifs[0]

    assert "type" in motif