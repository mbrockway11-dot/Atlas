"""Canonical provider-neutral Atlas market-data contracts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


MARKET_DATA_CONTRACT_VERSION = "1.0.0"


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def finite_number(
    value: Any,
    *,
    name: str,
) -> float:
    number = float(value)

    if not math.isfinite(number):
        raise ValueError(
            f"{name} must be finite."
        )

    return number


def parse_timestamp(
    value: str,
) -> datetime:
    text = str(value).strip()

    if not text:
        raise ValueError(
            "Timestamp is required."
        )

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
    )


@dataclass(frozen=True)
class QuoteSnapshot:
    """One canonical point-in-time market quote."""

    symbol: str
    provider: str
    as_of: str
    last: float
    bid: float | None = None
    ask: float | None = None
    bid_size: float | None = None
    ask_size: float | None = None
    volume: float | None = None
    currency: str = "USD"
    market_session: str = ""
    received_at: str = ""
    quote_id: str = ""

    def __post_init__(self) -> None:
        symbol = str(
            self.symbol
        ).strip().upper()

        provider = str(
            self.provider
        ).strip().upper()

        currency = str(
            self.currency
        ).strip().upper()

        if not symbol:
            raise ValueError(
                "Quote symbol is required."
            )

        if not provider:
            raise ValueError(
                "Quote provider is required."
            )

        parse_timestamp(
            self.as_of
        )

        last = finite_number(
            self.last,
            name="last",
        )

        if last <= 0:
            raise ValueError(
                "last must be positive."
            )

        optional_values = {
            "bid": self.bid,
            "ask": self.ask,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
            "volume": self.volume,
        }

        normalized = {}

        for name, value in (
            optional_values.items()
        ):
            if value is None:
                normalized[name] = None
                continue

            number = finite_number(
                value,
                name=name,
            )

            if number < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

            normalized[name] = number

        bid = normalized["bid"]
        ask = normalized["ask"]

        if (
            bid is not None
            and ask is not None
            and bid > ask
        ):
            raise ValueError(
                "bid cannot exceed ask."
            )

        received_at = (
            self.received_at
            or utc_now()
        )

        parse_timestamp(
            received_at
        )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "provider",
            provider,
        )

        object.__setattr__(
            self,
            "currency",
            currency,
        )

        object.__setattr__(
            self,
            "last",
            last,
        )

        for name, value in (
            normalized.items()
        ):
            object.__setattr__(
                self,
                name,
                value,
            )

        object.__setattr__(
            self,
            "received_at",
            received_at,
        )

        if not self.quote_id:
            object.__setattr__(
                self,
                "quote_id",
                build_quote_id(self),
            )

    @property
    def midpoint(self) -> float:
        if (
            self.bid is not None
            and self.ask is not None
        ):
            return (
                self.bid
                + self.ask
            ) / 2.0

        return self.last

    @property
    def spread(self) -> float | None:
        if (
            self.bid is None
            or self.ask is None
        ):
            return None

        return (
            self.ask
            - self.bid
        )

    @property
    def spread_bps(self) -> float | None:
        midpoint = self.midpoint

        if (
            self.spread is None
            or midpoint <= 0
        ):
            return None

        return (
            self.spread
            / midpoint
            * 10_000.0
        )

    def age_seconds(
        self,
        *,
        now: datetime | None = None,
    ) -> float:
        current = (
            now.astimezone(UTC)
            if now is not None
            else datetime.now(UTC)
        )

        timestamp = parse_timestamp(
            self.as_of
        )

        return max(
            0.0,
            (
                current
                - timestamp
            ).total_seconds(),
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["midpoint"] = (
            self.midpoint
        )
        result["spread"] = (
            self.spread
        )
        result["spread_bps"] = (
            self.spread_bps
        )
        return result


@dataclass(frozen=True)
class MarketBar:
    """One canonical OHLCV market-data bar."""

    symbol: str
    provider: str
    interval: str
    start_at: str
    end_at: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    trade_count: int | None = None
    vwap: float | None = None
    currency: str = "USD"
    bar_id: str = ""

    def __post_init__(self) -> None:
        symbol = str(
            self.symbol
        ).strip().upper()

        provider = str(
            self.provider
        ).strip().upper()

        interval = str(
            self.interval
        ).strip().upper()

        if not symbol:
            raise ValueError(
                "Bar symbol is required."
            )

        if not provider:
            raise ValueError(
                "Bar provider is required."
            )

        if not interval:
            raise ValueError(
                "Bar interval is required."
            )

        start = parse_timestamp(
            self.start_at
        )

        end = parse_timestamp(
            self.end_at
        )

        if end <= start:
            raise ValueError(
                "Bar end_at must follow start_at."
            )

        prices = {
            "open": finite_number(
                self.open,
                name="open",
            ),
            "high": finite_number(
                self.high,
                name="high",
            ),
            "low": finite_number(
                self.low,
                name="low",
            ),
            "close": finite_number(
                self.close,
                name="close",
            ),
        }

        if any(
            value <= 0
            for value
            in prices.values()
        ):
            raise ValueError(
                "OHLC prices must be positive."
            )

        if (
            prices["high"]
            < max(
                prices["open"],
                prices["close"],
                prices["low"],
            )
        ):
            raise ValueError(
                "Bar high is inconsistent."
            )

        if (
            prices["low"]
            > min(
                prices["open"],
                prices["close"],
                prices["high"],
            )
        ):
            raise ValueError(
                "Bar low is inconsistent."
            )

        volume = finite_number(
            self.volume,
            name="volume",
        )

        if volume < 0:
            raise ValueError(
                "volume cannot be negative."
            )

        vwap = (
            finite_number(
                self.vwap,
                name="vwap",
            )
            if self.vwap is not None
            else None
        )

        if (
            vwap is not None
            and vwap <= 0
        ):
            raise ValueError(
                "vwap must be positive."
            )

        if (
            self.trade_count is not None
            and int(
                self.trade_count
            )
            < 0
        ):
            raise ValueError(
                "trade_count cannot be negative."
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "provider",
            provider,
        )

        object.__setattr__(
            self,
            "interval",
            interval,
        )

        object.__setattr__(
            self,
            "volume",
            volume,
        )

        for name, value in (
            prices.items()
        ):
            object.__setattr__(
                self,
                name,
                value,
            )

        object.__setattr__(
            self,
            "vwap",
            vwap,
        )

        if not self.bar_id:
            object.__setattr__(
                self,
                "bar_id",
                build_bar_id(self),
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_quote_id(
    quote: QuoteSnapshot,
) -> str:
    payload = {
        "symbol": quote.symbol,
        "provider": quote.provider,
        "as_of": quote.as_of,
        "last": quote.last,
        "bid": quote.bid,
        "ask": quote.ask,
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return (
        "QUOTE-"
        + digest[:24]
    )


def build_bar_id(
    bar: MarketBar,
) -> str:
    payload = {
        "symbol": bar.symbol,
        "provider": bar.provider,
        "interval": bar.interval,
        "start_at": bar.start_at,
        "end_at": bar.end_at,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return (
        "BAR-"
        + digest[:24]
    )


__all__ = [
    "MARKET_DATA_CONTRACT_VERSION",
    "MarketBar",
    "QuoteSnapshot",
    "parse_timestamp",
    "utc_now",
]
