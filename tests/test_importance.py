from atlas.importance import (
    build_importance_from_global_ablation,
    importance_rows_to_dicts,
)


def test_build_importance_from_global_ablation():
    report = {
        "results": [
            {
                "summary": {
                    "experiment_name": "remove_roles",
                    "description": "Remove roles.",
                    "importance_score": 2.0,
                    "mean_rank_shift": 1.0,
                    "mean_changed_profiles": 4.0,
                    "mean_absolute_similarity_delta": 0.01,
                    "max_absolute_similarity_delta": 0.05,
                    "mean_removed_column_count": 10.0,
                    "mean_remaining_feature_count": 100.0,
                }
            },
            {
                "summary": {
                    "experiment_name": "remove_stability",
                    "description": "Remove stability.",
                    "importance_score": 3.0,
                    "mean_rank_shift": 2.0,
                    "mean_changed_profiles": 5.0,
                    "mean_absolute_similarity_delta": 0.02,
                    "max_absolute_similarity_delta": 0.06,
                    "mean_removed_column_count": 12.0,
                    "mean_remaining_feature_count": 98.0,
                }
            },
        ]
    }

    rows = build_importance_from_global_ablation(report)

    assert rows[0].experiment_name == "remove_stability"
    assert rows[0].importance_score == 3.0


def test_importance_rows_to_dicts():
    report = {
        "results": [
            {
                "summary": {
                    "experiment_name": "remove_roles",
                    "description": "Remove roles.",
                    "importance_score": 2.0,
                    "mean_rank_shift": 1.0,
                    "mean_changed_profiles": 4.0,
                    "mean_absolute_similarity_delta": 0.01,
                    "max_absolute_similarity_delta": 0.05,
                    "mean_removed_column_count": 10.0,
                    "mean_remaining_feature_count": 100.0,
                }
            }
        ]
    }

    rows = build_importance_from_global_ablation(report)
    data = importance_rows_to_dicts(rows)

    assert data[0]["experiment_name"] == "remove_roles"
    assert data[0]["importance_score"] == 2.0