"""Multi-venue public market-feed supervisor for Atlas G.23 Section 2."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

from .aggregation import consolidate_tickers
from .collectors import (
    CoinbasePublicTickerCollector,
    CollectorConfig,
    KrakenPublicTickerCollector,
    PublicWebSocketCollector,
)
from .contracts import Venue, VenueTicker
from .event_bridge import MarketEventBridge
from .health import evaluate_venue_health
from .snapshot import atomic_write_json, build_snapshot_payload


@dataclass(frozen=True)
class SupervisorConfig:
    symbols: tuple[str, ...] = ("BTC-USD", "ETH-USD", "SOL-USD")
    enable_coinbase: bool = True
    enable_kraken: bool = True
    enable_binance: bool = False
    snapshot_interval_seconds: float = 1.0
    degraded_after_seconds: float = 5.0
    stale_after_seconds: float = 15.0

    def __post_init__(self) -> None:
        if not self.symbols:
            raise ValueError("At least one symbol is required")
        if not self.enable_coinbase and not self.enable_kraken:
            raise ValueError("At least one USD venue must be enabled")
        if self.snapshot_interval_seconds <= 0:
            raise ValueError("snapshot_interval_seconds must be positive")
        if self.enable_binance:
            raise ValueError(
                "Binance remains disabled in G.23 Section 2; "
                "USDT basis handling is required first"
            )


class MarketMonitorSupervisor:
    def __init__(
        self,
        *,
        config: SupervisorConfig,
        output_dir: Path,
        event_bridge: MarketEventBridge | None = None,
        collector_factory: (
            Callable[
                [Venue, CollectorConfig, Callable[[VenueTicker], Awaitable[None]]],
                PublicWebSocketCollector,
            ]
            | None
        ) = None,
    ) -> None:
        self.config = config
        self.output_dir = output_dir
        self.event_bridge = event_bridge
        self.collector_factory = collector_factory or self._default_collector_factory
        self.latest_by_venue_symbol: dict[tuple[Venue, str], VenueTicker] = {}
        self.collectors: list[PublicWebSocketCollector] = []
        self.snapshots_written = 0
        self._stop_event = asyncio.Event()

    async def on_ticker(self, ticker: VenueTicker) -> None:
        self.latest_by_venue_symbol[(ticker.venue, ticker.symbol)] = ticker
        if self.event_bridge is not None:
            await self.event_bridge.publish(ticker)

    async def run(self, *, run_seconds: float | None = None) -> None:
        collector_config = CollectorConfig(symbols=self.config.symbols)
        venues: list[Venue] = []
        if self.config.enable_coinbase:
            venues.append(Venue.COINBASE)
        if self.config.enable_kraken:
            venues.append(Venue.KRAKEN)

        self.collectors = [
            self.collector_factory(venue, collector_config, self.on_ticker)
            for venue in venues
        ]
        tasks = [
            asyncio.create_task(collector.run(), name=f"{collector.venue.value}-collector")
            for collector in self.collectors
        ]
        snapshot_task = asyncio.create_task(
            self._snapshot_loop(),
            name="market-monitor-snapshot",
        )
        tasks.append(snapshot_task)

        timer_task: asyncio.Task | None = None
        if run_seconds is not None:
            timer_task = asyncio.create_task(self._stop_after(run_seconds))
            tasks.append(timer_task)

        try:
            await self._stop_event.wait()
        finally:
            for collector in self.collectors:
                await collector.stop()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.write_status()

    async def stop(self) -> None:
        self._stop_event.set()

    async def _stop_after(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
        await self.stop()

    async def _snapshot_loop(self) -> None:
        while not self._stop_event.is_set():
            await self.write_snapshots()
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.config.snapshot_interval_seconds,
                )
            except asyncio.TimeoutError:
                pass

    async def write_snapshots(self) -> None:
        for symbol in self.config.symbols:
            tickers = [
                ticker
                for (_, ticker_symbol), ticker in self.latest_by_venue_symbol.items()
                if ticker_symbol == symbol
            ]
            health = [
                evaluate_venue_health(
                    ticker,
                    degraded_after_seconds=self.config.degraded_after_seconds,
                    stale_after_seconds=self.config.stale_after_seconds,
                )
                for ticker in tickers
            ]
            healthy_venues = {
                item.venue
                for item in health
                if item.state.value in {"HEALTHY", "DEGRADED"}
            }
            included = [
                ticker for ticker in tickers if ticker.venue in healthy_venues
            ]
            if not included:
                continue
            consolidated = consolidate_tickers(included, symbol=symbol)
            payload = build_snapshot_payload(
                tickers=tickers,
                health=health,
                consolidated=consolidated,
            )
            safe_symbol = symbol.replace("/", "-")
            atomic_write_json(
                self.output_dir / f"{safe_symbol}.json",
                payload,
            )
            self.snapshots_written += 1

    async def write_status(self) -> None:
        payload = {
            "schema_version": "g23.public_monitor.status.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(self.config),
            "collectors": [asdict(collector.metrics) for collector in self.collectors],
            "snapshots_written": self.snapshots_written,
            "latest_ticker_count": len(self.latest_by_venue_symbol),
            "paper_only": True,
            "live_execution": False,
            "credentials_used": False,
        }
        for collector in payload["collectors"]:
            collector["venue"] = collector["venue"].value
            collector["state"] = collector["state"].value
        atomic_write_json(self.output_dir / "monitor_status.json", payload)

    @staticmethod
    def _default_collector_factory(
        venue: Venue,
        config: CollectorConfig,
        on_ticker: Callable[[VenueTicker], Awaitable[None]],
    ) -> PublicWebSocketCollector:
        if venue == Venue.COINBASE:
            return CoinbasePublicTickerCollector(
                config=config,
                on_ticker=on_ticker,
            )
        if venue == Venue.KRAKEN:
            return KrakenPublicTickerCollector(
                config=config,
                on_ticker=on_ticker,
            )
        raise ValueError(f"Unsupported enabled venue: {venue.value}")


__all__ = ["MarketMonitorSupervisor", "SupervisorConfig"]
