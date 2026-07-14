"""Symbol and ticker normalization helpers for Atlas G.23."""

from __future__ import annotations

from datetime import datetime, timezone

from .contracts import VenueTicker
from .errors import MarketDataValidationError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper().replace("/", "-").replace("_", "-")
    if "-" not in value and value.endswith("USDT"):
        value = f"{value[:-4]}-USDT"
    elif "-" not in value and value.endswith("USD"):
        value = f"{value[:-3]}-USD"
    if not value or value.startswith("-") or value.endswith("-"):
        raise MarketDataValidationError(f"Invalid symbol: {symbol!r}")
    return value


def validate_ticker(ticker: VenueTicker) -> None:
    if ticker.bid <= 0 or ticker.ask <= 0 or ticker.last <= 0:
        raise MarketDataValidationError("Prices must be positive")
    if ticker.ask < ticker.bid:
        raise MarketDataValidationError(
            f"Crossed ticker for {ticker.venue.value} {ticker.symbol}"
        )
    if ticker.bid_quantity < 0 or ticker.ask_quantity < 0:
        raise MarketDataValidationError("Quantities cannot be negative")
    if ticker.volume_24h < 0:
        raise MarketDataValidationError("volume_24h cannot be negative")
    if not ticker.paper_only or ticker.live_execution or ticker.credentials_used:
        raise MarketDataValidationError("Ticker violates read-only safety boundary")


__all__ = ["normalize_symbol", "utc_now", "validate_ticker"]
