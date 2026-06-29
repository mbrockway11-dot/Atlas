from atlas.acf.builder import build_acf_profile, export_acf_profile


def test_build_acf_profile():
    acf = build_acf_profile("Michael Elvis Brockway")

    assert acf["metadata"]["atlas_codex_format"] == "1.0"
    assert acf["metadata"]["entity_type"] == "person"
    assert acf["identity"]["name"] == "Michael Elvis Brockway"

    assert "birth_data" in acf["identity"]
    assert acf["identity"]["birth_data"]["confidence"] == "unknown"

    assert "profile_interpretation" in acf
    assert "essence" in acf
    assert "invariant_analysis" in acf
    assert "identity_graph" in acf
    assert "identity_persistence" in acf
    assert "planetary_matrix" in acf
    assert "cipher_matrix" in acf
    assert "analyses" in acf
    assert "interpretation_seed" in acf

    assert len(acf["analyses"]) == 21
    assert acf["essence"]["graph_summary"]["node_count"] > 0
    assert acf["interpretation_seed"]["facts"]

    classification = acf["essence"]["classification"]

    assert "function" in classification
    assert "expression" in classification
    assert "state" in classification
    assert "scale" in classification
    assert "summary" in classification

    assert "meanings" in classification
    assert "function" in classification["meanings"]
    assert "expression" in classification["meanings"]
    assert "state" in classification["meanings"]

    invariant = acf["invariant_analysis"]

    assert invariant["analysis_count"] == 21
    assert "subtype" in invariant
    assert "top_kameas" in invariant
    assert "ranked_kameas" in invariant
    assert "planetary_weights" in invariant
    assert "planetary_contrast" in invariant
    assert "structural_summary" in invariant

    identity_graph = acf["identity_graph"]

    assert identity_graph["layer_count"] == 21
    assert len(identity_graph["layers"]) == 21
    assert len(identity_graph["layer_edges"]) == 210
    assert "summary" in identity_graph

    identity_persistence = acf["identity_persistence"]

    assert identity_persistence["layer_count"] == 21
    assert "persistent_nodes" in identity_persistence
    assert "residual_nodes" in identity_persistence
    assert "persistent_edges" in identity_persistence
    assert "residual_edges" in identity_persistence
    assert "summary" in identity_persistence


def test_export_acf_profile(tmp_path):
    output_path = tmp_path / "profile.acf.json"

    result_path = export_acf_profile(
        name="Michael Elvis Brockway",
        output_path=output_path,
    )

    assert result_path == output_path
    assert output_path.exists()