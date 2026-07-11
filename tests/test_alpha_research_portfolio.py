"""Tests for exposure-aware Research Lab portfolio curves."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.research_lab.portfolio import (
    build_engine_portfolio_curves,
    summarize_portfolio_curves,
)


def test_portfolio_curve_marks_active_trade_daily():
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
        {
            "timestamp": "2026-01-03T00:00:00Z",
            "asset": "BTC-USD",
            "close": 121.0,
        },
    ])

    trades = pd.DataFrame([
        {
            "engine_id": "test_engine",
            "timestamp": "2026-01-01T00:00:00Z",
            "exit_timestamp": "2026-01-03T00:00:00Z",
            "asset": "BTC-USD",
            "direction": "LONG",
        }
    ])

    curves = build_engine_portfolio_curves(
        trades,
        market,
        transaction_cost_bps=0.0,
    )

    assert not curves.empty

    invested = curves[
        curves["active_positions"] > 0
    ]

    assert len(invested) == 2

    assert round(
        float(
            invested.iloc[1][
                "portfolio_return"
            ]
        ),
        8,
    ) == 0.10


def test_short_trade_inverts_daily_return():
    market = pd.DataFrame([
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "close": 100.0,
        },
        {
            "timestamp": "2026-01-02T00:00:00Z",
            "asset": "BTC-USD",
            "close": 90.0,
        },
    ])

    trades = pd.DataFrame([
        {
            "engine_id": "test_engine",
            "timestamp": "2026-01-01T00:00:00Z",
            "exit_timestamp": "2026-01-02T12:00:00Z",
            "asset": "BTC-USD",
            "direction": "SHORT",
        }
    ])

    curves = build_engine_portfolio_curves(
        trades,
        market,
        transaction_cost_bps=0.0,
    )

    observed = curves[
        curves["timestamp"]
        == pd.Timestamp(
            "2026-01-02",
            tz="UTC",
        )
    ].iloc[0]

    assert round(
        float(
            observed[
                "portfolio_return"
            ]
        ),
        8,
    ) == 0.10


def test_portfolio_summary_contains_risk_metrics():
    market = pd.DataFrame([
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "close": 100.0,
        },
        {
            "timestamp": "2026-01-02T00:00:00Z",
            "asset": "BTC-USD",
            "close": 105.0,
        },
        {
            "timestamp": "2026-01-03T00:00:00Z",
            "asset": "BTC-USD",
            "close": 103.0,
        },
    ])

    trades = pd.DataFrame([
        {
            "engine_id": "test_engine",
            "timestamp": "2026-01-01T00:00:00Z",
            "exit_timestamp": "2026-01-04T00:00:00Z",
            "asset": "BTC-USD",
            "direction": "LONG",
        }
    ])

    curves = build_engine_portfolio_curves(
        trades,
        market,
        transaction_cost_bps=0.0,
    )

    summary = summarize_portfolio_curves(
        curves
    )

    assert len(summary) == 1
    assert "portfolio_max_drawdown" in summary.columns
    assert "portfolio_sharpe" in summary.columns


def test_entry_day_return_is_not_owned():
    market = pd.DataFrame([
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "close": 100.0,
        },
        {
            "timestamp": "2026-01-02T00:00:00Z",
            "asset": "BTC-USD",
            "close": 150.0,
        },
        {
            "timestamp": "2026-01-03T00:00:00Z",
            "asset": "BTC-USD",
            "close": 165.0,
        },
    ])

    trades = pd.DataFrame([
        {
            "engine_id": "test_engine",
            "timestamp": "2026-01-02T00:00:00Z",
            "exit_timestamp": "2026-01-03T00:00:00Z",
            "asset": "BTC-USD",
            "direction": "LONG",
        }
    ])

    curves = build_engine_portfolio_curves(
        trades,
        market,
        transaction_cost_bps=0.0,
    )

    entry_day = curves[
        curves["timestamp"]
        == pd.Timestamp(
            "2026-01-02",
            tz="UTC",
        )
    ].iloc[0]

    exit_day = curves[
        curves["timestamp"]
        == pd.Timestamp(
            "2026-01-03",
            tz="UTC",
        )
    ].iloc[0]

    assert float(
        entry_day["portfolio_return"]
    ) == 0.0

    assert round(
        float(
            exit_day["portfolio_return"]
        ),
        8,
    ) == 0.10
