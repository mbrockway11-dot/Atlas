"""Audit installed Atlas market-data provider adapters."""

from __future__ import annotations

from atlas.investment.market_data import (
    CoinbasePublicMarketDataProvider,
    StaticMarketDataProvider,
)


def main() -> int:
    providers = [
        StaticMarketDataProvider(),
        CoinbasePublicMarketDataProvider(),
    ]

    rows = []

    for provider in providers:
        capabilities = (
            provider
            .capabilities
            .to_dict()
        )

        row = {
            "provider": (
                provider.name
            ),
            **capabilities,
        }

        rows.append(row)

    names = [
        row["provider"]
        for row in rows
    ]

    unique_names = (
        len(names)
        == len(set(names))
    )

    coinbase = next(
        row
        for row in rows
        if row["provider"]
        == "COINBASE_PUBLIC"
    )

    coinbase_boundary = bool(
        coinbase["quotes"]
        and coinbase["bars"]
        and coinbase[
            "network_required"
        ]
        and not coinbase[
            "credentials_required"
        ]
        and not coinbase["trades"]
        and not coinbase[
            "order_book"
        ]
        and not coinbase[
            "funding_rates"
        ]
        and not coinbase[
            "open_interest"
        ]
    )

    success = bool(
        unique_names
        and coinbase_boundary
    )

    print(
        "ATLAS MARKET DATA PROVIDERS "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )

    print(
        "Providers:",
        names,
    )

    print(
        "Unique names:",
        unique_names,
    )

    print(
        "Coinbase public boundary:",
        coinbase_boundary,
    )

    for row in rows:
        print(row)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
