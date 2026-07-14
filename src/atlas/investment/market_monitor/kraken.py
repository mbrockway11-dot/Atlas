"""Kraken WebSocket v2 public ticker normalization for Atlas G.23."""

from __future__ import annotations

from typing import Any, Mapping

from .contracts import Venue, VenueTicker
from .errors import MarketDataValidationError
from .normalization import normalize_symbol, utc_now, validate_ticker


def build_kraken_subscription(symbols: list[str]) -> dict[str, Any]:
    return {
        "method": "subscribe",
        "params": {
            "channel": "ticker",
            "symbol": [
                normalize_symbol(symbol).replace("-", "/")
                for symbol in symbols
            ],
            "event_trigger": "bbo",
            "snapshot": True,
        },
    }


def parse_kraken_ticker(
    payload: Mapping[str, Any],
    *,
    received_at: str | None = None,
) -> VenueTicker:
    data = payload.get("data", [])
    if not isinstance(data, list) or not data:
        raise MarketDataValidationError("Kraken ticker payload has no data")
    item = data[0]

    try:
        ticker = VenueTicker(
            venue=Venue.KRAKEN,
            symbol=normalize_symbol(str(item["symbol"])),
            bid=float(item["bid"]),
            ask=float(item["ask"]),
            bid_quantity=float(item.get("bid_qty", 0.0)),
            ask_quantity=float(item.get("ask_qty", 0.0)),
            last=float(item["last"]),
            volume_24h=float(item.get("volume", 0.0)),
            timestamp=str(item.get("timestamp") or received_at or utc_now()),
            received_at=received_at or utc_now(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MarketDataValidationError(
            "Malformed Kraken ticker payload"
        ) from exc

    validate_ticker(ticker)
    return ticker


__all__ = ["build_kraken_subscription", "parse_kraken_ticker"]
