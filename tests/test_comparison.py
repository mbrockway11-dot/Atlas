import pandas as pd

from atlas.comparison import (
    compare_profiles,
    identity_comparison_to_dict,
)


def test_compare_profiles():
    dataframe = pd.DataFrame(
        [
            {
                "name": "A",
                "saturn_entropy": 0.1,
                "saturn_hub_ratio": 0.2,
                "mars_entropy": 0.3,
            },
            {
                "name": "B",
                "saturn_entropy": 0.2,
                "saturn_hub_ratio": 0.25,
                "mars_entropy": 0.35,
            },
            {
                "name": "C",
                "saturn_entropy": 0.9,
                "saturn_hub_ratio": 0.8,
                "mars_entropy": 0.7,
            },
        ]
    )

    comparison = compare_profiles(
        dataframe=dataframe,
        profile_a="A",
        profile_b="B",
        top_n=2,
    )

    assert comparison.profile_a == "A"
    assert comparison.profile_b == "B"
    assert comparison.similarity > 0
    assert comparison.most_similar_features
    assert comparison.most_different_features
    assert comparison.planet_summary["ranked_planets"]


def test_identity_comparison_to_dict():
    dataframe = pd.DataFrame(
        [
            {
                "name": "A",
                "saturn_entropy": 0.1,
                "saturn_hub_ratio": 0.2,
            },
            {
                "name": "B",
                "saturn_entropy": 0.2,
                "saturn_hub_ratio": 0.25,
            },
        ]
    )

    comparison = compare_profiles(
        dataframe=dataframe,
        profile_a="A",
        profile_b="B",
    )

    data = identity_comparison_to_dict(comparison)

    assert data["profile_a"] == "A"
    assert data["profile_b"] == "B"
    assert "planet_summary" in data