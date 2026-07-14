from __future__ import annotations

import asyncio
import json

from atlas.investment.market_monitor import (
    CoinbasePublicTickerCollector,
    CollectorConfig,
    KrakenPublicTickerCollector,
    Venue,
)


async def noop(_ticker) -> None:
    return None


def test_coinbase_subscription_has_no_credentials() -> None:
    collector = CoinbasePublicTickerCollector(
        config=CollectorConfig(symbols=("BTC-USD",)),
        on_ticker=noop,
    )

    class Connection:
        def __init__(self) -> None:
            self.message = ""

        async def send(self, message: str) -> None:
            self.message = message

        async def recv(self):
            return ""

        async def close(self) -> None:
            return None

    connection = Connection()
    asyncio.run(collector.subscribe(connection))
    payload = json.loads(connection.message)

    assert payload["channel"] == "ticker"
    assert payload["product_ids"] == ["BTC-USD"]
    assert "jwt" not in payload
    assert "api_key" not in payload


def test_coinbase_parser_detects_sequence_gap() -> None:
    collector = CoinbasePublicTickerCollector(
        config=CollectorConfig(symbols=("BTC-USD",)),
        on_ticker=noop,
    )

    def message(sequence: int) -> str:
        return json.dumps(
            {
                "sequence_num": sequence,
                "events": [
                    {
                        "tickers": [
                            {
                                "product_id": "BTC-USD",
                                "best_bid": "100",
                                "best_ask": "101",
                                "price": "100.5",
                            }
                        ]
                    }
                ],
            }
        )

    assert len(collector.parse_message(message(1))) == 1
    assert len(collector.parse_message(message(3))) == 1
    assert collector.metrics.sequence_gaps == 1


def test_kraken_parser_handles_multiple_symbols() -> None:
    collector = KrakenPublicTickerCollector(
        config=CollectorConfig(symbols=("BTC-USD", "ETH-USD")),
        on_ticker=noop,
    )
    tickers = collector.parse_message(
        json.dumps(
            {
                "channel": "ticker",
                "type": "update",
                "data": [
                    {
                        "symbol": "BTC/USD",
                        "bid": 100,
                        "ask": 101,
                        "last": 100.5,
                    },
                    {
                        "symbol": "ETH/USD",
                        "bid": 50,
                        "ask": 51,
                        "last": 50.5,
                    },
                ],
            }
        )
    )

    assert [ticker.venue for ticker in tickers] == [Venue.KRAKEN, Venue.KRAKEN]
    assert [ticker.symbol for ticker in tickers] == ["BTC-USD", "ETH-USD"]
