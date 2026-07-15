"""Authenticated read-only CCXT connectivity probe.

This script never submits, edits, cancels, or replaces orders.
Credentials are read only from environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ccxt


SUPPORTED_EXCHANGES = {
    "coinbase",
    "kraken",
    "binanceus",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def env_name(exchange_id: str, suffix: str) -> str:
    return (
        f"ATLAS_{exchange_id.upper()}_{suffix}"
        .replace("-", "_")
    )


def credential(
    exchange_id: str,
    suffix: str,
) -> str | None:
    value = os.getenv(
        env_name(exchange_id, suffix)
    )

    if value is None:
        return None

    value = value.strip()
    return value or None


def safe_error(exc: Exception) -> str:
    message = str(exc)

    secrets = [
        value
        for value in (
            os.getenv(name)
            for name in os.environ
            if name.startswith("ATLAS_")
        )
        if value
    ]

    for secret in secrets:
        message = message.replace(
            secret,
            "<REDACTED>",
        )

    return message


def summarize_balance(
    payload: dict[str, Any],
) -> dict[str, Any]:
    free = payload.get("free", {}) or {}
    used = payload.get("used", {}) or {}
    total = payload.get("total", {}) or {}

    currencies = sorted(
        {
            *free.keys(),
            *used.keys(),
            *total.keys(),
        }
    )

    rows = []

    for currency in currencies:
        free_value = float(
            free.get(currency) or 0.0
        )
        used_value = float(
            used.get(currency) or 0.0
        )
        total_value = float(
            total.get(currency) or 0.0
        )

        if (
            free_value == 0.0
            and used_value == 0.0
            and total_value == 0.0
        ):
            continue

        rows.append({
            "currency": currency,
            "free": free_value,
            "used": used_value,
            "total": total_value,
        })

    return {
        "nonzero_currency_count": len(rows),
        "balances": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--exchange",
        required=True,
        choices=sorted(SUPPORTED_EXCHANGES),
    )

    parser.add_argument(
        "--output",
        default=(
            "output/investment_ccxt_probe/"
            "authenticated_read_only_probe.json"
        ),
    )

    parser.add_argument(
        "--sandbox",
        action="store_true",
    )

    args = parser.parse_args()
    exchange_id = args.exchange

    api_key = credential(
        exchange_id,
        "API_KEY",
    )
    api_secret = credential(
        exchange_id,
        "API_SECRET",
    )
    password = credential(
        exchange_id,
        "PASSWORD",
    )
    uid = credential(
        exchange_id,
        "UID",
    )

    report: dict[str, Any] = {
        "schema_version":
            "atlas.ccxt.read_only_probe.v1",
        "exchange":
            exchange_id,
        "checked_at":
            utc_now(),
        "sandbox_requested":
            bool(args.sandbox),
        "credentials_present": {
            "api_key": bool(api_key),
            "api_secret": bool(api_secret),
            "password": bool(password),
            "uid": bool(uid),
        },
        "read_only":
            True,
        "submission_attempted":
            False,
        "live_authorized":
            False,
        "order_submission_allowed":
            False,
        "success":
            False,
        "steps": {},
    }

    exchange_class = getattr(
        ccxt,
        exchange_id,
    )

    config: dict[str, Any] = {
        "enableRateLimit": True,
    }

    if api_key:
        config["apiKey"] = api_key

    if api_secret:
        config["secret"] = api_secret

    if password:
        config["password"] = password

    if uid:
        config["uid"] = uid

    exchange = exchange_class(config)

    try:
        if args.sandbox:
            exchange.set_sandbox_mode(True)

        markets = exchange.load_markets()

        report["steps"]["markets"] = {
            "success": True,
            "market_count": len(markets),
            "sol_usd_available":
                "SOL/USD" in markets,
            "sol_usdt_available":
                "SOL/USDT" in markets,
        }

        if not api_key or not api_secret:
            report["steps"]["authentication"] = {
                "success": False,
                "reason":
                    "API key and secret are not both present.",
            }
        else:
            balance = exchange.fetch_balance()

            report["steps"]["authentication"] = {
                "success": True,
            }

            report["steps"]["balance"] = {
                "success": True,
                **summarize_balance(balance),
            }

            try:
                orders = exchange.fetch_open_orders()

                report["steps"]["open_orders"] = {
                    "success": True,
                    "count": len(orders),
                    "orders": [
                        {
                            "id": str(
                                row.get("id", "")
                            ),
                            "symbol": str(
                                row.get("symbol", "")
                            ),
                            "side": str(
                                row.get("side", "")
                            ),
                            "type": str(
                                row.get("type", "")
                            ),
                            "status": str(
                                row.get("status", "")
                            ),
                        }
                        for row in orders
                    ],
                }
            except Exception as exc:
                report["steps"]["open_orders"] = {
                    "success": False,
                    "error": safe_error(exc),
                }

            if exchange.has.get(
                "fetchPositions"
            ):
                try:
                    positions = (
                        exchange.fetch_positions()
                    )

                    report["steps"]["positions"] = {
                        "success": True,
                        "count": len(positions),
                    }
                except Exception as exc:
                    report["steps"]["positions"] = {
                        "success": False,
                        "error": safe_error(exc),
                    }
            else:
                report["steps"]["positions"] = {
                    "success": False,
                    "reason":
                        "Exchange does not advertise fetchPositions.",
                }

            report["success"] = True

    except Exception as exc:
        report["error"] = safe_error(exc)

    finally:
        close = getattr(
            exchange,
            "close",
            None,
        )

        if callable(close):
            close()

    output = Path(args.output)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "=== AUTHENTICATED READ-ONLY CCXT PROBE ==="
    )
    print(f"exchange={exchange_id}")
    print(f"sandbox={args.sandbox}")
    print(f"success={report['success']}")
    print("submission_attempted=False")
    print("live_authorized=False")
    print(f"report={output}")


if __name__ == "__main__":
    main()
