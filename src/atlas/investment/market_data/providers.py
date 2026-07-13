"""Provider contracts and deterministic Atlas market-data adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from atlas.investment.execution.instruments import (
    normalize_symbol,
)
from atlas.investment.market_data.contracts import (
    MarketBar,
    QuoteSnapshot,
)


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capabilities exposed by one market-data provider."""

    provider: str
    quotes: bool = True
    bars: bool = False
    trades: bool = False
    order_book: bool = False
    funding_rates: bool = False
    open_interest: bool = False
    network_required: bool = False
    credentials_required: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "quotes": self.quotes,
            "bars": self.bars,
            "trades": self.trades,
            "order_book": self.order_book,
            "funding_rates": (
                self.funding_rates
            ),
            "open_interest": (
                self.open_interest
            ),
            "network_required": (
                self.network_required
            ),
            "credentials_required": (
                self.credentials_required
            ),
        }


class MarketDataProvider(
    Protocol
):
    """Provider-neutral market-data adapter protocol."""

    @property
    def name(self) -> str:
        ...

    @property
    def capabilities(
        self,
    ) -> ProviderCapabilities:
        ...

    def get_quote(
        self,
        symbol: str,
    ) -> QuoteSnapshot:
        ...

    def get_bars(
        self,
        symbol: str,
        *,
        interval: str,
        limit: int,
    ) -> Sequence[MarketBar]:
        ...


class StaticMarketDataProvider:
    """Deterministic in-memory provider used by tests and fixtures."""

    def __init__(
        self,
        *,
        name: str = "STATIC",
        quotes: Mapping[
            str,
            QuoteSnapshot,
        ] | None = None,
        bars: Mapping[
            tuple[str, str],
            Sequence[MarketBar],
        ] | None = None,
    ) -> None:
        self._name = str(
            name
        ).strip().upper()

        if not self._name:
            raise ValueError(
                "Provider name is required."
            )

        self._quotes = {
            normalize_symbol(
                symbol
            ): quote
            for symbol, quote
            in (
                quotes or {}
            ).items()
        }

        self._bars = {
            (
                normalize_symbol(
                    symbol
                ),
                str(
                    interval
                ).strip().upper(),
            ): tuple(rows)
            for (
                symbol,
                interval,
            ), rows
            in (
                bars or {}
            ).items()
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(
        self,
    ) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self.name,
            quotes=True,
            bars=bool(
                self._bars
            ),
            network_required=False,
            credentials_required=False,
        )

    def get_quote(
        self,
        symbol: str,
    ) -> QuoteSnapshot:
        normalized = normalize_symbol(
            symbol
        )

        try:
            return self._quotes[
                normalized
            ]
        except KeyError as error:
            raise LookupError(
                "QUOTE_NOT_AVAILABLE:"
                + self.name
                + ":"
                + normalized
            ) from error

    def get_bars(
        self,
        symbol: str,
        *,
        interval: str,
        limit: int,
    ) -> Sequence[MarketBar]:
        normalized = normalize_symbol(
            symbol
        )

        key = (
            normalized,
            str(
                interval
            ).strip().upper(),
        )

        rows = self._bars.get(
            key
        )

        if rows is None:
            raise LookupError(
                "BARS_NOT_AVAILABLE:"
                + self.name
                + ":"
                + normalized
                + ":"
                + key[1]
            )

        count = max(
            0,
            int(limit),
        )

        return (
            rows[-count:]
            if count
            else ()
        )


__all__ = [
    "MarketDataProvider",
    "ProviderCapabilities",
    "StaticMarketDataProvider",
]
