from __future__ import annotations

from datetime import datetime, timezone

from atlas.investment.market_monitor import (
    Venue,
    VenueHealthState,
    VenueTicker,
    evaluate_venue_health,
)


def test_stale_ticker_is_detected() -> None:
    ticker = VenueTicker(
        venue=Venue.COINBASE,
        symbol="BTC-USD",
        bid=1,
        ask=2,
        bid_quantity=1,
        ask_quantity=1,
        last=1.5,
        volume_24h=1,
        timestamp="2026-01-01T00:00:00+00:00",
        received_at="2026-01-01T00:00:00+00:00",
    )

    health = evaluate_venue_health(
        ticker,
        now=datetime(2026, 1, 1, 0, 0, 20, tzinfo=timezone.utc),
        degraded_after_seconds=5,
        stale_after_seconds=15,
    )

    assert health.state == VenueHealthState.STALE
