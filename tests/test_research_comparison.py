from atlas.acf.builder import build_acf_profile
from atlas.research.comparison import compare_acf_profiles
from atlas.research.differential import summarize_profile_difference


def test_compare_acf_profiles():
    acf_a = build_acf_profile("Julius Caesar")
    acf_b = build_acf_profile("Napoleon Bonaparte")

    comparison = compare_acf_profiles(acf_a, acf_b)

    assert comparison["profile_a"] == "Julius Caesar"
    assert comparison["profile_b"] == "Napoleon Bonaparte"
    assert "overall_similarity" in comparison
    assert "subtype" in comparison
    assert "planetary" in comparison
    assert "essence_function" in comparison


def test_summarize_profile_difference():
    acf_a = build_acf_profile("Julius Caesar")
    acf_b = build_acf_profile("Napoleon Bonaparte")

    comparison = compare_acf_profiles(acf_a, acf_b)
    summary = summarize_profile_difference(comparison)

    assert summary["profile_a"] == "Julius Caesar"
    assert summary["profile_b"] == "Napoleon Bonaparte"
    assert "largest_subtype_difference" in summary
    assert "largest_planetary_difference" in summary
    assert "largest_essence_difference" in summary