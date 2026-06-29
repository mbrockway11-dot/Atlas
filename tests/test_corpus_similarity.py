import pandas as pd

from atlas.corpus.similarity import (
    explain_profile_difference,
    find_nearest_profiles,
    numeric_similarity_columns,
    pearson_similarity,
)


def test_numeric_similarity_columns_excludes_constant_and_metadata():
    dataframe = pd.DataFrame(
        [
            {
                "name": "A",
                "feature_a": 0.1,
                "feature_b": 0.5,
                "quality_planet_count": 7,
                "saturn_source_count": 3,
            },
            {
                "name": "B",
                "feature_a": 0.9,
                "feature_b": 0.5,
                "quality_planet_count": 7,
                "saturn_source_count": 3,
            },
        ]
    )

    columns = numeric_similarity_columns(dataframe)

    assert "feature_a" in columns
    assert "feature_b" not in columns
    assert "quality_planet_count" not in columns
    assert "saturn_source_count" not in columns


def test_find_nearest_profiles_euclidean():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "feature_a": 0.1, "feature_b": 0.1},
            {"name": "B", "feature_a": 0.2, "feature_b": 0.2},
            {"name": "C", "feature_a": 0.9, "feature_b": 0.9},
        ]
    )

    results = find_nearest_profiles(
        dataframe=dataframe,
        profile_name="A",
        top_n=1,
        metric="euclidean",
    )

    assert results.iloc[0]["name"] == "B"


def test_find_nearest_profiles_manhattan():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "feature_a": 0.1, "feature_b": 0.1},
            {"name": "B", "feature_a": 0.2, "feature_b": 0.2},
            {"name": "C", "feature_a": 0.9, "feature_b": 0.9},
        ]
    )

    results = find_nearest_profiles(
        dataframe=dataframe,
        profile_name="A",
        top_n=1,
        metric="manhattan",
    )

    assert results.iloc[0]["name"] == "B"


def test_pearson_similarity_bounds():
    similarity = pearson_similarity(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
    )

    assert similarity == 1.0


def test_explain_profile_difference():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "feature_a": 0.1, "feature_b": 0.1},
            {"name": "B", "feature_a": 0.2, "feature_b": 0.1},
            {"name": "C", "feature_a": 0.9, "feature_b": 0.9},
        ]
    )

    explanation = explain_profile_difference(
        dataframe=dataframe,
        profile_a="A",
        profile_b="B",
        top_n=1,
    )

    assert explanation["profile_a"] == "A"
    assert explanation["profile_b"] == "B"
    assert explanation["most_similar_features"]
    assert explanation["most_different_features"]