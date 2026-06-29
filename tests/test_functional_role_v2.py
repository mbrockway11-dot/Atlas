from atlas.classification.functional_role_v2 import (
    classify_functional_role_v2,
    classify_profile_functional_role_v2,
    normalize_scores,
    score_functional_roles,
    score_modifiers,
)
from atlas.research import build_research_matrix


def test_functional_role_v2_scores_are_normalized():
    rows = build_research_matrix(["Michael Elvis Brockway"])
    result = classify_functional_role_v2(rows[0])

    assert result["version"] == "2.0"
    assert result["primary_role"] in [
        "Driver",
        "Amplifier",
        "Regulator",
        "Integrator",
        "Explorer",
    ]
    assert result["modifier"]
    assert result["subtype"] == f"{result['primary_role']}-{result['modifier']}"

    total = sum(result["scores"].values())

    assert abs(total - 1.0) < 0.000001
    assert 0.0 <= result["confidence"] <= 1.0


def test_functional_role_v2_raw_scores_are_bounded():
    rows = build_research_matrix(["Michael Elvis Brockway"])
    scores = score_functional_roles(rows[0])

    for score in scores.values():
        assert 0.0 <= score <= 1.0


def test_functional_role_v2_modifier_scores_are_bounded():
    rows = build_research_matrix(["Michael Elvis Brockway"])
    scores = score_modifiers(rows[0])

    assert "Axial" in scores
    assert "Persistent" in scores
    assert "Bridge" in scores

    for score in scores.values():
        assert 0.0 <= score <= 1.0


def test_profile_functional_role_v2_classification():
    rows = build_research_matrix(["Michael Elvis Brockway"])
    result = classify_profile_functional_role_v2(rows)

    assert result["version"] == "2.0"
    assert result["scope"] == "profile"
    assert result["primary_role"] in [
        "Driver",
        "Amplifier",
        "Regulator",
        "Integrator",
        "Explorer",
    ]
    assert result["modifier"]
    assert result["layer_results"]
    assert len(result["layer_results"]) == 21

    total = sum(result["scores"].values())

    assert abs(total - 1.0) < 0.000001


def test_normalize_scores_handles_zero_scores():
    scores = normalize_scores(
        {
            "Driver": 0.0,
            "Amplifier": 0.0,
            "Regulator": 0.0,
        }
    )

    assert abs(sum(scores.values()) - 1.0) < 0.000001
    assert scores["Driver"] == scores["Amplifier"] == scores["Regulator"]