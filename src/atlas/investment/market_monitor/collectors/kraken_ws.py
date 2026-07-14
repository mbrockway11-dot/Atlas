"""Kraken public WebSocket v2 ticker collector."""

from __future__ import annotations

import json
from typing import Any

from ..contracts import Venue, VenueTicker
from ..kraken import build_kraken_subscription, parse_kraken_ticker
from .base import PublicWebSocketCollector, WebSocketConnection, utc_now


class KrakenPublicTickerCollector(PublicWebSocketCollector):
    venue = Venue.KRAKEN
    url = "wss://ws.kraken.com/v2"

    async def subscribe(self, connection: WebSocketConnection) -> None:
        message = build_kraken_subscription(list(self.config.symbols))
        await connection.send(json.dumps(message, separators=(",", ":")))

    def parse_message(self, raw: str | bytes) -> list[VenueTicker]:
        payload = json.loads(
            raw.decode("utf-8") if isinstance(raw, bytes) else raw
        )
        if not isinstance(payload, dict):
            return []
        if payload.get("method") == "subscribe":
            return []
        if payload.get("channel") in {"heartbeat", "status"}:
            return []
        if payload.get("channel") != "ticker":
            return []

        data = payload.get("data")
        if not isinstance(data, list):
            return []

        received_at = utc_now()
        tickers: list[VenueTicker] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            isolated: dict[str, Any] = {
                "channel": "ticker",
                "type": payload.get("type", "update"),
                "data": [item],
            }
            tickers.append(
                parse_kraken_ticker(isolated, received_at=received_at)
            )
        return tickers


__all__ = ["KrakenPublicTickerCollector"]
