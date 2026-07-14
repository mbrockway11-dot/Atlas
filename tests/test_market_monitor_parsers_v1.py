from __future__ import annotations

from atlas.investment.market_monitor import (
    Venue,
    parse_binance_book_ticker,
    parse_coinbase_ticker,
    parse_kraken_ticker,
)


def test_coinbase_ticker_normalization() -> None:
    ticker = parse_coinbase_ticker(
        {
            "sequence_num": 7,
            "events": [
                {
                    "tickers": [
                        {
                            "product_id": "BTC-USD",
                            "best_bid": "60000",
                            "best_ask": "60001",
                            "best_bid_quantity": "1.2",
                            "best_ask_quantity": "1.3",
                            "price": "60000.5",
                            "volume_24_h": "1000",
                            "time": "2026-01-01T00:00:00+00:00",
                        }
                    ]
                }
            ],
        },
        received_at="2026-01-01T00:00:01+00:00",
    )

    assert ticker.venue == Venue.COINBASE
    assert ticker.symbol == "BTC-USD"
    assert ticker.sequence == 7


def test_kraken_ticker_normalization() -> None:
    ticker = parse_kraken_ticker(
        {
            "channel": "ticker",
            "data": [
                {
                    "symbol": "BTC/USD",
                    "bid": 59999,
                    "ask": 60002,
                    "bid_qty": 2,
                    "ask_qty": 3,
                    "last": 60000,
                    "volume": 500,
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ],
        },
        received_at="2026-01-01T00:00:01+00:00",
    )

    assert ticker.venue == Venue.KRAKEN
    assert ticker.symbol == "BTC-USD"


def test_binance_book_ticker_normalization() -> None:
    ticker = parse_binance_book_ticker(
        {
            "s": "BTCUSDT",
            "b": "60010",
            "B": "4",
            "a": "60011",
            "A": "5",
            "u": 99,
        },
        received_at="2026-01-01T00:00:01+00:00",
    )

    assert ticker.venue == Venue.BINANCE
    assert ticker.symbol == "BTC-USDT"
    assert ticker.sequence == 99
