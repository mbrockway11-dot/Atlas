"""Tests for historical Alpha Engine validation."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.engines.validation import (
    build_validation_segments,
    classify_engine_status,
)


def sample_trades() -> pd.DataFrame:
    rows = []

    for index in range(120):
        rows.append({
            "engine_id": "good_engine",
            "timestamp": (
                pd.Timestamp(
                    "2025-01-01",
                    tz="UTC",
                )
                + pd.Timedelta(
                    days=index
                )
            ),
            "asset": (
                "BTC-USD"
                if index % 2 == 0
                else "ETH-USD"
            ),
            "direction": "LONG",
            "regime": "UPTREND",
            "strategy_return": (
                0.03
                if index % 3 != 0
                else -0.01
            ),
        })

    for index in range(120):
        rows.append({
            "engine_id": "bad_engine",
            "timestamp": (
                pd.Timestamp(
                    "2025-01-01",
                    tz="UTC",
                )
                + pd.Timedelta(
                    days=index
                )
            ),
            "asset": "BTC-USD",
            "direction": "LONG",
            "regime": "NEUTRAL",
            "strategy_return": (
                0.01
                if index % 3 == 0
                else -0.02
            ),
        })

    return pd.DataFrame(rows)


def test_validation_builds_expected_segments():
    validation = build_validation_segments(
        sample_trades(),
        cost_bps=10.0,
    )

    assert not validation.empty

    assert {
        "overall",
        "direction",
        "asset",
        "regime",
        "year",
    }.issubset(
        set(
            validation[
                "segment_type"
            ]
        )
    )


def test_validation_applies_transaction_costs():
    trades = pd.DataFrame([
        {
            "engine_id": "test",
            "timestamp": "2025-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "direction": "LONG",
            "regime": "TEST",
            "strategy_return": 0.01,
        }
    ])

    validation = build_validation_segments(
        trades,
        cost_bps=10.0,
    )

    overall = validation[
        validation["segment_type"].eq(
            "overall"
        )
    ].iloc[0]

    assert float(
        overall["mean_return"]
    ) == 0.009


def test_engine_status_classification():
    validation = build_validation_segments(
        sample_trades(),
        cost_bps=10.0,
    )

    statuses = {
        row["engine_id"]: row["status"]
        for row in classify_engine_status(
            validation
        )
    }

    assert (
        statuses["good_engine"]
        == "VALIDATION_CANDIDATE"
    )

    assert statuses["bad_engine"] == "REJECT"
