from __future__ import annotations

import pytest

from atlas.investment.market_monitor import (
    MarketDataValidationError,
    Venue,
    VenueTicker,
    build_binance_stream_names,
    build_coinbase_subscription,
    build_kraken_subscription,
    validate_ticker,
)


def test_subscription_builders_use_public_market_channels() -> None:
    coinbase = build_coinbase_subscription(["BTC-USD"])
    kraken = build_kraken_subscription(["BTC-USD"])
    binance = build_binance_stream_names(["BTC-USDT"])

    assert coinbase["channel"] == "ticker"
    assert kraken["params"]["channel"] == "ticker"
    assert binance == ["btcusdt@bookTicker"]


def test_credentials_and_live_execution_are_rejected() -> None:
    ticker = VenueTicker(
        venue=Venue.COINBASE,
        symbol="BTC-USD",
        bid=1,
        ask=2,
        bid_quantity=1,
        ask_quantity=1,
        last=1.5,
        volume_24h=1,
        timestamp="2026-01-01T00:00:00+00:00",
        received_at="2026-01-01T00:00:00+00:00",
        paper_only=False,
        live_execution=True,
        credentials_used=True,
    )

    with pytest.raises(MarketDataValidationError, match="safety boundary"):
        validate_ticker(ticker)


def test_crossed_market_is_rejected() -> None:
    ticker = VenueTicker(
        venue=Venue.KRAKEN,
        symbol="BTC-USD",
        bid=2,
        ask=1,
        bid_quantity=1,
        ask_quantity=1,
        last=1.5,
        volume_24h=1,
        timestamp="2026-01-01T00:00:00+00:00",
        received_at="2026-01-01T00:00:00+00:00",
    )

    with pytest.raises(MarketDataValidationError, match="Crossed"):
        validate_ticker(ticker)
