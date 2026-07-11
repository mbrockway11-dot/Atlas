"""Tests for historical Alpha Engine execution."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.engines.backtest_adapter import (
    build_engine_trades,
    direction_adjusted_return,
    non_overlapping_engine_trades,
)
from atlas.investment.alpha.engines.historical import (
    add_historical_cross_sectional_features,
)


def test_cross_sectional_features_are_added():
    market = pd.DataFrame([
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "momentum_30d": 0.20,
            "momentum_90d": 0.30,
            "return_14d": 0.10,
            "return_30d": 0.15,
        },
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "asset": "ETH-USD",
            "momentum_30d": -0.10,
            "momentum_90d": -0.20,
            "return_14d": -0.05,
            "return_30d": -0.10,
        },
    ])

    result = add_historical_cross_sectional_features(
        market
    )

    assert "cross_sectional_score" in result.columns
    assert "cross_sectional_rank" in result.columns
    assert "cross_sectional_percentile" in result.columns

    btc = result[
        result["asset"].eq("BTC-USD")
    ].iloc[0]

    eth = result[
        result["asset"].eq("ETH-USD")
    ].iloc[0]

    assert (
        btc["cross_sectional_score"]
        > eth["cross_sectional_score"]
    )

    assert (
        btc["cross_sectional_rank"]
        < eth["cross_sectional_rank"]
    )


def test_direction_adjusts_returns():
    long_row = pd.Series({
        "direction": "LONG",
        "forward_return": 0.10,
    })

    short_row = pd.Series({
        "direction": "SHORT",
        "forward_return": 0.10,
    })

    assert direction_adjusted_return(long_row) == 0.10
    assert direction_adjusted_return(short_row) == -0.10


def test_engine_trade_builder_uses_forward_close():
    market = pd.DataFrame([
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "close": 100.0,
        },
        {
            "timestamp": "2026-01-02T00:00:00Z",
            "asset": "BTC-USD",
            "close": 110.0,
        },
    ])

    signals = pd.DataFrame([
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "engine_id": "test_engine",
            "engine_version": "1",
            "family": "test",
            "direction": "LONG",
            "signal": "LONG",
            "holding_period": 1,
            "normalized_score": 0.70,
            "confidence": 0.80,
            "conviction": 0.56,
            "regime": "TEST",
            "reason_codes": "TEST",
        }
    ])

    trades = build_engine_trades(
        signals,
        market,
    )

    assert len(trades) == 1
    assert round(
        float(
            trades.iloc[0]["strategy_return"]
        ),
        8,
    ) == 0.10


def test_non_overlap_is_engine_and_asset_specific():
    trades = pd.DataFrame([
        {
            "engine_id": "engine_a",
            "engine_version": "1",
            "family": "test",
            "timestamp": "2026-01-01T00:00:00Z",
            "date": "2026-01-01T00:00:00Z",
            "exit_timestamp": "2026-01-04T00:00:00Z",
            "asset": "BTC-USD",
            "direction": "LONG",
            "signal": "LONG",
            "holding_period": 3,
            "entry_close": 100,
            "exit_close": 110,
            "forward_return": 0.10,
            "strategy_return": 0.10,
            "normalized_score": 0.70,
            "confidence": 0.80,
            "conviction": 0.56,
            "regime": "TEST",
            "reason_codes": "TEST",
        },
        {
            "engine_id": "engine_a",
            "engine_version": "1",
            "family": "test",
            "timestamp": "2026-01-02T00:00:00Z",
            "date": "2026-01-02T00:00:00Z",
            "exit_timestamp": "2026-01-05T00:00:00Z",
            "asset": "BTC-USD",
            "direction": "LONG",
            "signal": "LONG",
            "holding_period": 3,
            "entry_close": 101,
            "exit_close": 111,
            "forward_return": 0.099,
            "strategy_return": 0.099,
            "normalized_score": 0.70,
            "confidence": 0.80,
            "conviction": 0.56,
            "regime": "TEST",
            "reason_codes": "TEST",
        },
    ])

    result = non_overlapping_engine_trades(
        trades
    )

    assert len(result) == 1


