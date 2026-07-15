from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.regime_stability import (
    MorphologyRegimeStabilityConfig,
    build_expression_stability_matrix,
    build_past_only_regimes,
    summarize_regime_stability,
)


def _market(
    periods: int = 1500,
) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2024-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    close = (
        100.0
        * np.exp(
            np.linspace(
                0.0,
                0.20,
                periods,
            )
        )
    )

    volume = np.where(
        np.arange(periods)
        < periods // 2,
        100.0,
        150.0,
    )

    return pd.DataFrame({
        "timestamp":
            timestamps,
        "asset":
            "BTC",
        "close":
            close,
        "volume":
            volume,
    })


def _config() -> MorphologyRegimeStabilityConfig:
    return MorphologyRegimeStabilityConfig(
        trend_lookback_bars=96,
        volatility_lookback_bars=32,
        liquidity_lookback_bars=32,
        minimum_condition_observations=2,
        minimum_control_observations=2,
        minimum_cluster_observations=4,
        minimum_regime_folds=2,
    )


def test_regimes_are_past_only_and_nonempty() -> None:
    regimes = build_past_only_regimes(
        _market(),
        config=_config(),
    )

    assert not regimes.empty

    assert {
        "trend_regime",
        "volatility_regime",
        "liquidity_regime",
        "combined_regime",
    }.issubset(
        regimes.columns
    )

    assert regimes["timestamp"].is_monotonic_increasing


def test_combined_regime_contains_three_dimensions() -> None:
    regimes = build_past_only_regimes(
        _market(),
        config=_config(),
    )

    assert regimes[
        "combined_regime"
    ].str.count(
        r"\|"
    ).eq(2).all()


def test_summary_can_identify_stable_regime() -> None:
    evaluations = pd.DataFrame([
        {
            "candidate_id": "C1",
            "candidate_kind": "single",
            "expression": "field_high_rotation == True",
            "asset": "SOL",
            "direction": "LONG",
            "regime_dimension": "trend_regime",
            "regime_value": "BULL",
            "fold_id": fold_id,
            "condition_observations": 20,
            "control_observations": 20,
            "matched_cluster_count": 2,
            "condition_net_mean_return": 0.003,
            "control_net_mean_return": 0.001,
            "cluster_matched_uplift": 0.002,
            "condition_net_win_rate": 0.60,
            "control_net_win_rate": 0.50,
            "condition_profit_factor": 1.5,
        }
        for fold_id in range(1, 6)
    ])

    summary = summarize_regime_stability(
        evaluations,
        config=MorphologyRegimeStabilityConfig(
            minimum_regime_folds=4,
            multiple_testing_alpha=0.10,
        ),
    )

    assert not summary.empty
    assert bool(
        summary.iloc[0][
            "regime_stable"
        ]
    )


def test_stability_matrix_reports_candidate() -> None:
    summary = pd.DataFrame([
        {
            "candidate_id": "C1",
            "expression": "x",
            "asset": "SOL",
            "direction": "LONG",
            "regime_dimension": "trend_regime",
            "regime_value": "BULL",
            "valid_fold_count": 5,
            "weighted_condition_net_return": 0.002,
            "weighted_cluster_matched_uplift": 0.001,
            "regime_stable": True,
        }
    ])

    matrix = build_expression_stability_matrix(
        summary
    )

    assert not matrix.empty
    assert bool(
        matrix.iloc[0][
            "regime_dependent_candidate"
        ]
    )
