"""Tests for canonical market-data contracts."""

from __future__ import annotations

import pytest

from atlas.investment.market_data import (
    MarketBar,
    QuoteSnapshot,
)


def test_quote_computes_spread():
    quote = QuoteSnapshot(
        symbol="BTC-USD",
        provider="STATIC",
        as_of=(
            "2026-07-13T16:00:00+00:00"
        ),
        last=50_000.0,
        bid=49_990.0,
        ask=50_010.0,
    )

    assert quote.midpoint == 50_000.0
    assert quote.spread == 20.0
    assert quote.spread_bps == 4.0


def test_crossed_quote_is_rejected():
    with pytest.raises(
        ValueError,
        match="bid cannot exceed ask",
    ):
        QuoteSnapshot(
            symbol="BTC-USD",
            provider="STATIC",
            as_of=(
                "2026-07-13T16:00:00+00:00"
            ),
            last=50_000.0,
            bid=50_010.0,
            ask=49_990.0,
        )


def test_invalid_ohlc_is_rejected():
    with pytest.raises(
        ValueError,
        match="Bar high is inconsistent",
    ):
        MarketBar(
            symbol="BTC-USD",
            provider="STATIC",
            interval="1H",
            start_at=(
                "2026-07-13T15:00:00+00:00"
            ),
            end_at=(
                "2026-07-13T16:00:00+00:00"
            ),
            open=100.0,
            high=90.0,
            low=80.0,
            close=95.0,
        )
