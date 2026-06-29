from atlas.acf.builder import build_acf_profile
from atlas.research import (
    build_profile_matrix_rows,
    compare_profile_feature_importance,
    summarize_feature_importance,
)


def test_compare_profile_feature_importance():
    acf_a = build_acf_profile("Michael Elvis Brockway")
    acf_b = build_acf_profile("Nikola Tesla")

    rows_a = build_profile_matrix_rows(acf_a)
    rows_b = build_profile_matrix_rows(acf_b)

    importance = compare_profile_feature_importance(rows_a, rows_b)

    assert importance
    assert "cipher" in importance[0]
    assert "planet" in importance[0]
    assert "feature" in importance[0]
    assert "difference" in importance[0]


def test_summarize_feature_importance():
    acf_a = build_acf_profile("Michael Elvis Brockway")
    acf_b = build_acf_profile("Nikola Tesla")

    rows_a = build_profile_matrix_rows(acf_a)
    rows_b = build_profile_matrix_rows(acf_b)

    importance = compare_profile_feature_importance(rows_a, rows_b)
    summary = summarize_feature_importance(importance)

    assert "top_layer_differences" in summary
    assert "top_feature_families" in summary