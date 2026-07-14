"""Bridge canonical market tickers into the G.22 event store."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from atlas.investment.events import AtlasEvent, EventStore, EventType

from .contracts import VenueTicker


def _event_id(ticker: VenueTicker) -> str:
    payload = {
        "venue": ticker.venue.value,
        "symbol": ticker.symbol,
        "timestamp": ticker.timestamp,
        "sequence": ticker.sequence,
        "bid": ticker.bid,
        "ask": ticker.ask,
        "last": ticker.last,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return f"market-{ticker.venue.value.lower()}-{digest}"


class MarketEventBridge:
    def __init__(self, *, event_store: EventStore) -> None:
        self.event_store = event_store
        self.events_published = 0
        self.duplicate_events = 0

    async def publish(self, ticker: VenueTicker) -> None:
        payload: dict[str, Any] = asdict(ticker)
        payload["venue"] = ticker.venue.value
        event = AtlasEvent(
            event_id=_event_id(ticker),
            event_type=EventType.MARKET_DATA,
            aggregate_type="market_symbol",
            aggregate_id=ticker.symbol,
            occurred_at=ticker.timestamp,
            source=f"public_ws:{ticker.venue.value.lower()}",
            payload=payload,
            correlation_id=f"market:{ticker.symbol}",
            paper_only=True,
            live_execution=False,
            credentials_used=False,
        )
        try:
            self.event_store.append(event)
            self.events_published += 1
        except Exception as exc:
            if type(exc).__name__ == "DuplicateEventError":
                self.duplicate_events += 1
                return
            raise


__all__ = ["MarketEventBridge"]
