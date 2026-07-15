"""Promote live Market Monitor symbol snapshots into an Atlas quote fixture.

Reads per-symbol JSON artifacts from:
    output/investment_market_monitor/live/

Writes one aggregate fixture consumed by build_market_data_snapshot.py:
    output/investment_market_data/public_monitor_quotes.json

This module is read-only with respect to exchanges and never submits orders.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_INPUT_DIR = Path(
    "output/investment_market_monitor/live"
)

DEFAULT_OUTPUT_PATH = Path(
    "output/investment_market_data/public_monitor_quotes.json"
)

IGNORED_FILENAMES = {
    "monitor_status.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    parser.add_argument(
        "--maximum-age-seconds",
        type=float,
        default=300.0,
    )
    parser.add_argument(
        "--required-symbols",
        nargs="*",
        default=[],
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def finite_number(
    value: Any,
) -> float | None:
    try:
        number = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(number):
        return None

    return number


def normalized_timestamp(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return text

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=UTC
        )

    return parsed.astimezone(
        UTC
    ).isoformat()


def timestamp_age_seconds(
    value: str | None,
) -> float | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=UTC
        )

    return max(
        0.0,
        (
            datetime.now(UTC)
            - parsed.astimezone(UTC)
        ).total_seconds(),
    )


def walk_mappings(
    value: Any,
) -> Iterable[Mapping[str, Any]]:
    if isinstance(
        value,
        Mapping,
    ):
        yield value

        for nested in value.values():
            yield from walk_mappings(
                nested
            )

    elif isinstance(
        value,
        list,
    ):
        for nested in value:
            yield from walk_mappings(
                nested
            )


def candidate_score(
    payload: Mapping[str, Any],
) -> int:
    score = 0

    numeric_keys = {
        "last",
        "price",
        "midpoint",
        "mid",
        "mark_price",
        "close",
        "bid",
        "ask",
    }

    time_keys = {
        "as_of",
        "timestamp",
        "received_at",
        "updated_at",
        "generated_at",
    }

    if any(
        finite_number(
            payload.get(key)
        )
        is not None
        for key
        in numeric_keys
    ):
        score += 10

    if (
        finite_number(
            payload.get("bid")
        )
        is not None
        and finite_number(
            payload.get("ask")
        )
        is not None
    ):
        score += 5

    if any(
        payload.get(key)
        for key
        in time_keys
    ):
        score += 3

    if payload.get(
        "provider"
    ) or payload.get(
        "venue"
    ):
        score += 2

    label = str(
        payload.get(
            "type",
            payload.get(
                "kind",
                payload.get(
                    "source",
                    "",
                ),
            ),
        )
    ).upper()

    if any(
        token in label
        for token in (
            "AGGREGATE",
            "COMPOSITE",
            "CONSENSUS",
            "BEST",
        )
    ):
        score += 4

    return score


def select_quote_mapping(
    payload: Any,
) -> Mapping[str, Any]:
    candidates = list(
        walk_mappings(
            payload
        )
    )

    if not candidates:
        raise ValueError(
            "SYMBOL_SNAPSHOT_HAS_NO_OBJECTS"
        )

    ranked = sorted(
        candidates,
        key=candidate_score,
        reverse=True,
    )

    best = ranked[0]

    if candidate_score(
        best
    ) < 10:
        raise ValueError(
            "SYMBOL_SNAPSHOT_HAS_NO_PRICE"
        )

    return best


def first_number(
    payload: Mapping[str, Any],
    keys: Iterable[str],
) -> float | None:
    for key in keys:
        value = finite_number(
            payload.get(key)
        )

        if value is not None:
            return value

    return None


def first_text(
    payload: Mapping[str, Any],
    keys: Iterable[str],
) -> str | None:
    for key in keys:
        value = payload.get(
            key
        )

        if value is None:
            continue

        text = str(
            value
        ).strip()

        if text:
            return text

    return None


def quote_from_payload(
    *,
    symbol: str,
    payload: Any,
    maximum_age_seconds: float,
) -> dict[str, Any]:
    selected = select_quote_mapping(
        payload
    )

    bid = first_number(
        selected,
        (
            "bid",
            "best_bid",
            "bid_price",
        ),
    )

    ask = first_number(
        selected,
        (
            "ask",
            "best_ask",
            "ask_price",
        ),
    )

    last = first_number(
        selected,
        (
            "last",
            "price",
            "midpoint",
            "mid",
            "mark_price",
            "close",
        ),
    )

    if (
        last is None
        and bid is not None
        and ask is not None
    ):
        last = (
            bid + ask
        ) / 2.0

    if last is None:
        raise ValueError(
            "PRICE_NOT_RESOLVED:"
            + symbol
        )

    as_of_raw = first_text(
        selected,
        (
            "as_of",
            "timestamp",
            "received_at",
            "updated_at",
            "generated_at",
        ),
    )

    as_of = normalized_timestamp(
        as_of_raw
    ) or utc_now()

    age_seconds = timestamp_age_seconds(
        as_of
    )

    if (
        age_seconds is not None
        and age_seconds
        > maximum_age_seconds
    ):
        raise ValueError(
            "STALE_MONITOR_QUOTE:"
            + symbol
            + ":"
            + str(
                round(
                    age_seconds,
                    3,
                )
            )
        )

    provider = first_text(
        selected,
        (
            "provider",
            "venue",
            "source",
        ),
    ) or "PUBLIC_MARKET_MONITOR"

    volume = first_number(
        selected,
        (
            "volume",
            "base_volume",
            "quote_volume",
            "size",
        ),
    )

    return {
        "symbol": symbol,
        "provider": provider,
        "as_of": as_of,
        "last": last,
        "bid": bid,
        "ask": ask,
        "volume": volume,
        "currency": str(
            selected.get(
                "currency",
                "USD",
            )
        ),
    }


def load_symbol_file(
    path: Path,
    *,
    maximum_age_seconds: float,
) -> tuple[str, dict[str, Any]]:
    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    symbol = str(
        payload.get(
            "symbol",
            path.stem,
        )
        if isinstance(
            payload,
            Mapping,
        )
        else path.stem
    ).strip().upper()

    if not symbol:
        raise ValueError(
            "SYMBOL_NOT_RESOLVED:"
            + str(path)
        )

    quote = quote_from_payload(
        symbol=symbol,
        payload=payload,
        maximum_age_seconds=(
            maximum_age_seconds
        ),
    )

    return (
        symbol,
        quote,
    )


def write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(payload),
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def main() -> int:
    args = parse_args()

    if not args.input_dir.exists():
        raise FileNotFoundError(
            str(
                args.input_dir
            )
        )

    required = {
        str(symbol)
        .strip()
        .upper()
        for symbol
        in args.required_symbols
        if str(symbol).strip()
    }

    quotes: dict[
        str,
        dict[str, Any],
    ] = {}

    failures: list[
        dict[str, str],
    ] = []

    for path in sorted(
        args.input_dir.glob(
            "*.json"
        )
    ):
        if path.name in IGNORED_FILENAMES:
            continue

        try:
            symbol, quote = (
                load_symbol_file(
                    path,
                    maximum_age_seconds=(
                        args.maximum_age_seconds
                    ),
                )
            )

            quotes[
                symbol
            ] = quote

        except (
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            failures.append({
                "file": str(
                    path
                ),
                "error": (
                    type(exc).__name__
                    + ": "
                    + str(exc)
                ),
            })

    missing = sorted(
        required
        - set(
            quotes
        )
    )

    success = bool(
        quotes
        and not missing
    )

    fixture = {
        "success": success,
        "version": (
            "atlas.market-monitor-promotion.v1"
        ),
        "generated_at": utc_now(),
        "source_directory": str(
            args.input_dir
        ),
        "provider": (
            "PUBLIC_MARKET_MONITOR"
        ),
        "quotes": {
            symbol: {
                key: value
                for key, value
                in quote.items()
                if key
                not in {
                    "symbol",
                    "provider",
                }
            }
            for symbol, quote
            in sorted(
                quotes.items()
            )
        },
        "providers_by_symbol": {
            symbol: quote[
                "provider"
            ]
            for symbol, quote
            in sorted(
                quotes.items()
            )
        },
        "counts": {
            "resolved": len(
                quotes
            ),
            "failed": len(
                failures
            ),
            "required": len(
                required
            ),
            "missing_required": len(
                missing
            ),
        },
        "missing_required_symbols": (
            missing
        ),
        "failures": failures,
        "contract": {
            "paper_only": True,
            "live_execution": False,
            "credentials_used": False,
            "source_is_public_market_data": True,
            "freshness_checked": True,
        },
    }

    write_json_atomic(
        args.output,
        fixture,
    )

    print(
        json.dumps(
            {
                "success": success,
                "output": str(
                    args.output
                ),
                "resolved": sorted(
                    quotes
                ),
                "missing": missing,
                "failures": failures,
            },
            sort_keys=True,
        )
    )

    return (
        0
        if success
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
