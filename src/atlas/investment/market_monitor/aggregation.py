"""Cross-venue ticker aggregation for Atlas G.23."""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import median
from typing import Iterable

from .contracts import ConsolidatedTicker, VenueTicker
from .errors import MarketDataValidationError
from .normalization import normalize_symbol, validate_ticker


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def consolidate_tickers(
    tickers: Iterable[VenueTicker],
    *,
    symbol: str,
    generated_at: str | None = None,
) -> ConsolidatedTicker:
    normalized_symbol = normalize_symbol(symbol)
    matching = [
        ticker
        for ticker in tickers
        if normalize_symbol(ticker.symbol) == normalized_symbol
    ]
    if not matching:
        raise MarketDataValidationError(
            f"No venue tickers available for {normalized_symbol}"
        )

    for ticker in matching:
        validate_ticker(ticker)

    best_bid_ticker = max(matching, key=lambda item: item.bid)
    best_ask_ticker = min(matching, key=lambda item: item.ask)
    best_bid = best_bid_ticker.bid
    best_ask = best_ask_ticker.ask
    midpoint = (best_bid + best_ask) / 2.0
    spread = best_ask - best_bid
    spread_bps = spread / midpoint * 10_000 if midpoint else 0.0

    lasts = [ticker.last for ticker in matching]
    last_median = median(lasts)
    divergence = (
        (max(lasts) - min(lasts)) / last_median * 10_000
        if last_median
        else 0.0
    )

    return ConsolidatedTicker(
        symbol=normalized_symbol,
        best_bid=best_bid,
        best_bid_venue=best_bid_ticker.venue,
        best_ask=best_ask,
        best_ask_venue=best_ask_ticker.venue,
        midpoint=midpoint,
        spread=spread,
        spread_bps=spread_bps,
        last_median=last_median,
        venue_count=len(matching),
        cross_venue_divergence_bps=divergence,
        total_bid_quantity=sum(item.bid_quantity for item in matching),
        total_ask_quantity=sum(item.ask_quantity for item in matching),
        generated_at=generated_at or _utc_now(),
        paper_only=True,
        live_execution=False,
        credentials_used=False,
    )


__all__ = ["consolidate_tickers"]
