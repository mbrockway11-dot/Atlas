from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.field_incremental_value import (
    FieldIncrementalValueConfig,
    benjamini_hochberg,
    cluster_weighted_uplift,
    evaluate_incremental_value,
    matched_cluster_samples,
    select_non_overlapping,
    summarize_incremental_value,
)


def _joined(
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
        cluster_id = index % 3
        high_rotation = (
            index % 4 == 0
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
                    0.0015
                    if high_rotation
                    else 0.0
                )
            )

            rows.append({
                "timestamp":
                    timestamp,
                "fold_id":
                    1 + index // 400,
                "asset":
                    asset,
                "morphology_cluster_id":
                    cluster_id,
                "morphology_cluster":
                    f"MORPH-{cluster_id}",
                "field_supported":
                    True,
                "field_high_predictability":
                    index % 5 == 0,
                "field_high_expansion":
                    index % 6 == 0,
                "field_high_contraction":
                    index % 7 == 0,
                "field_high_rotation":
                    high_rotation,
                "field_high_strain":
                    index % 8 == 0,
                "field_combined_opportunity":
                    index % 9 == 0,
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


def _config() -> FieldIncrementalValueConfig:
    return FieldIncrementalValueConfig(
        horizon_bars=16,
        transaction_cost_bps=0.0,
        minimum_condition_observations=3,
        minimum_control_observations=3,
        minimum_cluster_observations=6,
        minimum_valid_folds=2,
        non_overlap_bars=4,
        bootstrap_iterations=20,
        permutation_iterations=20,
        bootstrap_block_size=2,
        random_seed=33,
    )


def test_non_overlap_reduces_rows() -> None:
    frame = _joined(
        periods=100
    )

    asset = frame[
        frame["asset"].eq("BTC")
    ]

    selected = select_non_overlapping(
        asset,
        bars=4,
    )

    assert len(selected) < len(asset)


def test_cluster_matching_keeps_shared_clusters() -> None:
    frame = _joined(
        periods=500
    )

    btc = frame[
        frame["asset"].eq("BTC")
    ]

    condition, control = (
        matched_cluster_samples(
            btc,
            condition_name="HIGH_ROTATION",
            config=_config(),
        )
    )

    assert not condition.empty
    assert not control.empty

    assert set(
        condition[
            "morphology_cluster_id"
        ]
    ) == set(
        control[
            "morphology_cluster_id"
        ]
    )


def test_cluster_weighted_uplift_is_positive() -> None:
    frame = _joined(
        periods=500
    )

    btc = frame[
        frame["asset"].eq("BTC")
    ]

    condition, control = (
        matched_cluster_samples(
            btc,
            condition_name="HIGH_ROTATION",
            config=_config(),
        )
    )

    uplift, details = (
        cluster_weighted_uplift(
            condition,
            control,
            direction="LONG",
            config=_config(),
        )
    )

    assert not details.empty
    assert uplift > 0.0


def test_bh_adjustment_is_monotonic() -> None:
    p_values = pd.Series(
        [0.001, 0.01, 0.04, 0.20]
    )

    adjusted = benjamini_hochberg(
        p_values
    )

    assert adjusted.between(
        0.0,
        1.0,
    ).all()

    assert adjusted.iloc[0] <= (
        adjusted.iloc[-1]
    )


def test_incremental_evaluation_returns_rows() -> None:
    evaluations, clusters = (
        evaluate_incremental_value(
            _joined(),
            config=_config(),
        )
    )

    assert not evaluations.empty
    assert not clusters.empty

    assert {
        "cluster_matched_uplift",
        "uplift_ci_low",
        "uplift_ci_high",
        "permutation_p_value",
    }.issubset(
        evaluations.columns
    )


def test_summary_identifies_rotation_candidate() -> None:
    evaluations, _ = (
        evaluate_incremental_value(
            _joined(),
            config=_config(),
        )
    )

    summary = summarize_incremental_value(
        evaluations,
        config=_config(),
    )

    rotation = summary[
        summary[
            "condition_name"
        ].eq("HIGH_ROTATION")
        & summary[
            "direction"
        ].eq("LONG")
    ]

    assert not rotation.empty

    assert rotation[
        "weighted_cluster_matched_uplift"
    ].max() > 0.0
