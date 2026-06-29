from atlas.profiles.summary import build_individual_profile_summary


def test_build_individual_profile_summary():
    summary = build_individual_profile_summary("Michael Elvis Brockway")

    assert summary["name"] == "Michael Elvis Brockway"
    assert summary["analysis_count"] == 21
    assert len(summary["analyses"]) == 21

    first = summary["analyses"][0]

    assert "cipher" in first
    assert "kamea" in first
    assert "planet" in first
    assert "raw_values" in first
    assert "reduced_values" in first
    assert "coordinates" in first
    assert "graph_summary" in first
    assert "signature" in first

    assert "scores" in first["signature"]
    assert "metrics" in first["signature"]
    assert "patterns" in first["signature"]
    assert "motifs" in first["signature"]