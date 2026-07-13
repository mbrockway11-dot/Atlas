"""Read-only Coinbase Exchange public market-data adapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Mapping, Sequence

from atlas.investment.execution.instruments import (
    get_instrument,
    normalize_symbol,
)
from atlas.investment.market_data.contracts import (
    MarketBar,
    QuoteSnapshot,
)
from atlas.investment.market_data.http import (
    JsonHttpTransport,
    UrllibJsonTransport,
)
from atlas.investment.market_data.providers import (
    ProviderCapabilities,
)


COINBASE_BASE_URL = (
    "https://api.exchange.coinbase.com"
)

COINBASE_PROVIDER_VERSION = (
    "1.0.0"
)

COINBASE_INTERVAL_SECONDS = {
    "1M": 60,
    "5M": 300,
    "15M": 900,
    "1H": 3600,
    "6H": 21600,
    "1D": 86400,
}


class CoinbasePublicMarketDataProvider:
    """Unauthenticated Coinbase spot quotes and candles."""

    def __init__(
        self,
        *,
        transport: (
            JsonHttpTransport | None
        ) = None,
        base_url: str = (
            COINBASE_BASE_URL
        ),
        timeout_seconds: float = 10.0,
    ) -> None:
        self.transport = (
            transport
            or UrllibJsonTransport()
        )

        self.base_url = str(
            base_url
        ).rstrip("/")

        self.timeout_seconds = max(
            0.1,
            float(
                timeout_seconds
            ),
        )

    @property
    def name(self) -> str:
        return "COINBASE_PUBLIC"

    @property
    def capabilities(
        self,
    ) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self.name,
            quotes=True,
            bars=True,
            trades=False,
            order_book=False,
            funding_rates=False,
            open_interest=False,
            network_required=True,
            credentials_required=False,
        )

    def get_quote(
        self,
        symbol: str,
    ) -> QuoteSnapshot:
        canonical = (
            require_supported_crypto(
                symbol
            )
        )

        product_id = (
            to_coinbase_product(
                canonical
            )
        )

        response = (
            self.transport.get_json(
                self.base_url
                + "/products/"
                + product_id
                + "/ticker",
                timeout_seconds=(
                    self.timeout_seconds
                ),
            )
        )

        payload = require_mapping(
            response.payload,
            context="COINBASE_TICKER",
        )

        price = positive_number(
            payload.get(
                "price"
            ),
            field="price",
        )

        bid = optional_nonnegative(
            payload.get(
                "bid"
            ),
            field="bid",
        )

        ask = optional_nonnegative(
            payload.get(
                "ask"
            ),
            field="ask",
        )

        size = optional_nonnegative(
            payload.get(
                "size"
            ),
            field="size",
        )

        volume = optional_nonnegative(
            payload.get(
                "volume"
            ),
            field="volume",
        )

        as_of = normalize_time(
            payload.get(
                "time"
            )
        )

        return QuoteSnapshot(
            symbol=canonical,
            provider=self.name,
            as_of=as_of,
            last=price,
            bid=bid,
            ask=ask,
            volume=volume,
            received_at=(
                datetime.now(
                    UTC
                ).isoformat()
            ),
            market_session=(
                "CONTINUOUS"
            ),
            currency="USD",
            bid_size=None,
            ask_size=size,
        )

    def get_bars(
        self,
        symbol: str,
        *,
        interval: str,
        limit: int,
    ) -> Sequence[MarketBar]:
        canonical = (
            require_supported_crypto(
                symbol
            )
        )

        normalized_interval = str(
            interval
        ).strip().upper()

        if normalized_interval not in (
            COINBASE_INTERVAL_SECONDS
        ):
            raise ValueError(
                "COINBASE_INTERVAL_UNSUPPORTED:"
                + normalized_interval
            )

        normalized_limit = max(
            0,
            min(
                int(limit),
                300,
            ),
        )

        if normalized_limit == 0:
            return ()

        granularity = (
            COINBASE_INTERVAL_SECONDS[
                normalized_interval
            ]
        )

        response = (
            self.transport.get_json(
                self.base_url
                + "/products/"
                + to_coinbase_product(
                    canonical
                )
                + "/candles",
                query={
                    "granularity": (
                        granularity
                    ),
                },
                timeout_seconds=(
                    self.timeout_seconds
                ),
            )
        )

        payload = response.payload

        if not isinstance(
            payload,
            list,
        ):
            raise ValueError(
                "COINBASE_CANDLES_NOT_LIST"
            )

        bars: list[
            MarketBar
        ] = []

        for index, row in enumerate(
            payload
        ):
            if not isinstance(
                row,
                list,
            ) or len(row) < 6:
                raise ValueError(
                    "COINBASE_CANDLE_INVALID:"
                    + str(index)
                )

            start_epoch = int(
                number(
                    row[0],
                    field="time",
                )
            )

            start = datetime.fromtimestamp(
                start_epoch,
                tz=UTC,
            )

            end = start + timedelta(
                seconds=granularity
            )

            bars.append(
                MarketBar(
                    symbol=canonical,
                    provider=self.name,
                    interval=(
                        normalized_interval
                    ),
                    start_at=(
                        start.isoformat()
                    ),
                    end_at=(
                        end.isoformat()
                    ),
                    low=positive_number(
                        row[1],
                        field="low",
                    ),
                    high=positive_number(
                        row[2],
                        field="high",
                    ),
                    open=positive_number(
                        row[3],
                        field="open",
                    ),
                    close=positive_number(
                        row[4],
                        field="close",
                    ),
                    volume=nonnegative_number(
                        row[5],
                        field="volume",
                    ),
                    currency="USD",
                )
            )

        bars.sort(
            key=lambda item: (
                item.start_at
            )
        )

        return tuple(
            bars[-normalized_limit:]
        )


def require_supported_crypto(
    symbol: str,
) -> str:
    canonical = normalize_symbol(
        symbol
    )

    instrument = get_instrument(
        canonical
    )

    if instrument is None:
        raise KeyError(
            "UNREGISTERED_INSTRUMENT:"
            + canonical
        )

    if instrument.asset_class != (
        "CRYPTO"
    ):
        raise LookupError(
            "COINBASE_ASSET_CLASS_UNSUPPORTED:"
            + canonical
        )

    if not canonical.endswith(
        "-USD"
    ):
        raise LookupError(
            "COINBASE_QUOTE_CURRENCY_UNSUPPORTED:"
            + canonical
        )

    return canonical


def to_coinbase_product(
    symbol: str,
) -> str:
    return require_supported_crypto(
        symbol
    )


def require_mapping(
    payload: Any,
    *,
    context: str,
) -> Mapping[str, Any]:
    if not isinstance(
        payload,
        Mapping,
    ):
        raise ValueError(
            context
            + "_NOT_OBJECT"
        )

    return payload


def normalize_time(
    value: Any,
) -> str:
    if value is None:
        return datetime.now(
            UTC
        ).isoformat()

    text = str(value).strip()

    if not text:
        return datetime.now(
            UTC
        ).isoformat()

    if text.endswith("Z"):
        text = (
            text[:-1]
            + "+00:00"
        )

    parsed = datetime.fromisoformat(
        text
    )

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=UTC
        )

    return parsed.astimezone(
        UTC
    ).isoformat()


def number(
    value: Any,
    *,
    field: str,
) -> float:
    try:
        result = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "COINBASE_NUMBER_INVALID:"
            + field
        ) from error

    return result


def positive_number(
    value: Any,
    *,
    field: str,
) -> float:
    result = number(
        value,
        field=field,
    )

    if result <= 0:
        raise ValueError(
            "COINBASE_NUMBER_NOT_POSITIVE:"
            + field
        )

    return result


def nonnegative_number(
    value: Any,
    *,
    field: str,
) -> float:
    result = number(
        value,
        field=field,
    )

    if result < 0:
        raise ValueError(
            "COINBASE_NUMBER_NEGATIVE:"
            + field
        )

    return result


def optional_nonnegative(
    value: Any,
    *,
    field: str,
) -> float | None:
    if value in (
        None,
        "",
    ):
        return None

    return nonnegative_number(
        value,
        field=field,
    )


__all__ = [
    "COINBASE_BASE_URL",
    "COINBASE_INTERVAL_SECONDS",
    "COINBASE_PROVIDER_VERSION",
    "CoinbasePublicMarketDataProvider",
    "to_coinbase_product",
]
