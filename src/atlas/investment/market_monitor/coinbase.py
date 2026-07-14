"""Coinbase Advanced Trade public ticker normalization for Atlas G.23."""

from __future__ import annotations

from typing import Any, Mapping

from .contracts import Venue, VenueTicker
from .errors import MarketDataValidationError
from .normalization import normalize_symbol, utc_now, validate_ticker


def build_coinbase_subscription(symbols: list[str]) -> dict[str, Any]:
    return {
        "type": "subscribe",
        "product_ids": [normalize_symbol(symbol) for symbol in symbols],
        "channel": "ticker",
    }


def parse_coinbase_ticker(
    payload: Mapping[str, Any],
    *,
    received_at: str | None = None,
) -> VenueTicker:
    events = payload.get("events")
    if isinstance(events, list) and events:
        tickers = events[0].get("tickers", [])
        if not isinstance(tickers, list) or not tickers:
            raise MarketDataValidationError("Coinbase ticker payload has no tickers")
        item = tickers[0]
    else:
        item = payload

    try:
        ticker = VenueTicker(
            venue=Venue.COINBASE,
            symbol=normalize_symbol(
                str(item.get("product_id") or item.get("symbol"))
            ),
            bid=float(item.get("best_bid") or item.get("bid")),
            ask=float(item.get("best_ask") or item.get("ask")),
            bid_quantity=float(
                item.get("best_bid_quantity")
                or item.get("bid_quantity")
                or item.get("bid_qty")
                or 0.0
            ),
            ask_quantity=float(
                item.get("best_ask_quantity")
                or item.get("ask_quantity")
                or item.get("ask_qty")
                or 0.0
            ),
            last=float(item.get("price") or item.get("last")),
            volume_24h=float(item.get("volume_24_h") or item.get("volume") or 0.0),
            timestamp=str(
                item.get("time")
                or item.get("timestamp")
                or payload.get("timestamp")
                or received_at
                or utc_now()
            ),
            received_at=received_at or utc_now(),
            sequence=(
                None
                if payload.get("sequence_num") is None
                else int(payload["sequence_num"])
            ),
        )
    except (TypeError, ValueError) as exc:
        raise MarketDataValidationError(
            "Malformed Coinbase ticker payload"
        ) from exc

    validate_ticker(ticker)
    return ticker


__all__ = ["build_coinbase_subscription", "parse_coinbase_ticker"]
