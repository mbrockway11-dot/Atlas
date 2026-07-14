from __future__ import annotations

import asyncio
from pathlib import Path

from atlas.investment.market_monitor import (
    CollectorConfig,
    MarketMonitorSupervisor,
    PublicWebSocketCollector,
    SupervisorConfig,
    Venue,
    VenueTicker,
)


class FakeCollector(PublicWebSocketCollector):
    url = "wss://example.invalid"

    def __init__(self, *, venue: Venue, **kwargs) -> None:
        self.venue = venue
        super().__init__(**kwargs)

    async def run(self) -> None:
        await self.on_ticker(
            VenueTicker(
                venue=self.venue,
                symbol="BTC-USD",
                bid=100 if self.venue == Venue.COINBASE else 101,
                ask=102 if self.venue == Venue.COINBASE else 103,
                bid_quantity=1,
                ask_quantity=1,
                last=101,
                volume_24h=100,
                timestamp="2026-01-01T00:00:00+00:00",
                received_at="2999-01-01T00:00:00+00:00",
            )
        )
        await self._stop_event.wait()

    async def subscribe(self, connection) -> None:
        return None

    def parse_message(self, raw):
        return []


def test_supervisor_writes_consolidated_snapshot(tmp_path: Path) -> None:
    def factory(venue, config, on_ticker):
        return FakeCollector(venue=venue, config=config, on_ticker=on_ticker)

    supervisor = MarketMonitorSupervisor(
        config=SupervisorConfig(
            symbols=("BTC-USD",),
            snapshot_interval_seconds=0.01,
        ),
        output_dir=tmp_path,
        collector_factory=factory,
    )

    asyncio.run(supervisor.run(run_seconds=0.05))

    assert (tmp_path / "BTC-USD.json").exists()
    assert (tmp_path / "monitor_status.json").exists()
    assert supervisor.snapshots_written >= 1


def test_binance_cannot_be_enabled_before_basis_layer(tmp_path: Path) -> None:
    try:
        SupervisorConfig(enable_binance=True)
    except ValueError as exc:
        assert "USDT basis" in str(exc)
    else:
        raise AssertionError("Expected Binance safety rejection")
