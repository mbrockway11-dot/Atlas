import pandas as pd

from atlas.corpus.diagnostics import (
    build_feature_diagnostics,
    diagnostics_to_dict,
    numeric_feature_columns,
)


def test_numeric_feature_columns_excludes_metadata():
    dataframe = pd.DataFrame(
        [
            {
                "name": "A",
                "global_entropy": 0.1,
                "quality_planet_count": 7,
                "diagnostic_flag": 1,
                "primary_archetype_score": 0.5,
            }
        ]
    )

    columns = numeric_feature_columns(dataframe)

    assert "global_entropy" in columns
    assert "primary_archetype_score" in columns
    assert "quality_planet_count" not in columns
    assert "diagnostic_flag" not in columns


def test_build_feature_diagnostics():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "feature_a": 0.1, "feature_b": 0.5},
            {"name": "B", "feature_a": 0.2, "feature_b": 0.5},
            {"name": "C", "feature_a": 0.9, "feature_b": 0.5},
        ]
    )

    diagnostics = build_feature_diagnostics(dataframe)

    assert diagnostics.profile_count == 3
    assert diagnostics.feature_count == 2
    assert diagnostics.highest_variance_features
    assert diagnostics.lowest_variance_features
    assert diagnostics.near_constant_features


def test_diagnostics_to_dict():
    dataframe = pd.DataFrame(
        [
            {"name": "A", "feature_a": 0.1},
            {"name": "B", "feature_a": 0.2},
        ]
    )

    diagnostics = build_feature_diagnostics(dataframe)
    data = diagnostics_to_dict(diagnostics)

    assert data["profile_count"] == 2
    assert "summary" in data