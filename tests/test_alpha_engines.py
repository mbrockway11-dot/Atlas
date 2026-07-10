"""Tests for Atlas Alpha Engine Framework v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.engines import (
    registered_engines,
)
from atlas.investment.alpha.engines.base import (
    score_to_direction,
    score_to_signal,
)
from atlas.investment.alpha.engines.schema import (
    ENGINE_SIGNAL_COLUMNS,
)


def sample_market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": "2026-07-01T00:00:00Z",
                "asset": "BTC-USD",
                "close": 100.0,
                "return_1d": 0.02,
                "return_7d": 0.08,
                "return_30d": 0.15,
                "momentum_30d": 0.14,
                "momentum_90d": 0.35,
                "volatility_7d": 0.50,
                "volatility_30d": 0.25,
                "trend_state": "UPTREND",
                "cross_sectional_percentile": 0.90,
            },
            {
                "timestamp": "2026-07-01T00:00:00Z",
                "asset": "ETH-USD",
                "close": 50.0,
                "return_1d": -0.02,
                "return_7d": -0.08,
                "return_30d": -0.15,
                "momentum_30d": -0.14,
                "momentum_90d": -0.35,
                "volatility_7d": 0.50,
                "volatility_30d": 0.25,
                "trend_state": "DOWNTREND",
                "cross_sectional_percentile": 0.10,
            },
        ]
    )


def test_registry_contains_unique_engines():
    engines = registered_engines()
    engine_ids = [
        engine.metadata.engine_id
        for engine in engines
    ]

    assert len(engines) == 3
    assert len(engine_ids) == len(set(engine_ids))


def test_all_engines_emit_canonical_columns():
    market = sample_market_frame()

    for engine in registered_engines():
        signals = engine.run(market)

        assert not signals.empty
        assert list(signals.columns) == ENGINE_SIGNAL_COLUMNS
        assert len(signals) == len(market)
        assert signals["engine_id"].nunique() == 1
        assert signals["asset"].nunique() == 2


def test_scores_and_confidence_are_bounded():
    market = sample_market_frame()

    for engine in registered_engines():
        signals = engine.run(market)

        assert signals["normalized_score"].between(
            0.0,
            1.0,
        ).all()

        assert signals["confidence"].between(
            0.0,
            1.0,
        ).all()

        assert signals["conviction"].between(
            0.0,
            1.0,
        ).all()


def test_direction_and_signal_are_consistent():
    for score in [
        0.0,
        0.20,
        0.30,
        0.40,
        0.41,
        0.50,
        0.59,
        0.60,
        0.70,
        1.0,
    ]:
        direction = score_to_direction(score)
        signal = score_to_signal(
            score,
            confidence=1.0,
        )

        if direction == "LONG":
            assert signal in {
                "LONG",
                "STRONG_LONG",
            }

        elif direction == "SHORT":
            assert signal in {
                "SHORT",
                "STRONG_SHORT",
            }

        else:
            assert signal == "NEUTRAL"


def test_low_confidence_suppresses_signal():
    assert (
        score_to_signal(
            0.95,
            confidence=0.20,
        )
        == "INSUFFICIENT_EVIDENCE"
    )
