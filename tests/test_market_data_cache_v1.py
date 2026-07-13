"""Tests for market-data provider TTL caching."""

from __future__ import annotations

from atlas.investment.market_data import (
    CachedMarketDataProvider,
    QuoteSnapshot,
    StaticMarketDataProvider,
)


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


def test_quote_cache_hits_before_expiry():
    clock = Clock()

    static = StaticMarketDataProvider(
        quotes={
            "BTC-USD": QuoteSnapshot(
                symbol="BTC-USD",
                provider="STATIC",
                as_of=(
                    "2026-07-13T16:00:00+00:00"
                ),
                last=50000.0,
            )
        }
    )

    cached = CachedMarketDataProvider(
        static,
        quote_ttl_seconds=5.0,
        monotonic_clock=clock,
    )

    first = cached.get_quote(
        "BTC"
    )

    clock.value = 4.0

    second = cached.get_quote(
        "BTC-USD"
    )

    assert first is second

    assert (
        cached.statistics()
        .to_dict()
    ) == {
        "quote_hits": 1,
        "quote_misses": 1,
        "bar_hits": 0,
        "bar_misses": 0,
    }


def test_cache_misses_after_expiry():
    clock = Clock()

    static = StaticMarketDataProvider(
        quotes={
            "BTC-USD": QuoteSnapshot(
                symbol="BTC-USD",
                provider="STATIC",
                as_of=(
                    "2026-07-13T16:00:00+00:00"
                ),
                last=50000.0,
            )
        }
    )

    cached = CachedMarketDataProvider(
        static,
        quote_ttl_seconds=5.0,
        monotonic_clock=clock,
    )

    cached.get_quote(
        "BTC-USD"
    )

    clock.value = 6.0

    cached.get_quote(
        "BTC-USD"
    )

    stats = (
        cached.statistics()
    )

    assert stats.quote_hits == 0
    assert stats.quote_misses == 2
