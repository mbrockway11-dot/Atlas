"""Tests for read-only provider diagnostics."""

from __future__ import annotations

from atlas.investment.market_data import (
    QuoteSnapshot,
    StaticMarketDataProvider,
    diagnose_provider,
)


def test_provider_diagnostics_report_success():
    provider = StaticMarketDataProvider(
        quotes={
            "BTC-USD": QuoteSnapshot(
                symbol="BTC-USD",
                provider="STATIC",
                as_of=(
                    "2026-07-13T16:00:00+00:00"
                ),
                last=50000.0,
                bid=49990.0,
                ask=50010.0,
            )
        }
    )

    report = diagnose_provider(
        provider,
        symbols=[
            "BTC-USD"
        ],
        maximum_spread_bps=10.0,
    )

    assert report["success"]

    assert report["counts"] == {
        "requested": 1,
        "successful": 1,
        "failed": 0,
    }

    assert report[
        "contract"
    ][
        "read_only"
    ]


def test_provider_diagnostics_capture_failure():
    provider = StaticMarketDataProvider()

    report = diagnose_provider(
        provider,
        symbols=[
            "BTC-USD"
        ],
    )

    assert not report["success"]
    assert report["counts"][
        "failed"
    ] == 1
