"""Build a canonical Atlas snapshot from Coinbase public market data."""

from __future__ import annotations

import argparse

from atlas.investment.market_data import (
    CachedMarketDataProvider,
    CoinbasePublicMarketDataProvider,
    MarketDataRouter,
    diagnose_provider,
    write_market_snapshot,
)


DEFAULT_SYMBOLS = (
    "BTC-USD,ETH-USD,SOL-USD"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Build an unauthenticated Coinbase "
            "crypto market snapshot."
        )
    )

    parser.add_argument(
        "--symbols",
        default=(
            DEFAULT_SYMBOLS
        ),
    )

    parser.add_argument(
        "--maximum-age-seconds",
        type=float,
        default=60.0,
    )

    parser.add_argument(
        "--maximum-spread-bps",
        type=float,
        default=100.0,
    )

    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
    )

    parser.add_argument(
        "--quote-cache-seconds",
        type=float,
        default=5.0,
    )

    parser.add_argument(
        "--diagnose",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    symbols = [
        item.strip().upper()
        for item
        in args.symbols.split(",")
        if item.strip()
    ]

    base = (
        CoinbasePublicMarketDataProvider(
            timeout_seconds=(
                args.timeout_seconds
            )
        )
    )

    provider = (
        CachedMarketDataProvider(
            base,
            quote_ttl_seconds=(
                args.quote_cache_seconds
            ),
        )
    )

    if args.diagnose:
        diagnostics = diagnose_provider(
            provider,
            symbols=symbols,
            maximum_age_seconds=(
                args.maximum_age_seconds
            ),
            maximum_spread_bps=(
                args.maximum_spread_bps
            ),
        )

        print(
            "COINBASE PROVIDER DIAGNOSTICS"
        )

        print(
            "Counts:",
            diagnostics["counts"],
        )

        for row in diagnostics[
            "rows"
        ]:
            print(
                row["symbol"],
                row["success"],
                row["elapsed_ms"],
                row["error"],
            )

    router = MarketDataRouter([
        provider
    ])

    snapshot = (
        router.build_snapshot(
            symbols,
            maximum_age_seconds=(
                args.maximum_age_seconds
            ),
            maximum_spread_bps=(
                args.maximum_spread_bps
            ),
        )
    )

    snapshot["source"] = {
        "adapter": (
            "COINBASE_PUBLIC"
        ),
        "network_required": True,
        "credentials_required": False,
        "cache_statistics": (
            provider
            .statistics()
            .to_dict()
        ),
    }

    write_market_snapshot(
        snapshot
    )

    print(
        "ATLAS COINBASE MARKET SNAPSHOT "
        + (
            "READY"
            if snapshot["success"]
            else "FAILED"
        )
    )

    print(
        "Snapshot ID:",
        snapshot["snapshot_id"],
    )

    print(
        "Counts:",
        snapshot["counts"],
    )

    print(
        "Reference prices:",
        snapshot[
            "reference_prices"
        ],
    )

    print(
        "Failures:",
        snapshot[
            "failures"
        ],
    )

    return (
        0
        if snapshot["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
