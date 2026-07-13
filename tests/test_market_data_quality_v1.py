"""Tests for quote freshness and market-data quality."""

from __future__ import annotations

from datetime import UTC, datetime

from atlas.investment.market_data import (
    QuoteSnapshot,
    evaluate_quote_quality,
)


NOW = datetime(
    2026,
    7,
    13,
    16,
    0,
    tzinfo=UTC,
)


def test_stale_quote_fails():
    quote = QuoteSnapshot(
        symbol="ETH-USD",
        provider="STATIC",
        as_of=(
            "2026-07-13T15:00:00+00:00"
        ),
        last=2_000.0,
    )

    quality = evaluate_quote_quality(
        quote,
        maximum_age_seconds=60.0,
        now=NOW,
    )

    assert not quality["valid"]

    assert any(
        value.startswith(
            "STALE_QUOTE"
        )
        for value
        in quality["errors"]
    )


def test_wide_spread_fails():
    quote = QuoteSnapshot(
        symbol="ETH-USD",
        provider="STATIC",
        as_of=(
            "2026-07-13T15:59:55+00:00"
        ),
        last=2_000.0,
        bid=1_990.0,
        ask=2_010.0,
    )

    quality = evaluate_quote_quality(
        quote,
        maximum_age_seconds=60.0,
        maximum_spread_bps=50.0,
        now=NOW,
    )

    assert not quality["valid"]

    assert any(
        value.startswith(
            "SPREAD_LIMIT_EXCEEDED"
        )
        for value
        in quality["errors"]
    )
