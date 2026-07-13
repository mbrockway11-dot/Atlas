"""Tests for market-data provider routing and fallback."""

from __future__ import annotations

from datetime import UTC, datetime

from atlas.investment.market_data import (
    MarketDataRouter,
    QuoteSnapshot,
    StaticMarketDataProvider,
)


NOW = datetime(
    2026,
    7,
    13,
    16,
    0,
    tzinfo=UTC,
)


def quote(
    provider: str,
    *,
    as_of: str,
) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol="BTC-USD",
        provider=provider,
        as_of=as_of,
        last=50_000.0,
        bid=49_990.0,
        ask=50_010.0,
    )


def test_router_falls_back_from_stale_provider():
    stale = StaticMarketDataProvider(
        name="STALE",
        quotes={
            "BTC-USD": quote(
                "STALE",
                as_of=(
                    "2026-07-13T14:00:00+00:00"
                ),
            )
        },
    )

    fresh = StaticMarketDataProvider(
        name="FRESH",
        quotes={
            "BTC-USD": quote(
                "FRESH",
                as_of=(
                    "2026-07-13T15:59:45+00:00"
                ),
            )
        },
    )

    router = MarketDataRouter([
        stale,
        fresh,
    ])

    resolved = router.get_quote(
        "BTC",
        maximum_age_seconds=60.0,
        now=NOW,
    )

    assert (
        resolved.provider
        == "FRESH"
    )


def test_snapshot_uses_canonical_aliases():
    provider = (
        StaticMarketDataProvider(
            quotes={
                "GLD": QuoteSnapshot(
                    symbol="GLD",
                    provider="STATIC",
                    as_of=(
                        "2026-07-13T15:59:45+00:00"
                    ),
                    last=300.0,
                )
            }
        )
    )

    router = MarketDataRouter([
        provider
    ])

    snapshot = (
        router.build_snapshot(
            ["gold"],
            maximum_age_seconds=60.0,
            now=NOW,
        )
    )

    assert snapshot["success"]

    assert (
        snapshot[
            "reference_prices"
        ][
            "GLD"
        ]
        == 300.0
    )
