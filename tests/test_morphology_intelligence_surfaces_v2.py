from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.surfaces import (
    MorphologySurfaceConfig,
    build_entry_exit_surfaces,
    build_morphology_bins,
    build_surface_matrix,
)


def _observations(
    periods: int = 200,
) -> pd.DataFrame:
    rows = []

    timestamps = pd.date_range(
        "2026-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    for index, timestamp in enumerate(
        timestamps
    ):
        positive_state = (
            index % 2 == 0
        )

        forward = (
            0.02
            if positive_state
            else -0.01
        )

        rows.append({
            "timestamp": timestamp,
            "asset": "SOL",
            "rank_state": (
                "SOL>ETH>BTC"
                if positive_state
                else "BTC>ETH>SOL"
            ),
            "transition": (
                "ETH>SOL>BTC->SOL>ETH>BTC"
                if positive_state
                else "SOL>ETH>BTC->BTC>ETH>SOL"
            ),
            "entropy": 0.2 + index / 1000,
            "transition_velocity":
                0.1 + index / 2000,
            "multi_timeframe_agreement":
                0.6 + (index % 10) / 100,
            "concentration":
                0.7 + (index % 5) / 100,
            "dispersion":
                0.01 + (index % 3) / 1000,
            "persistence_bars":
                1 + index % 12,
            "forward_return_1":
                forward / 4,
            "long_mfe_1":
                max(forward / 3, 0.001),
            "long_mae_1":
                min(forward / 6, -0.001),
            "short_return_1":
                -forward / 4,
            "short_mfe_1":
                max(-forward / 3, 0.001),
            "short_mae_1":
                min(-forward / 6, -0.001),
            "forward_return_4":
                forward,
            "long_mfe_4":
                max(forward * 1.25, 0.002),
            "long_mae_4":
                min(forward * 0.30, -0.002),
            "short_return_4":
                -forward,
            "short_mfe_4":
                max(-forward * 1.25, 0.002),
            "short_mae_4":
                min(-forward * 0.30, -0.002),
        })

    return pd.DataFrame(rows)


def test_bins_are_added() -> None:
    frame = build_morphology_bins(
        _observations(),
        config=MorphologySurfaceConfig(
            horizons=(1, 4),
            minimum_observations=2,
            quantile_bins=4,
        ),
    )

    assert "entropy_bin" in frame.columns
    assert "velocity_bin" in frame.columns
    assert "agreement_bin" in frame.columns
    assert "persistence_bin" in frame.columns


def test_surface_matrix_contains_both_directions() -> None:
    matrix = build_surface_matrix(
        _observations(),
        config=MorphologySurfaceConfig(
            horizons=(1, 4),
            minimum_observations=2,
            confidence_target=10,
            quantile_bins=2,
        ),
    )

    assert set(
        matrix["direction"]
    ) == {
        "LONG",
        "SHORT",
    }

    assert set(
        matrix["horizon_bars"]
    ) == {
        1,
        4,
    }


def test_positive_long_state_is_detected() -> None:
    matrix = build_surface_matrix(
        _observations(),
        config=MorphologySurfaceConfig(
            horizons=(1, 4),
            minimum_observations=2,
            confidence_target=10,
            quantile_bins=2,
        ),
    )

    positive = matrix[
        matrix["rank_state"].eq(
            "SOL>ETH>BTC"
        )
        & matrix["direction"].eq(
            "LONG"
        )
        & matrix[
            "horizon_bars"
        ].eq(4)
    ]

    assert not positive.empty
    assert (
        positive[
            "mean_return"
        ] > 0.0
    ).all()


def test_entry_exit_surface_selects_a_direction() -> None:
    matrix = build_surface_matrix(
        _observations(),
        config=MorphologySurfaceConfig(
            horizons=(1, 4),
            minimum_observations=2,
            confidence_target=10,
            quantile_bins=2,
        ),
    )

    surfaces = (
        build_entry_exit_surfaces(
            matrix
        )
    )

    assert not surfaces.empty

    assert set(
        surfaces[
            "recommended_action"
        ]
    ).issubset({
        "ENTER",
        "AVOID",
        "INSUFFICIENT_EVIDENCE",
    })

    entered = surfaces[
        surfaces[
            "recommended_action"
        ].eq("ENTER")
    ]

    assert not entered.empty

    assert entered[
        "recommended_direction"
    ].isin([
        "LONG",
        "SHORT",
    ]).all()


def test_minimum_sample_is_enforced() -> None:
    matrix = build_surface_matrix(
        _observations(periods=20),
        config=MorphologySurfaceConfig(
            horizons=(1, 4),
            minimum_observations=1000,
            confidence_target=1000,
            quantile_bins=2,
        ),
    )

    assert (
        matrix["eligible"]
        == False
    ).all()
