"""Shared public WebSocket collector contracts for Atlas G.23 Section 2."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Awaitable, Callable, Protocol

from ..contracts import Venue, VenueTicker


class CollectorState(str, Enum):
    STOPPED = "STOPPED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"


@dataclass(frozen=True)
class CollectorConfig:
    symbols: tuple[str, ...]
    reconnect_initial_seconds: float = 1.0
    reconnect_max_seconds: float = 30.0
    receive_timeout_seconds: float = 20.0
    max_consecutive_failures: int = 20

    def __post_init__(self) -> None:
        if not self.symbols:
            raise ValueError("At least one symbol is required")
        if self.reconnect_initial_seconds <= 0:
            raise ValueError("reconnect_initial_seconds must be positive")
        if self.reconnect_max_seconds < self.reconnect_initial_seconds:
            raise ValueError(
                "reconnect_max_seconds cannot be below reconnect_initial_seconds"
            )
        if self.receive_timeout_seconds <= 0:
            raise ValueError("receive_timeout_seconds must be positive")
        if self.max_consecutive_failures < 1:
            raise ValueError("max_consecutive_failures must be positive")


@dataclass
class CollectorMetrics:
    venue: Venue
    state: CollectorState = CollectorState.STOPPED
    connections_opened: int = 0
    reconnects: int = 0
    messages_received: int = 0
    tickers_emitted: int = 0
    malformed_messages: int = 0
    sequence_gaps: int = 0
    out_of_order_messages: int = 0
    timeouts: int = 0
    consecutive_failures: int = 0
    last_connected_at: str | None = None
    last_message_at: str | None = None
    last_ticker_at: str | None = None
    last_error: str = ""


class WebSocketConnection(Protocol):
    async def send(self, message: str) -> None: ...
    async def recv(self) -> str | bytes: ...
    async def close(self) -> None: ...


ConnectionFactory = Callable[[str], Awaitable[WebSocketConnection]]
TickerHandler = Callable[[VenueTicker], Awaitable[None]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def default_connection_factory(url: str) -> WebSocketConnection:
    try:
        import websockets
    except ImportError as exc:
        raise RuntimeError(
            "The 'websockets' package is required. Install with: pip install websockets"
        ) from exc
    return await websockets.connect(
        url,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=5,
        max_queue=2048,
    )


class PublicWebSocketCollector:
    venue: Venue
    url: str

    def __init__(
        self,
        *,
        config: CollectorConfig,
        on_ticker: TickerHandler,
        connection_factory: ConnectionFactory | None = None,
    ) -> None:
        self.config = config
        self.on_ticker = on_ticker
        self.connection_factory = connection_factory or default_connection_factory
        self.metrics = CollectorMetrics(venue=self.venue)
        self._stop_event = asyncio.Event()
        self._connection: WebSocketConnection | None = None

    async def run(self) -> None:
        backoff = self.config.reconnect_initial_seconds

        while not self._stop_event.is_set():
            try:
                self.metrics.state = (
                    CollectorState.CONNECTING
                    if self.metrics.connections_opened == 0
                    else CollectorState.RECONNECTING
                )
                connection = await self.connection_factory(self.url)
                self._connection = connection
                self.metrics.connections_opened += 1
                if self.metrics.connections_opened > 1:
                    self.metrics.reconnects += 1
                self.metrics.state = CollectorState.CONNECTED
                self.metrics.last_connected_at = utc_now()
                self.metrics.consecutive_failures = 0
                backoff = self.config.reconnect_initial_seconds

                await self.subscribe(connection)
                await self._receive_loop(connection)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.metrics.last_error = f"{type(exc).__name__}: {exc}"
                self.metrics.consecutive_failures += 1
                if (
                    self.metrics.consecutive_failures
                    >= self.config.max_consecutive_failures
                ):
                    self.metrics.state = CollectorState.FAILED
                    return
                self.metrics.state = CollectorState.RECONNECTING
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=backoff,
                    )
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2.0, self.config.reconnect_max_seconds)
            finally:
                await self._close_connection()

        self.metrics.state = CollectorState.STOPPED

    async def stop(self) -> None:
        self._stop_event.set()
        await self._close_connection()

    async def _receive_loop(self, connection: WebSocketConnection) -> None:
        while not self._stop_event.is_set():
            try:
                raw = await asyncio.wait_for(
                    connection.recv(),
                    timeout=self.config.receive_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                self.metrics.timeouts += 1
                raise RuntimeError("Public market feed receive timeout") from exc

            self.metrics.messages_received += 1
            self.metrics.last_message_at = utc_now()
            try:
                tickers = self.parse_message(raw)
            except Exception:
                self.metrics.malformed_messages += 1
                continue

            for ticker in tickers:
                await self.on_ticker(ticker)
                self.metrics.tickers_emitted += 1
                self.metrics.last_ticker_at = utc_now()

    async def _close_connection(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is not None:
            try:
                await connection.close()
            except Exception:
                pass

    async def subscribe(self, connection: WebSocketConnection) -> None:
        raise NotImplementedError

    def parse_message(self, raw: str | bytes) -> list[VenueTicker]:
        raise NotImplementedError


__all__ = [
    "CollectorConfig",
    "CollectorMetrics",
    "CollectorState",
    "ConnectionFactory",
    "PublicWebSocketCollector",
    "TickerHandler",
    "WebSocketConnection",
    "default_connection_factory",
    "utc_now",
]
