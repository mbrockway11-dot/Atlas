"""Feature importance audit for profile-to-profile differences."""

from __future__ import annotations

from typing import Any

from atlas.research.feature_variance import AUDIT_FEATURES


def compare_profile_feature_importance(
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare two profile research matrices feature-by-feature."""
    paired_rows = pair_layers(rows_a, rows_b)
    importance_rows = []

    for layer_key, row_a, row_b in paired_rows:
        cipher, planet = layer_key

        for feature in AUDIT_FEATURES:
            if feature not in row_a or feature not in row_b:
                continue

            value_a = float(row_a[feature])
            value_b = float(row_b[feature])
            difference = abs(value_a - value_b)

            importance_rows.append(
                {
                    "cipher": cipher,
                    "planet": planet,
                    "feature": feature,
                    "value_a": value_a,
                    "value_b": value_b,
                    "difference": difference,
                }
            )

    return sorted(
        importance_rows,
        key=lambda row: row["difference"],
        reverse=True,
    )


def pair_layers(
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
) -> list[tuple[tuple[str, str], dict[str, Any], dict[str, Any]]]:
    """Pair profile rows by cipher and planet."""
    index_a = {
        (row["cipher"], row["planet"]): row
        for row in rows_a
    }
    index_b = {
        (row["cipher"], row["planet"]): row
        for row in rows_b
    }

    shared_keys = sorted(set(index_a) & set(index_b))

    return [
        (
            key,
            index_a[key],
            index_b[key],
        )
        for key in shared_keys
    ]


def summarize_feature_importance(
    importance_rows: list[dict[str, Any]],
    top_n: int = 10,
) -> dict[str, Any]:
    """Summarize strongest feature differences."""
    feature_totals: dict[str, float] = {}

    for row in importance_rows:
        feature = row["feature"]
        feature_totals.setdefault(feature, 0.0)
        feature_totals[feature] += row["difference"]

    ranked_features = sorted(
        [
            {
                "feature": feature,
                "total_difference": total,
            }
            for feature, total in feature_totals.items()
        ],
        key=lambda row: row["total_difference"],
        reverse=True,
    )

    return {
        "top_layer_differences": importance_rows[:top_n],
        "top_feature_families": ranked_features[:top_n],
    }