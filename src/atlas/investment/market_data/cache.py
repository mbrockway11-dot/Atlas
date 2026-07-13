"""Thread-safe TTL caching for Atlas market-data providers."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Sequence

from atlas.investment.execution.instruments import (
    normalize_symbol,
)
from atlas.investment.market_data.contracts import (
    MarketBar,
    QuoteSnapshot,
)
from atlas.investment.market_data.providers import (
    MarketDataProvider,
    ProviderCapabilities,
)


@dataclass(frozen=True)
class CacheStatistics:
    quote_hits: int
    quote_misses: int
    bar_hits: int
    bar_misses: int

    def to_dict(self) -> dict[str, int]:
        return {
            "quote_hits": (
                self.quote_hits
            ),
            "quote_misses": (
                self.quote_misses
            ),
            "bar_hits": (
                self.bar_hits
            ),
            "bar_misses": (
                self.bar_misses
            ),
        }


class CachedMarketDataProvider:
    """TTL cache around any provider implementing the Atlas protocol."""

    def __init__(
        self,
        provider: MarketDataProvider,
        *,
        quote_ttl_seconds: float = 5.0,
        bar_ttl_seconds: float = 60.0,
        monotonic_clock=None,
    ) -> None:
        self.provider = provider

        self.quote_ttl_seconds = max(
            0.0,
            float(
                quote_ttl_seconds
            ),
        )

        self.bar_ttl_seconds = max(
            0.0,
            float(
                bar_ttl_seconds
            ),
        )

        self._clock = (
            monotonic_clock
            or time.monotonic
        )

        self._quote_cache: dict[
            str,
            tuple[
                float,
                QuoteSnapshot,
            ],
        ] = {}

        self._bar_cache: dict[
            tuple[
                str,
                str,
                int,
            ],
            tuple[
                float,
                tuple[
                    MarketBar,
                    ...,
                ],
            ],
        ] = {}

        self._quote_hits = 0
        self._quote_misses = 0
        self._bar_hits = 0
        self._bar_misses = 0

        self._lock = (
            threading.RLock()
        )

    @property
    def name(self) -> str:
        return self.provider.name

    @property
    def capabilities(
        self,
    ) -> ProviderCapabilities:
        return (
            self.provider.capabilities
        )

    def get_quote(
        self,
        symbol: str,
    ) -> QuoteSnapshot:
        canonical = normalize_symbol(
            symbol
        )

        now = float(
            self._clock()
        )

        with self._lock:
            cached = (
                self._quote_cache.get(
                    canonical
                )
            )

            if (
                cached is not None
                and now
                - cached[0]
                <= self.quote_ttl_seconds
            ):
                self._quote_hits += 1
                return cached[1]

            self._quote_misses += 1

        quote = self.provider.get_quote(
            canonical
        )

        with self._lock:
            self._quote_cache[
                canonical
            ] = (
                now,
                quote,
            )

        return quote

    def get_bars(
        self,
        symbol: str,
        *,
        interval: str,
        limit: int,
    ) -> Sequence[MarketBar]:
        canonical = normalize_symbol(
            symbol
        )

        normalized_interval = str(
            interval
        ).strip().upper()

        normalized_limit = max(
            0,
            int(limit),
        )

        key = (
            canonical,
            normalized_interval,
            normalized_limit,
        )

        now = float(
            self._clock()
        )

        with self._lock:
            cached = (
                self._bar_cache.get(
                    key
                )
            )

            if (
                cached is not None
                and now
                - cached[0]
                <= self.bar_ttl_seconds
            ):
                self._bar_hits += 1
                return cached[1]

            self._bar_misses += 1

        bars = tuple(
            self.provider.get_bars(
                canonical,
                interval=(
                    normalized_interval
                ),
                limit=(
                    normalized_limit
                ),
            )
        )

        with self._lock:
            self._bar_cache[
                key
            ] = (
                now,
                bars,
            )

        return bars

    def clear(self) -> None:
        with self._lock:
            self._quote_cache.clear()
            self._bar_cache.clear()

    def statistics(
        self,
    ) -> CacheStatistics:
        with self._lock:
            return CacheStatistics(
                quote_hits=(
                    self._quote_hits
                ),
                quote_misses=(
                    self._quote_misses
                ),
                bar_hits=(
                    self._bar_hits
                ),
                bar_misses=(
                    self._bar_misses
                ),
            )


__all__ = [
    "CacheStatistics",
    "CachedMarketDataProvider",
]
