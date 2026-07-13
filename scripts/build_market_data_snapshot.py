"""Build a canonical Atlas market-data snapshot from a static JSON fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.investment.execution import (
    normalize_symbol,
)
from atlas.investment.market_data import (
    MarketDataRouter,
    QuoteSnapshot,
    StaticMarketDataProvider,
    write_market_snapshot,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Build a provider-neutral Atlas market snapshot "
            "from deterministic quote fixtures."
        )
    )

    parser.add_argument(
        "--quotes-file",
        required=True,
    )

    parser.add_argument(
        "--provider",
        default="STATIC",
    )

    parser.add_argument(
        "--maximum-age-seconds",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--maximum-spread-bps",
        type=float,
        default=None,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    source = json.loads(
        Path(
            args.quotes_file
        ).read_text(
            encoding="utf-8"
        )
    )

    raw_quotes = source.get(
        "quotes",
        source,
    )

    if not isinstance(
        raw_quotes,
        dict,
    ):
        raise ValueError(
            "Quotes fixture must be an object."
        )

    quotes = {}

    for symbol, payload in (
        raw_quotes.items()
    ):
        canonical = normalize_symbol(
            symbol
        )

        if isinstance(
            payload,
            (int, float),
        ):
            payload = {
                "last": float(
                    payload
                ),
                "as_of": source.get(
                    "as_of"
                ),
            }

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "Invalid quote payload: "
                + canonical
            )

        quotes[canonical] = (
            QuoteSnapshot(
                symbol=canonical,
                provider=(
                    args.provider
                ),
                as_of=str(
                    payload["as_of"]
                ),
                last=float(
                    payload["last"]
                ),
                bid=(
                    float(
                        payload["bid"]
                    )
                    if payload.get(
                        "bid"
                    )
                    is not None
                    else None
                ),
                ask=(
                    float(
                        payload["ask"]
                    )
                    if payload.get(
                        "ask"
                    )
                    is not None
                    else None
                ),
                volume=(
                    float(
                        payload["volume"]
                    )
                    if payload.get(
                        "volume"
                    )
                    is not None
                    else None
                ),
                currency=str(
                    payload.get(
                        "currency",
                        "USD",
                    )
                ),
            )
        )

    provider = (
        StaticMarketDataProvider(
            name=args.provider,
            quotes=quotes,
        )
    )

    router = MarketDataRouter([
        provider
    ])

    snapshot = (
        router.build_snapshot(
            quotes,
            maximum_age_seconds=(
                args.maximum_age_seconds
            ),
            maximum_spread_bps=(
                args.maximum_spread_bps
            ),
        )
    )

    write_market_snapshot(
        snapshot
    )

    print(
        "ATLAS MARKET DATA SNAPSHOT "
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
        "Providers:",
        snapshot[
            "provider_order"
        ],
    )

    print(
        "Reference prices:",
        snapshot[
            "reference_prices"
        ],
    )

    if snapshot["failures"]:
        print("Failures:")

        for failure in (
            snapshot["failures"]
        ):
            print(
                "-",
                failure,
            )

    return (
        0
        if snapshot["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
