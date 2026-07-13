"""Read-only provider diagnostics for Atlas market data."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any, Iterable

from atlas.investment.market_data.providers import (
    MarketDataProvider,
)
from atlas.investment.market_data.service import (
    evaluate_quote_quality,
)


def diagnose_provider(
    provider: MarketDataProvider,
    *,
    symbols: Iterable[str],
    maximum_age_seconds: float | None = None,
    maximum_spread_bps: float | None = None,
) -> dict[str, Any]:
    rows: list[
        dict[str, Any]
    ] = []

    for symbol in symbols:
        started = time.perf_counter()

        try:
            quote = provider.get_quote(
                symbol
            )

            quality = evaluate_quote_quality(
                quote,
                maximum_age_seconds=(
                    maximum_age_seconds
                ),
                maximum_spread_bps=(
                    maximum_spread_bps
                ),
            )

            success = bool(
                quality["valid"]
            )

            error = ""

        except Exception as exception:
            quote = None

            quality = {
                "valid": False,
                "errors": [
                    str(exception)
                ],
                "warnings": [],
            }

            success = False
            error = str(
                exception
            )

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1_000.0

        rows.append({
            "symbol": str(
                symbol
            ),
            "success": success,
            "provider": (
                provider.name
            ),
            "elapsed_ms": (
                elapsed_ms
            ),
            "quote": (
                quote.to_dict()
                if quote is not None
                else {}
            ),
            "quality": quality,
            "error": error,
        })

    successful = sum(
        1
        for row in rows
        if row["success"]
    )

    return {
        "success": (
            successful
            == len(rows)
        ),
        "generated_at": (
            datetime.now(
                UTC
            ).isoformat()
        ),
        "provider": (
            provider.name
        ),
        "capabilities": (
            provider
            .capabilities
            .to_dict()
        ),
        "counts": {
            "requested": len(
                rows
            ),
            "successful": (
                successful
            ),
            "failed": (
                len(rows)
                - successful
            ),
        },
        "rows": rows,
        "contract": {
            "diagnostic_only": True,
            "read_only": True,
            "credentials_used": False,
            "submits_orders": False,
            "live_execution": False,
        },
    }


__all__ = [
    "diagnose_provider",
]
