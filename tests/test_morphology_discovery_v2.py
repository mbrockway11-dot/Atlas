from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.discovery import (
    MorphologyDiscoveryConfig,
    apply_candidate,
    build_candidate_catalog,
    exact_sign_test_p_value,
    run_discovery_evaluation,
    split_discovery_validation_folds,
    summarize_discovery,
)


def _joined(
    periods: int = 3_200,
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
        fold_id = (
            1 + index // 400
        )

        cluster_id = (
            index % 3
        )

        high_rotation = (
            index % 5
            in {
                0,
                1,
            }
        )

        for asset_index, asset in enumerate(
            ("BTC", "ETH", "SOL")
        ):
            base = (
                0.001
                * (
                    asset_index + 1
                )
            )

            edge = (
                base
                + (
                    0.002
                    if high_rotation
                    else 0.0
                )
            )

            rows.append({
                "timestamp":
                    timestamp,
                "fold_id":
                    fold_id,
                "asset":
                    asset,
                "morphology_cluster_id":
                    cluster_id,
                "morphology_cluster":
                    f"MORPH-{cluster_id}",
                "field_supported":
                    True,
                "field_high_predictability":
                    index % 6 == 0,
                "field_high_expansion":
                    index % 7 == 0,
                "field_high_contraction":
                    index % 9 == 0,
                "field_high_rotation":
                    high_rotation,
                "field_high_strain":
                    index % 8 == 0,
                "field_combined_opportunity":
                    index % 11 == 0,
                "field_validation_state":
                    (
                        "ROTATING_CW"
                        if high_rotation
                        else "EXPANDING"
                    ),
                "forward_return_16":
                    edge,
                "short_return_16":
                    -edge,
                "long_mfe_16":
                    abs(edge) * 1.5,
                "long_mae_16":
                    -abs(edge) * 0.5,
                "short_mfe_16":
                    abs(edge) * 0.5,
                "short_mae_16":
                    -abs(edge) * 1.5,
            })

    return pd.DataFrame(rows)


def _config() -> MorphologyDiscoveryConfig:
    return MorphologyDiscoveryConfig(
        horizon_bars=16,
        transaction_cost_bps=0.0,
        non_overlap_bars=4,
        discovery_fraction=0.50,
        minimum_raw_candidate_rows=100,
        minimum_condition_observations=3,
        minimum_control_observations=3,
        minimum_cluster_observations=6,
        minimum_discovery_folds=2,
        minimum_validation_folds=2,
        minimum_discovery_uplift_rate=0.50,
        minimum_validation_uplift_rate=0.50,
        maximum_pair_candidates=10,
        multiple_testing_alpha=0.50,
    )


def test_catalog_contains_boolean_and_categorical_candidates() -> None:
    frame = _joined()

    catalog = build_candidate_catalog(
        frame,
        config=_config(),
    )

    assert {
        "boolean",
        "categorical",
    }.issubset(
        set(
            catalog[
                "candidate_kind"
            ]
        )
    )


def test_candidate_expression_is_applied() -> None:
    frame = _joined(
        periods=200
    )

    candidate = {
        "feature_a":
            "field_high_rotation",
        "operator_a":
            "IS_TRUE",
        "value_a":
            "True",
        "feature_b":
            "",
        "operator_b":
            "",
        "value_b":
            "",
    }

    mask = apply_candidate(
        frame,
        candidate,
    )

    assert mask.any()
    assert (~mask).any()


def test_fold_split_is_chronological() -> None:
    discovery, validation = (
        split_discovery_validation_folds(
            _joined()["fold_id"],
            discovery_fraction=0.50,
        )
    )

    assert discovery
    assert validation
    assert max(discovery) < min(validation)


def test_sign_test_rewards_consistency() -> None:
    assert (
        exact_sign_test_p_value(
            5,
            5,
        )
        < exact_sign_test_p_value(
            3,
            5,
        )
    )


def test_discovery_evaluation_produces_both_phases() -> None:
    frame = _joined()

    catalog = build_candidate_catalog(
        frame,
        config=_config(),
    )

    discovery, validation = (
        split_discovery_validation_folds(
            frame["fold_id"],
            discovery_fraction=0.50,
        )
    )

    evaluations = (
        run_discovery_evaluation(
            frame,
            catalog=catalog,
            discovery_folds=discovery,
            validation_folds=validation,
            config=_config(),
        )
    )

    assert not evaluations.empty

    assert set(
        evaluations["phase"]
    ) == {
        "DISCOVERY",
        "VALIDATION",
    }


def test_rotation_edge_reaches_summary() -> None:
    frame = _joined()

    catalog = build_candidate_catalog(
        frame,
        config=_config(),
    )

    discovery, validation = (
        split_discovery_validation_folds(
            frame["fold_id"],
            discovery_fraction=0.50,
        )
    )

    evaluations = (
        run_discovery_evaluation(
            frame,
            catalog=catalog,
            discovery_folds=discovery,
            validation_folds=validation,
            config=_config(),
        )
    )

    summary = summarize_discovery(
        evaluations,
        config=_config(),
    )

    rotation = summary[
        summary[
            "expression"
        ].eq(
            "field_high_rotation == True"
        )
        & summary[
            "direction"
        ].eq("LONG")
    ]

    assert not rotation.empty

    assert rotation[
        "discovery_weighted_uplift"
    ].max() > 0.0

    assert rotation[
        "validation_weighted_uplift"
    ].max() > 0.0
