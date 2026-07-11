"""Tests for Regime Intelligence v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.regime_intelligence.classifier import (
    classify_regime,
)
from atlas.investment.regime_intelligence.features import (
    build_market_state_history,
)
from atlas.investment.regime_intelligence.suitability import (
    build_engine_suitability,
)


def sample_history() -> pd.DataFrame:
    rows = []

    for day in range(40):
        timestamp = (
            pd.Timestamp(
                "2026-01-01",
                tz="UTC",
            )
            + pd.Timedelta(
                days=day
            )
        )

        for index, asset in enumerate([
            "BTC-USD",
            "ETH-USD",
            "SOL-USD",
            "LINK-USD",
        ]):
            close = (
                100.0
                + day * 2.0
                + index
            )

            rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "close": close,
                "return_1d": 0.02,
                "return_7d": 0.08,
                "return_30d": 0.22,
                "momentum_30d": 0.22,
                "momentum_90d": 0.30,
                "volatility_7d": 0.30,
                "volatility_30d": 0.35,
                "atr_pct_14d": 0.04,
                "volume_ratio_30d": 1.25,
                "drawdown_from_90d_high": -0.03,
                "trend_state": "UPTREND",
            })

    return pd.DataFrame(rows)


def test_market_state_history_is_timestamp_level():
    state = build_market_state_history(
        sample_history()
    )

    assert len(state) == 40
    assert state[
        "timestamp"
    ].is_unique
    assert (
        state[
            "asset_count"
        ]
        == 4
    ).all()


def test_broad_trending_market_is_detected():
    state = build_market_state_history(
        sample_history()
    )

    report = classify_regime(
        state
    )

    assert report[
        "primary_regime"
    ] in {
        "BROAD_TRENDING_RISK_ON",
        "SELECTIVE_TRENDING_RISK_ON",
    }

    assert report[
        "confidence"
    ] > 0.0


def test_regime_report_is_deterministic():
    state = build_market_state_history(
        sample_history()
    )

    first = classify_regime(state)
    second = classify_regime(state)

    assert first == second


def test_engine_suitability_uses_family():
    engine_summary = pd.DataFrame([
        {
            "engine_id": "trend_engine",
            "family": "trend",
        },
        {
            "engine_id": "mean_engine",
            "family": "mean_reversion",
        },
    ])

    regime = {
        "regime": (
            "BROAD_TRENDING_RISK_ON"
        ),
        "primary_regime": (
            "BROAD_TRENDING_RISK_ON"
        ),
        "confidence": 1.0,
    }

    rows = build_engine_suitability(
        regime,
        engine_summary,
    )

    indexed = {
        row["engine_id"]: row
        for row in rows
    }

    assert (
        indexed[
            "trend_engine"
        ][
            "effective_suitability"
        ]
        > indexed[
            "mean_engine"
        ][
            "effective_suitability"
        ]
    )


def test_empty_history_returns_insufficient_data():
    report = classify_regime(
        pd.DataFrame()
    )

    assert (
        report["regime"]
        == "INSUFFICIENT_DATA"
    )
