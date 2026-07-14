from __future__ import annotations

import pandas as pd
import pytest

from atlas.investment.lyfe_bridge.morphology_observations import (
    MorphologyObservationConfig,
    build_morphology_observations,
    future_window_max,
    future_window_min,
)


def _topology(periods: int = 8) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    return pd.DataFrame({
        "timestamp": timestamps,
        "rank_state": ["SOL>ETH>BTC"] * periods,
        "prior_rank_state": ["ETH>SOL>BTC"] * periods,
        "transition": [
            "ETH>SOL>BTC->SOL>ETH>BTC"
        ] * periods,
        "persistence_bars": list(range(1, periods + 1)),
        "entropy": [0.3] * periods,
        "leader": ["SOL"] * periods,
        "laggard": ["BTC"] * periods,
        "concentration": [0.7] * periods,
        "dispersion": [0.02] * periods,
        "transition_velocity": [0.04] * periods,
        "multi_timeframe_agreement": [0.8] * periods,
        "sol_fulcrum_score": [0.03] * periods,
        "next_rank_state": ["SOL>ETH>BTC"] * periods,
        "next_transition": [
            "SOL>ETH>BTC->SOL>ETH>BTC"
        ] * periods,
    })


def _market(periods: int = 8) -> pd.DataFrame:
    rows = []

    timestamps = pd.date_range(
        "2026-01-01",
        periods=periods,
        freq="15min",
        tz="UTC",
    )

    for asset, offset in (
        ("BTC", 100.0),
        ("ETH", 200.0),
        ("SOL", 300.0),
    ):
        for index, timestamp in enumerate(timestamps):
            open_price = offset + index

            rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "open": open_price,
                "high": open_price + 2.0,
                "low": open_price - 1.0,
                "close": open_price + 1.0,
                "volume": 1000.0,
            })

    return pd.DataFrame(rows)


def test_future_windows_use_only_future_bars() -> None:
    series = pd.Series(
        [1.0, 4.0, 2.0, 8.0, 3.0]
    )

    maximum = future_window_max(
        series,
        2,
    )

    minimum = future_window_min(
        series,
        2,
    )

    assert maximum.iloc[0] == 4.0
    assert minimum.iloc[0] == 2.0
    assert maximum.iloc[1] == 8.0
    assert minimum.iloc[1] == 2.0


def test_generator_creates_one_row_per_asset_timestamp() -> None:
    observations = build_morphology_observations(
        _topology(),
        _market(),
        config=MorphologyObservationConfig(
            horizons=(1, 2, 4),
            target_horizon=2,
        ),
    )

    assert set(observations["asset"]) == {
        "BTC",
        "ETH",
        "SOL",
    }

    assert observations["observation_id"].is_unique

    assert observations["engine_id"].eq(
        "LYFE_MORPHOLOGY_V1"
    ).all()


def test_trade_return_uses_target_horizon() -> None:
    observations = build_morphology_observations(
        _topology(),
        _market(),
        config=MorphologyObservationConfig(
            horizons=(1, 2, 4),
            target_horizon=2,
        ),
    )

    pd.testing.assert_series_equal(
        observations["trade_return"].reset_index(drop=True),
        observations["forward_return_2"].reset_index(drop=True),
        check_names=False,
    )


def test_generator_calculates_long_and_short_paths() -> None:
    observations = build_morphology_observations(
        _topology(),
        _market(),
        config=MorphologyObservationConfig(
            horizons=(1, 2),
            target_horizon=1,
        ),
    )

    row = observations.iloc[0]

    assert row["long_mfe_1"] > 0.0
    assert row["short_mae_1"] < 0.0

    assert row["long_mfe_2"] >= row["long_mfe_1"]
    assert row["short_mfe_2"] >= 0.0


def test_trailing_rows_without_future_path_are_removed() -> None:
    observations = build_morphology_observations(
        _topology(),
        _market(),
        config=MorphologyObservationConfig(
            horizons=(1, 4),
            target_horizon=4,
        ),
    )

    assert observations["forward_return_4"].notna().all()
    assert len(observations) == 12


def test_target_horizon_must_be_configured() -> None:
    with pytest.raises(
        ValueError,
        match="target_horizon",
    ):
        MorphologyObservationConfig(
            horizons=(1, 2, 4),
            target_horizon=8,
        )
