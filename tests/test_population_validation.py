import pandas as pd

from atlas.research.validation import (
    build_population_validation_report,
    build_profile_feature_matrix,
    correlated_feature_pairs,
    data_quality_checks,
    nearest_neighbors,
    outlier_scores,
)


def sample_matrix():
    rows = []
    for name, offset in [
        ("Alpha", 0.0),
        ("Beta", 0.2),
        ("Gamma", 5.0),
    ]:
        for cipher in ["ordinal", "hebrew_phonetic", "hebrew_literal"]:
            for planet in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]:
                rows.append(
                    {
                        "name": name,
                        "cipher": cipher,
                        "planet": planet,
                        "kamea": planet,
                        "grid_size": 3,
                        "sequence_length": 10 + offset,
                        "unique_nodes": 5 + offset,
                        "density": 0.1 + offset,
                        "entropy": 1.0 + offset,
                    }
                )
    return pd.DataFrame(rows)


def test_data_quality_checks_passes_complete_matrix():
    quality = data_quality_checks(sample_matrix())

    assert quality["duplicate_profile_cipher_planet_rows"] == 0
    assert quality["profile_count_with_missing_realizations"] == 0
    assert quality["expected_rows_per_profile"] == 21


def test_profile_feature_matrix_aggregates_to_one_row_per_profile():
    features = build_profile_feature_matrix(sample_matrix())

    assert list(features["name"]) == ["Alpha", "Beta", "Gamma"]
    assert "density_mean" in features.columns
    assert "entropy_max" in features.columns


def test_nearest_neighbors_returns_beta_for_alpha():
    features = build_profile_feature_matrix(sample_matrix())
    neighbors = nearest_neighbors(features, "Alpha", limit=1)

    assert neighbors[0]["name"] == "Beta"


def test_outlier_scores_ranks_gamma_highest():
    features = build_profile_feature_matrix(sample_matrix())
    outliers = outlier_scores(features)

    assert outliers.iloc[0]["name"] == "Gamma"


def test_correlated_feature_pairs_and_report_are_available():
    matrix = sample_matrix()
    features = build_profile_feature_matrix(matrix)
    pairs = correlated_feature_pairs(features, threshold=0.95)
    report = build_population_validation_report(matrix)

    assert isinstance(pairs, list)
    assert report["corpus_summary"]["unique_profiles"] == 3
    assert "correlated_feature_pairs" in report