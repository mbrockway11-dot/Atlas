"""Binance public book-ticker normalization for Atlas G.23.

Binance is treated as an optional liquidity-reference venue. This module
contains no authenticated trading behavior.
"""

from __future__ import annotations

from typing import Any, Mapping

from .contracts import Venue, VenueTicker
from .errors import MarketDataValidationError
from .normalization import normalize_symbol, utc_now, validate_ticker


def build_binance_stream_names(symbols: list[str]) -> list[str]:
    return [
        normalize_symbol(symbol).replace("-", "").lower() + "@bookTicker"
        for symbol in symbols
    ]


def parse_binance_book_ticker(
    payload: Mapping[str, Any],
    *,
    received_at: str | None = None,
) -> VenueTicker:
    item = payload.get("data") if isinstance(payload.get("data"), Mapping) else payload

    try:
        bid = float(item.get("b") or item.get("bid"))
        ask = float(item.get("a") or item.get("ask"))
        ticker = VenueTicker(
            venue=Venue.BINANCE,
            symbol=normalize_symbol(str(item.get("s") or item.get("symbol"))),
            bid=bid,
            ask=ask,
            bid_quantity=float(item.get("B") or item.get("bid_qty") or 0.0),
            ask_quantity=float(item.get("A") or item.get("ask_qty") or 0.0),
            last=float(item.get("last") or (bid + ask) / 2.0),
            volume_24h=float(item.get("volume") or 0.0),
            timestamp=str(
                item.get("timestamp")
                or item.get("E")
                or received_at
                or utc_now()
            ),
            received_at=received_at or utc_now(),
            sequence=(
                None
                if item.get("u") is None
                else int(item["u"])
            ),
        )
    except (TypeError, ValueError) as exc:
        raise MarketDataValidationError(
            "Malformed Binance book-ticker payload"
        ) from exc

    validate_ticker(ticker)
    return ticker


__all__ = ["build_binance_stream_names", "parse_binance_book_ticker"]
