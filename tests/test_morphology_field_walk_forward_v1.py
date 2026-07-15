from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.field_walk_forward import (
    FieldWalkForwardConfig,
    assign_frozen_grid,
    build_walk_forward_folds,
    finite_quantile_edges,
    fit_training_field,
    run_field_walk_forward,
    score_test_field,
    summarize_field_validation,
)


def _motion(
    periods: int = 4_000,
) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2024-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    phase = np.linspace(
        0.0,
        30.0,
        periods,
    )

    x = np.sin(phase)
    y = np.cos(phase)

    return pd.DataFrame({
        "timestamp":
            timestamps,
        "morphology_cluster_id":
            (
                (
                    x > 0.0
                ).astype(int)
            ),
        "morphology_cluster":
            np.where(
                x > 0.0,
                "MORPH-1",
                "MORPH-0",
            ),
        "morphology_pc_1":
            x,
        "morphology_pc_2":
            y,
        "morphology_velocity_1":
            np.gradient(x),
        "morphology_velocity_2":
            np.gradient(y),
        "morphology_speed":
            np.hypot(
                np.gradient(x),
                np.gradient(y),
            ),
        "morphology_acceleration_magnitude":
            np.hypot(
                np.gradient(
                    np.gradient(x)
                ),
                np.gradient(
                    np.gradient(y)
                ),
            ),
        "morphology_curvature":
            np.abs(
                np.gradient(
                    np.arctan2(
                        np.gradient(y),
                        np.gradient(x),
                    )
                )
            ),
        "morphology_directional_stability":
            0.8,
    })


def _outcomes(
    motion: pd.DataFrame,
    horizon: int = 16,
) -> pd.DataFrame:
    rows = []

    for row in motion.itertuples(
        index=False
    ):
        for asset_index, asset in enumerate(
            ("BTC", "ETH", "SOL")
        ):
            edge = (
                0.001
                * (
                    asset_index + 1
                )
                * (
                    1.0
                    if row.morphology_pc_1 > 0
                    else -0.25
                )
            )

            rows.append({
                "timestamp":
                    row.timestamp,
                "asset":
                    asset,
                "morphology_cluster_id":
                    row.morphology_cluster_id,
                f"forward_return_{horizon}":
                    edge,
                f"short_return_{horizon}":
                    -edge,
                f"long_mfe_{horizon}":
                    abs(edge) * 1.5,
                f"long_mae_{horizon}":
                    -abs(edge) * 0.5,
                f"short_mfe_{horizon}":
                    abs(edge) * 0.5,
                f"short_mae_{horizon}":
                    -abs(edge) * 1.5,
            })

    return pd.DataFrame(rows)


def _config() -> FieldWalkForwardConfig:
    return FieldWalkForwardConfig(
        training_days=20,
        test_days=10,
        step_days=10,
        embargo_bars=4,
        minimum_training_timestamps=500,
        minimum_test_timestamps=100,
        minimum_test_observations=5,
        horizon_bars=16,
        grid_bins=10,
        minimum_cell_observations=2,
    )


def test_frozen_edges_do_not_use_test_data() -> None:
    training = _motion(
        periods=1000
    )

    test = _motion(
        periods=200
    ).copy()

    test[
        "morphology_pc_1"
    ] += 100.0

    edges = finite_quantile_edges(
        training[
            "morphology_pc_1"
        ],
        bin_count=10,
    )

    assigned = assign_frozen_grid(
        test,
        x_edges=edges,
        y_edges=finite_quantile_edges(
            training[
                "morphology_pc_2"
            ],
            bin_count=10,
        ),
        training=False,
    )

    assert (
        ~assigned[
            "field_inside_training_bounds"
        ]
    ).all()


def test_walk_forward_boundaries_are_chronological() -> None:
    folds = build_walk_forward_folds(
        _motion()["timestamp"],
        config=_config(),
    )

    assert folds

    for fold in folds:
        assert (
            fold["train_start"]
            < fold["train_end"]
            <= fold["test_start"]
            < fold["test_end"]
        )


def test_training_field_produces_thresholds() -> None:
    motion = _motion()

    field, x_edges, y_edges, thresholds = (
        fit_training_field(
            motion.iloc[:2000],
            config=_config(),
        )
    )

    assert not field.empty
    assert len(x_edges) >= 3
    assert len(y_edges) >= 3

    assert {
        "predictability_high",
        "divergence_high",
        "divergence_low",
        "curl_high",
        "strain_high",
    } == set(thresholds)


def test_test_scoring_marks_supported_rows() -> None:
    motion = _motion()

    field, x_edges, y_edges, thresholds = (
        fit_training_field(
            motion.iloc[:2000],
            config=_config(),
        )
    )

    scored = score_test_field(
        motion.iloc[2000:2500],
        field=field,
        x_edges=x_edges,
        y_edges=y_edges,
        thresholds=thresholds,
        config=_config(),
    )

    assert {
        "field_supported",
        "field_validation_state",
        "field_high_predictability",
        "field_combined_opportunity",
    }.issubset(
        scored.columns
    )


def test_walk_forward_returns_evaluations() -> None:
    motion = _motion()
    outcomes = _outcomes(motion)

    scores, evaluations = (
        run_field_walk_forward(
            motion=motion,
            outcomes=outcomes,
            config=_config(),
        )
    )

    assert not scores.empty
    assert not evaluations.empty

    assert {
        "mean_return",
        "mean_return_uplift",
        "win_rate_uplift",
        "condition_name",
    }.issubset(
        evaluations.columns
    )


def test_summary_contains_baseline_and_field_models() -> None:
    motion = _motion()
    outcomes = _outcomes(motion)

    _, evaluations = run_field_walk_forward(
        motion=motion,
        outcomes=outcomes,
        config=_config(),
    )

    summary = summarize_field_validation(
        evaluations
    )

    assert {
        "STATIC_BASELINE",
        "FIELD_CONDITIONED",
    }.issubset(
        set(
            summary[
                "model_name"
            ]
        )
    )

    assert {
        "research_candidate",
        "weighted_mean_return_uplift",
        "positive_uplift_fold_rate",
    }.issubset(
        summary.columns
    )
