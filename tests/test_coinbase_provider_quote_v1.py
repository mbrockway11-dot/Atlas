"""Tests for Coinbase public quote normalization."""

from __future__ import annotations

from atlas.investment.market_data.coinbase import (
    CoinbasePublicMarketDataProvider,
)
from atlas.investment.market_data.http import (
    HttpJsonResponse,
)


class FakeTransport:
    def __init__(self):
        self.calls = []

    def get_json(
        self,
        url,
        *,
        query=None,
        headers=None,
        timeout_seconds=10.0,
    ):
        self.calls.append({
            "url": url,
            "query": query,
            "headers": headers,
            "timeout": (
                timeout_seconds
            ),
        })

        return HttpJsonResponse(
            status_code=200,
            payload={
                "trade_id": 1,
                "price": "50000.00",
                "size": "0.100",
                "bid": "49990.00",
                "ask": "50010.00",
                "volume": "1000.00",
                "time": (
                    "2026-07-13T16:00:00Z"
                ),
            },
            headers={},
            elapsed_ms=1.0,
            url=url,
        )


def test_coinbase_quote_is_canonical():
    transport = FakeTransport()

    provider = (
        CoinbasePublicMarketDataProvider(
            transport=transport
        )
    )

    quote = provider.get_quote(
        "BTC"
    )

    assert quote.symbol == "BTC-USD"
    assert quote.provider == (
        "COINBASE_PUBLIC"
    )
    assert quote.last == 50000.0
    assert quote.bid == 49990.0
    assert quote.ask == 50010.0
    assert quote.volume == 1000.0

    assert transport.calls[0][
        "url"
    ].endswith(
        "/products/BTC-USD/ticker"
    )


def test_coinbase_rejects_non_crypto():
    provider = (
        CoinbasePublicMarketDataProvider(
            transport=FakeTransport()
        )
    )

    try:
        provider.get_quote(
            "SPY"
        )
    except LookupError as error:
        assert (
            "ASSET_CLASS_UNSUPPORTED"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected non-crypto rejection"
        )
