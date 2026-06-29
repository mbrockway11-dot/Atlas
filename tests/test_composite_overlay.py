from atlas.acf.builder import build_acf_profile
from atlas.overlay.composite_overlay import build_composite_overlay


def test_build_composite_overlay():
    acf = build_acf_profile("Michael Elvis Brockway")

    overlay = build_composite_overlay(acf)

    assert overlay["name"] == "Michael Elvis Brockway"
    assert overlay["layer_count"] == 21
    assert overlay["nodes"]
    assert overlay["edges"]

    summary = overlay["summary"]

    assert summary["composite_node_count"] > 0
    assert summary["composite_edge_count"] > 0
    assert "top_resonant_nodes" in summary
    assert "top_resonant_edges" in summary


def test_composite_overlay_has_cross_layer_fields():
    acf = build_acf_profile("Michael Elvis Brockway")

    overlay = build_composite_overlay(acf)
    node = overlay["nodes"][0]

    assert "layer_occurrences" in node
    assert "ciphers" in node
    assert "planets" in node
    assert "resonance_score" in node
    assert "is_triple_cipher" in node
    assert "is_multi_planet" in node