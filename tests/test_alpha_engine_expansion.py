"""Tests for Alpha Engine Expansion v2."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.engines.drawdown_recovery import (
    DrawdownRecoveryEngine,
)
from atlas.investment.alpha.engines.market_breadth import (
    MarketBreadthEngine,
)
from atlas.investment.alpha.engines.mean_reversion import (
    MeanReversionEngine,
)
from atlas.investment.alpha.engines.volatility_compression import (
    VolatilityCompressionEngine,
)


def expanded_market_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp": "2026-07-01T00:00:00Z",
            "asset": "BTC-USD",
            "close": 100.0,
            "return_1d": 0.02,
            "return_7d": 0.10,
            "return_14d": 0.12,
            "return_30d": 0.15,
            "momentum_14d": 0.12,
            "momentum_30d": 0.15,
            "momentum_90d": 0.25,
            "volatility_7d": 0.15,
            "volatility_30d": 0.30,
            "atr_pct_14d": 0.04,
            "distance_sma_7d": 0.05,
            "distance_sma_14d": 0.07,
            "distance_sma_30d": 0.10,
            "drawdown_from_90d_high": -0.10,
            "volume_ratio_30d": 1.25,
            "trend_state": "UPTREND",
            "cross_sectional_percentile": 0.90,
        },
        {
            "timestamp": "2026-07-01T00:00:00Z",
            "asset": "ETH-USD",
            "close": 50.0,
            "return_1d": -0.02,
            "return_7d": -0.12,
            "return_14d": -0.15,
            "return_30d": -0.20,
            "momentum_14d": -0.14,
            "momentum_30d": -0.18,
            "momentum_90d": -0.25,
            "volatility_7d": 0.14,
            "volatility_30d": 0.32,
            "atr_pct_14d": 0.05,
            "distance_sma_7d": -0.06,
            "distance_sma_14d": -0.08,
            "distance_sma_30d": -0.12,
            "drawdown_from_90d_high": -0.35,
            "volume_ratio_30d": 1.10,
            "trend_state": "DOWNTREND",
            "cross_sectional_percentile": 0.10,
        },
    ])


def expanded_engines():
    return [
        MeanReversionEngine(),
        VolatilityCompressionEngine(),
        MarketBreadthEngine(),
        DrawdownRecoveryEngine(),
    ]


def test_expansion_engines_emit_one_row_per_asset():
    market = expanded_market_frame()

    for engine in expanded_engines():
        signals = engine.run(market)

        assert len(signals) == len(market)
        assert signals["asset"].nunique() == 2
        assert signals["engine_id"].nunique() == 1


def test_expansion_scores_are_bounded():
    market = expanded_market_frame()

    for engine in expanded_engines():
        signals = engine.run(market)

        assert signals[
            "normalized_score"
        ].between(
            0.0,
            1.0,
        ).all()

        assert signals[
            "confidence"
        ].between(
            0.0,
            1.0,
        ).all()


def test_mean_reversion_inverts_extreme_direction():
    signals = MeanReversionEngine().run(
        expanded_market_frame()
    )

    btc = signals[
        signals["asset"].eq("BTC-USD")
    ].iloc[0]

    eth = signals[
        signals["asset"].eq("ETH-USD")
    ].iloc[0]

    assert (
        float(eth["normalized_score"])
        > float(btc["normalized_score"])
    )


def test_breadth_is_common_but_asset_adjusted():
    signals = MarketBreadthEngine().run(
        expanded_market_frame()
    )

    assert len(signals) == 2

    scores = signals.set_index(
        "asset"
    )["normalized_score"]

    assert (
        float(scores["BTC-USD"])
        != float(scores["ETH-USD"])
    )


def test_expansion_engine_ids_are_unique():
    engine_ids = [
        engine.metadata.engine_id
        for engine in expanded_engines()
    ]

    assert len(engine_ids) == len(
        set(engine_ids)
    )
