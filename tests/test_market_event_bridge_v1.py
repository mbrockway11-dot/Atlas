from __future__ import annotations

import asyncio
from pathlib import Path

from atlas.investment.events import EventStore
from atlas.investment.market_monitor import (
    MarketEventBridge,
    Venue,
    VenueTicker,
)


def test_ticker_publishes_market_data_event(tmp_path: Path) -> None:
    store = EventStore(output_dir=tmp_path)
    bridge = MarketEventBridge(event_store=store)
    ticker = VenueTicker(
        venue=Venue.COINBASE,
        symbol="BTC-USD",
        bid=100,
        ask=101,
        bid_quantity=1,
        ask_quantity=1,
        last=100.5,
        volume_24h=100,
        timestamp="2026-01-01T00:00:00+00:00",
        received_at="2026-01-01T00:00:01+00:00",
        sequence=1,
    )

    asyncio.run(bridge.publish(ticker))
    records = store.all()

    assert len(records) == 1
    assert records[0]["event_type"] == "MARKET_DATA"
    assert records[0]["aggregate_id"] == "BTC-USD"
    assert records[0]["paper_only"] is True
    assert records[0]["live_execution"] is False
    assert records[0]["credentials_used"] is False
