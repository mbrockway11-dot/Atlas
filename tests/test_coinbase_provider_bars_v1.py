"""Tests for Coinbase public candle normalization."""

from __future__ import annotations

from atlas.investment.market_data.coinbase import (
    CoinbasePublicMarketDataProvider,
)
from atlas.investment.market_data.http import (
    HttpJsonResponse,
)


class FakeTransport:
    def get_json(
        self,
        url,
        *,
        query=None,
        headers=None,
        timeout_seconds=10.0,
    ):
        assert query == {
            "granularity": 3600
        }

        return HttpJsonResponse(
            status_code=200,
            payload=[
                [
                    1720890000,
                    49000,
                    51000,
                    50000,
                    50500,
                    100,
                ],
                [
                    1720886400,
                    48000,
                    50500,
                    49000,
                    50000,
                    90,
                ],
            ],
            headers={},
            elapsed_ms=1.0,
            url=url,
        )


def test_coinbase_bars_are_sorted():
    provider = (
        CoinbasePublicMarketDataProvider(
            transport=FakeTransport()
        )
    )

    bars = provider.get_bars(
        "BTC-USD",
        interval="1H",
        limit=2,
    )

    assert len(bars) == 2
    assert (
        bars[0].start_at
        < bars[1].start_at
    )
    assert bars[0].interval == "1H"
    assert bars[1].close == 50500.0


def test_coinbase_interval_fails_closed():
    provider = (
        CoinbasePublicMarketDataProvider(
            transport=FakeTransport()
        )
    )

    try:
        provider.get_bars(
            "BTC-USD",
            interval="2H",
            limit=2,
        )
    except ValueError as error:
        assert (
            "INTERVAL_UNSUPPORTED"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected interval rejection"
        )
