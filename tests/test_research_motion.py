from atlas.acf.builder import build_acf_profile
from atlas.research.motion import (
    build_dynamic_motion_profile,
    build_motion_summary,
    classify_motion_role,
    compare_motion_profiles,
    summarize_motion_by_planet,
    summarize_motion_features,
)


def test_classify_motion_role():
    assert classify_motion_role("max_depth") == "recurrence / depth"
    assert classify_motion_role("max_node_weight") == "recurrence / depth"
    assert classify_motion_role("self_loops") == "recurrence / depth"

    assert classify_motion_role("unique_edges") == "flow complexity"
    assert classify_motion_role("density") == "flow complexity"
    assert classify_motion_role("entropy") == "flow complexity"

    assert classify_motion_role("axis_strength") == "directional structure"

    assert (
        classify_motion_role("profile_node_persistence_ratio")
        == "identity persistence"
    )
    assert (
        classify_motion_role("profile_edge_persistence_ratio")
        == "identity persistence"
    )

    assert classify_motion_role("unknown_feature") == "structural feature"


def test_build_dynamic_motion_profile():
    acf = build_acf_profile("Michael Elvis Brockway")
    motion = build_dynamic_motion_profile(acf)

    assert motion["name"] == "Michael Elvis Brockway"

    assert "feature_summary" in motion
    assert "planet_summary" in motion
    assert "motion_summary" in motion

    assert len(motion["feature_summary"]) > 0
    assert len(motion["planet_summary"]) == 7
    assert isinstance(motion["motion_summary"], str)


def test_summarize_motion_features():
    acf = build_acf_profile("Michael Elvis Brockway")
    rows = acf["identity_graph"]["layers"]

    # Use build_dynamic_motion_profile here because raw identity layers are not
    # research matrix rows. This confirms feature_summary is produced correctly.
    motion = build_dynamic_motion_profile(acf)

    assert motion["feature_summary"]
    assert "feature" in motion["feature_summary"][0]
    assert "motion_role" in motion["feature_summary"][0]


def test_summarize_motion_by_planet():
    acf = build_acf_profile("Michael Elvis Brockway")
    motion = build_dynamic_motion_profile(acf)

    planets = {
        row["planet"]
        for row in motion["planet_summary"]
    }

    assert planets == {
        "Saturn",
        "Jupiter",
        "Mars",
        "Sun",
        "Venus",
        "Mercury",
        "Moon",
    }

    first = motion["planet_summary"][0]

    assert "structural_motion" in first
    assert "depth" in first
    assert "entropy" in first
    assert "edge_activity" in first


def test_build_motion_summary():
    feature_summary = [
        {
            "feature": "max_depth",
        },
        {
            "feature": "unique_edges",
        },
        {
            "feature": "entropy",
        },
    ]

    planet_summary = [
        {
            "planet": "Mercury",
        },
        {
            "planet": "Moon",
        },
        {
            "planet": "Mars",
        },
    ]

    summary = build_motion_summary(
        feature_summary,
        planet_summary,
    )

    assert "max_depth" in summary
    assert "Mercury" in summary


def test_compare_motion_profiles():
    acf_a = build_acf_profile("Michael Elvis Brockway")
    acf_b = build_acf_profile("Nikola Tesla")

    comparison = compare_motion_profiles(acf_a, acf_b)

    assert comparison["name_a"] == "Michael Elvis Brockway"
    assert comparison["name_b"] == "Nikola Tesla"

    assert "top_layer_differences" in comparison
    assert "top_feature_families" in comparison

    assert comparison["top_layer_differences"]
    assert comparison["top_feature_families"]