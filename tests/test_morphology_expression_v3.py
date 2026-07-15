from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.expression_v3 import (
    MorphologyExpressionConfig,
    apply_expression_candidate,
    build_expression_catalog,
    engineer_expression_features,
)


def _frame(
    periods: int = 2_000,
) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2024-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    rows = []

    for index, timestamp in enumerate(
        timestamps
    ):
        rotation = (
            index % 5
            in {
                0,
                1,
            }
        )

        approaching = (
            index % 4
            in {
                0,
                1,
            }
        )

        trajectory_enter = (
            index % 6
            in {
                0,
                1,
                2,
            }
        )

        rows.append({
            "timestamp":
                timestamp,
            "fold_id":
                1 + index // 250,
            "asset":
                "SOL",
            "morphology_cluster_id":
                index % 3,
            "field_supported":
                True,
            "field_high_predictability":
                index % 3 == 0,
            "field_high_expansion":
                index % 7 == 0,
            "field_high_contraction":
                False,
            "field_high_rotation":
                rotation,
            "field_high_strain":
                index % 8 == 0,
            "field_combined_opportunity":
                False,
            "evolution_signal":
                (
                    "APPROACH"
                    if approaching
                    else "RECEDING"
                ),
            "attractor_closing_efficiency":
                (
                    0.5
                    if approaching
                    else -0.4
                ),
            "distance_to_attractor":
                (
                    0.5
                    if approaching
                    else 2.0
                ),
            "estimated_bars_to_attractor":
                (
                    12.0
                    if approaching
                    else 10000.0
                ),
            "recommended_action":
                (
                    "ENTER"
                    if trajectory_enter
                    else "AVOID"
                ),
            "trajectory_score":
                (
                    0.01
                    if trajectory_enter
                    else 0.0
                ),
            "trajectory_shape":
                (
                    "PROGRESSIVE"
                    if trajectory_enter
                    else "OSCILLATING"
                ),
            "morphology_motion_state":
                (
                    "ACCELERATING"
                    if index % 2 == 0
                    else "FLOWING"
                ),
            "morphology_directional_stability":
                0.8,
        })

    return pd.DataFrame(rows)


def _config() -> MorphologyExpressionConfig:
    return MorphologyExpressionConfig(
        minimum_raw_candidate_rows=20,
        maximum_pair_candidates=20,
        maximum_triple_candidates=20,
    )


def test_expression_features_are_engineered() -> None:
    frame = engineer_expression_features(
        _frame(),
        config=_config(),
    )

    assert {
        "expression_approaching_attractor",
        "expression_trajectory_enter",
        "expression_motion_accelerating",
        "expression_positive_closing_efficiency",
    }.issubset(
        frame.columns
    )

    assert frame[
        "expression_approaching_attractor"
    ].any()

    assert frame[
        "expression_receding"
    ].any()


def test_catalog_contains_interactions() -> None:
    frame = engineer_expression_features(
        _frame(),
        config=_config(),
    )

    catalog = build_expression_catalog(
        frame,
        config=_config(),
    )

    assert not catalog.empty

    assert {
        "single",
        "pair",
        "triple",
    }.intersection(
        set(
            catalog[
                "candidate_kind"
            ]
        )
    )


def test_triple_expression_can_be_applied() -> None:
    frame = engineer_expression_features(
        _frame(),
        config=_config(),
    )

    candidate = {
        "feature_a":
            "field_high_rotation",
        "operator_a":
            "IS_TRUE",
        "value_a":
            "True",
        "feature_b":
            "expression_approaching_attractor",
        "operator_b":
            "IS_TRUE",
        "value_b":
            "True",
        "feature_c":
            "expression_trajectory_enter",
    }

    mask = apply_expression_candidate(
        frame,
        candidate,
    )

    assert mask.any()
    assert (~mask).any()


def test_catalog_is_deterministic() -> None:
    frame = engineer_expression_features(
        _frame(),
        config=_config(),
    )

    first = build_expression_catalog(
        frame,
        config=_config(),
    )

    second = build_expression_catalog(
        frame,
        config=_config(),
    )

    assert first[
        "candidate_id"
    ].tolist() == second[
        "candidate_id"
    ].tolist()


def test_expression_feature_export_schema_includes_field_support() -> None:
    frame = engineer_expression_features(
        _frame(),
        config=_config(),
    )

    assert "field_supported" in frame.columns
    assert frame["field_supported"].astype(bool).all()