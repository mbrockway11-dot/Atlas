"""Build a read-only multi-venue market-monitor snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from atlas.investment.market_monitor import (
    MarketMonitorError,
    atomic_write_json,
    build_snapshot_payload,
    consolidate_tickers,
    evaluate_venue_health,
    parse_binance_book_ticker,
    parse_coinbase_ticker,
    parse_kraken_ticker,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/investment_market_monitor/latest_snapshot.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        tickers = []
        if "coinbase" in payload:
            tickers.append(parse_coinbase_ticker(payload["coinbase"]))
        if "kraken" in payload:
            tickers.append(parse_kraken_ticker(payload["kraken"]))
        if "binance" in payload:
            tickers.append(parse_binance_book_ticker(payload["binance"]))

        consolidated = consolidate_tickers(tickers, symbol=args.symbol)
        health = [evaluate_venue_health(ticker) for ticker in tickers]
        snapshot = build_snapshot_payload(
            tickers=tickers,
            health=health,
            consolidated=consolidated,
        )
        atomic_write_json(args.output, snapshot)
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        MarketMonitorError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({"success": True, "snapshot": snapshot}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
