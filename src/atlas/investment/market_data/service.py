"""Market-data routing, validation, freshness, and snapshot construction."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Iterable, Mapping, Sequence

from atlas.investment.execution.instruments import (
    get_instrument,
    normalize_symbol,
)
from atlas.investment.market_data.contracts import (
    MarketBar,
    QuoteSnapshot,
    utc_now,
)
from atlas.investment.market_data.providers import (
    MarketDataProvider,
)


MARKET_DATA_SERVICE_VERSION = "1.0.0"


class MarketDataRouter:
    """Route requests across ordered provider fallbacks."""

    def __init__(
        self,
        providers: Iterable[
            MarketDataProvider
        ] = (),
    ) -> None:
        self._providers: dict[
            str,
            MarketDataProvider,
        ] = {}

        self._order: list[str] = []

        for provider in providers:
            self.register(
                provider
            )

    def register(
        self,
        provider: MarketDataProvider,
    ) -> None:
        name = str(
            provider.name
        ).strip().upper()

        if not name:
            raise ValueError(
                "Provider name is required."
            )

        if name in self._providers:
            raise ValueError(
                "DUPLICATE_MARKET_DATA_PROVIDER:"
                + name
            )

        self._providers[name] = (
            provider
        )

        self._order.append(name)

    def provider_names(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            self._order
        )

    def get_quote(
        self,
        symbol: str,
        *,
        providers: Sequence[
            str
        ] | None = None,
        maximum_age_seconds: float | None = None,
        maximum_spread_bps: float | None = None,
        now: datetime | None = None,
    ) -> QuoteSnapshot:
        normalized = normalize_symbol(
            symbol
        )

        get_instrument(
            normalized
        )

        errors: list[str] = []

        for name in self._resolve_order(
            providers
        ):
            provider = (
                self._providers[name]
            )

            if not (
                provider
                .capabilities
                .quotes
            ):
                errors.append(
                    "PROVIDER_QUOTES_UNSUPPORTED:"
                    + name
                )
                continue

            try:
                quote = (
                    provider.get_quote(
                        normalized
                    )
                )
            except Exception as error:
                errors.append(
                    str(error)
                )
                continue

            quality = (
                evaluate_quote_quality(
                    quote,
                    maximum_age_seconds=(
                        maximum_age_seconds
                    ),
                    maximum_spread_bps=(
                        maximum_spread_bps
                    ),
                    now=now,
                )
            )

            if quality["valid"]:
                return quote

            errors.extend(
                str(error)
                for error
                in quality["errors"]
            )

        raise LookupError(
            "NO_VALID_QUOTE:"
            + normalized
            + ":"
            + "|".join(
                errors
            )
        )

    def get_bars(
        self,
        symbol: str,
        *,
        interval: str,
        limit: int,
        providers: Sequence[
            str
        ] | None = None,
    ) -> tuple[MarketBar, ...]:
        normalized = normalize_symbol(
            symbol
        )

        get_instrument(
            normalized
        )

        errors: list[str] = []

        for name in self._resolve_order(
            providers
        ):
            provider = (
                self._providers[name]
            )

            if not (
                provider
                .capabilities
                .bars
            ):
                errors.append(
                    "PROVIDER_BARS_UNSUPPORTED:"
                    + name
                )
                continue

            try:
                bars = tuple(
                    provider.get_bars(
                        normalized,
                        interval=interval,
                        limit=limit,
                    )
                )
            except Exception as error:
                errors.append(
                    str(error)
                )
                continue

            quality = (
                evaluate_bar_series(
                    bars
                )
            )

            if quality["valid"]:
                return bars

            errors.extend(
                str(error)
                for error
                in quality["errors"]
            )

        raise LookupError(
            "NO_VALID_BARS:"
            + normalized
            + ":"
            + "|".join(
                errors
            )
        )

    def build_snapshot(
        self,
        symbols: Iterable[str],
        *,
        providers: Sequence[
            str
        ] | None = None,
        maximum_age_seconds: float | None = None,
        maximum_spread_bps: float | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        quotes: list[
            QuoteSnapshot
        ] = []

        failures: list[
            dict[str, str]
        ] = []

        normalized_symbols = sorted({
            normalize_symbol(
                symbol
            )
            for symbol
            in symbols
            if str(
                symbol
            ).strip()
            and normalize_symbol(
                symbol
            )
            != "CASH"
        })

        for symbol in (
            normalized_symbols
        ):
            try:
                quote = self.get_quote(
                    symbol,
                    providers=providers,
                    maximum_age_seconds=(
                        maximum_age_seconds
                    ),
                    maximum_spread_bps=(
                        maximum_spread_bps
                    ),
                    now=now,
                )
            except Exception as error:
                failures.append({
                    "symbol": symbol,
                    "error": str(error),
                })
                continue

            quotes.append(quote)

        snapshot_id = (
            build_snapshot_id(
                quotes
            )
        )

        return {
            "success": not failures,
            "version": (
                MARKET_DATA_SERVICE_VERSION
            ),
            "snapshot_id": (
                snapshot_id
            ),
            "generated_at": (
                utc_now()
            ),
            "provider_order": list(
                self._resolve_order(
                    providers
                )
            ),
            "symbols_requested": (
                normalized_symbols
            ),
            "quotes": [
                quote.to_dict()
                for quote
                in quotes
            ],
            "reference_prices": {
                quote.symbol: (
                    quote.midpoint
                )
                for quote
                in quotes
            },
            "failures": failures,
            "counts": {
                "requested": len(
                    normalized_symbols
                ),
                "resolved": len(
                    quotes
                ),
                "failed": len(
                    failures
                ),
            },
            "contract": {
                "provider_neutral": True,
                "broker_independent": True,
                "live_execution": False,
                "credentials_used": False,
                "quality_validated": True,
                "freshness_validated": (
                    maximum_age_seconds
                    is not None
                ),
            },
        }

    def _resolve_order(
        self,
        providers: Sequence[
            str
        ] | None,
    ) -> tuple[str, ...]:
        names = (
            tuple(
                str(name)
                .strip()
                .upper()
                for name
                in providers
            )
            if providers
            else tuple(
                self._order
            )
        )

        for name in names:
            if name not in (
                self._providers
            ):
                raise KeyError(
                    "UNKNOWN_MARKET_DATA_PROVIDER:"
                    + name
                )

        return names


def evaluate_quote_quality(
    quote: QuoteSnapshot,
    *,
    maximum_age_seconds: float | None = None,
    maximum_spread_bps: float | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    age = quote.age_seconds(
        now=now
    )

    if (
        maximum_age_seconds
        is not None
        and age
        > float(
            maximum_age_seconds
        )
    ):
        errors.append(
            "STALE_QUOTE:"
            + quote.symbol
        )

    spread_bps = (
        quote.spread_bps
    )

    if (
        maximum_spread_bps
        is not None
        and spread_bps is not None
        and spread_bps
        > float(
            maximum_spread_bps
        )
    ):
        errors.append(
            "SPREAD_LIMIT_EXCEEDED:"
            + quote.symbol
        )

    if (
        quote.bid is None
        or quote.ask is None
    ):
        warnings.append(
            "ONE_SIDED_OR_LAST_ONLY_QUOTE:"
            + quote.symbol
        )

    if (
        quote.volume is None
    ):
        warnings.append(
            "QUOTE_VOLUME_UNAVAILABLE:"
            + quote.symbol
        )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "age_seconds": age,
        "spread_bps": (
            spread_bps
        ),
    }


def evaluate_bar_series(
    bars: Sequence[
        MarketBar
    ],
) -> dict[str, Any]:
    errors: list[str] = []

    if not bars:
        errors.append(
            "EMPTY_BAR_SERIES"
        )

    symbols = {
        bar.symbol
        for bar
        in bars
    }

    providers = {
        bar.provider
        for bar
        in bars
    }

    intervals = {
        bar.interval
        for bar
        in bars
    }

    if len(symbols) > 1:
        errors.append(
            "MIXED_BAR_SYMBOLS"
        )

    if len(providers) > 1:
        errors.append(
            "MIXED_BAR_PROVIDERS"
        )

    if len(intervals) > 1:
        errors.append(
            "MIXED_BAR_INTERVALS"
        )

    start_times = [
        bar.start_at
        for bar
        in bars
    ]

    if start_times != sorted(
        start_times
    ):
        errors.append(
            "BAR_SERIES_NOT_SORTED"
        )

    bar_ids = [
        bar.bar_id
        for bar
        in bars
    ]

    if len(bar_ids) != len(
        set(bar_ids)
    ):
        errors.append(
            "DUPLICATE_BAR_ID"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "bar_count": len(
            bars
        ),
    }


def reference_prices_from_snapshot(
    snapshot: Mapping[
        str,
        Any,
    ],
) -> dict[str, float]:
    prices = snapshot.get(
        "reference_prices",
        {},
    )

    if not isinstance(
        prices,
        Mapping,
    ):
        raise ValueError(
            "MARKET_SNAPSHOT_PRICES_INVALID"
        )

    normalized: dict[
        str,
        float,
    ] = {}

    for symbol, price in (
        prices.items()
    ):
        canonical = normalize_symbol(
            symbol
        )

        get_instrument(
            canonical
        )

        number = float(price)

        if number <= 0:
            raise ValueError(
                "MARKET_SNAPSHOT_PRICE_INVALID:"
                + canonical
            )

        normalized[
            canonical
        ] = number

    return normalized


def build_snapshot_id(
    quotes: Sequence[
        QuoteSnapshot
    ],
) -> str:
    payload = [
        {
            "quote_id": (
                quote.quote_id
            ),
            "symbol": (
                quote.symbol
            ),
            "provider": (
                quote.provider
            ),
            "as_of": (
                quote.as_of
            ),
        }
        for quote
        in sorted(
            quotes,
            key=lambda item: (
                item.symbol,
                item.provider,
                item.as_of,
            ),
        )
    ]

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return (
        "MARKET-SNAPSHOT-"
        + digest[:24]
    )


__all__ = [
    "MARKET_DATA_SERVICE_VERSION",
    "MarketDataRouter",
    "evaluate_bar_series",
    "evaluate_quote_quality",
    "reference_prices_from_snapshot",
]
