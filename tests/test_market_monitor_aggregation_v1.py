from __future__ import annotations

from atlas.investment.market_monitor import (
    Venue,
    VenueTicker,
    consolidate_tickers,
)


def ticker(
    venue: Venue,
    bid: float,
    ask: float,
    last: float,
) -> VenueTicker:
    return VenueTicker(
        venue=venue,
        symbol="BTC-USD",
        bid=bid,
        ask=ask,
        bid_quantity=1,
        ask_quantity=1,
        last=last,
        volume_24h=100,
        timestamp="2026-01-01T00:00:00+00:00",
        received_at="2026-01-01T00:00:01+00:00",
    )


def test_consolidation_selects_best_prices() -> None:
    result = consolidate_tickers(
        [
            ticker(Venue.COINBASE, 60000, 60002, 60001),
            ticker(Venue.KRAKEN, 60001, 60003, 60002),
        ],
        symbol="BTC-USD",
        generated_at="2026-01-01T00:00:02+00:00",
    )

    assert result.best_bid == 60001
    assert result.best_bid_venue == Venue.KRAKEN
    assert result.best_ask == 60002
    assert result.best_ask_venue == Venue.COINBASE
    assert result.venue_count == 2
    assert result.paper_only is True
    assert result.live_execution is False
