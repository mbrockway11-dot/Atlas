"""Coinbase public market-data WebSocket collector."""

from __future__ import annotations

import json
from typing import Any

from ..coinbase import build_coinbase_subscription, parse_coinbase_ticker
from ..contracts import Venue, VenueTicker
from .base import PublicWebSocketCollector, WebSocketConnection, utc_now


class CoinbasePublicTickerCollector(PublicWebSocketCollector):
    venue = Venue.COINBASE
    url = "wss://advanced-trade-ws.coinbase.com"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._last_sequence: int | None = None

    async def subscribe(self, connection: WebSocketConnection) -> None:
        message = build_coinbase_subscription(list(self.config.symbols))
        # Public market subscription: deliberately no jwt field.
        await connection.send(json.dumps(message, separators=(",", ":")))

    def parse_message(self, raw: str | bytes) -> list[VenueTicker]:
        payload = json.loads(
            raw.decode("utf-8") if isinstance(raw, bytes) else raw
        )
        if not isinstance(payload, dict):
            return []

        channel = str(payload.get("channel", ""))
        if channel in {"subscriptions", "heartbeats"}:
            return []
        if payload.get("type") in {"subscriptions", "heartbeat"}:
            return []

        sequence = payload.get("sequence_num")
        if sequence is not None:
            sequence = int(sequence)
            if self._last_sequence is not None:
                if sequence > self._last_sequence + 1:
                    self.metrics.sequence_gaps += 1
                elif sequence <= self._last_sequence:
                    self.metrics.out_of_order_messages += 1
                    return []
            self._last_sequence = sequence

        events = payload.get("events")
        if not isinstance(events, list):
            return []

        tickers: list[VenueTicker] = []
        received_at = utc_now()
        for event in events:
            if not isinstance(event, dict):
                continue
            entries = event.get("tickers", [])
            if not isinstance(entries, list):
                continue
            for item in entries:
                if not isinstance(item, dict):
                    continue
                isolated: dict[str, Any] = {
                    "sequence_num": sequence,
                    "timestamp": payload.get("timestamp"),
                    "events": [{"tickers": [item]}],
                }
                tickers.append(
                    parse_coinbase_ticker(
                        isolated,
                        received_at=received_at,
                    )
                )
        return tickers


__all__ = ["CoinbasePublicTickerCollector"]
