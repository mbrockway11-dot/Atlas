"""Run the G.23 Section 2 public Coinbase and Kraken monitor."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Sequence

from atlas.investment.events import EventStore
from atlas.investment.market_monitor import (
    MarketEventBridge,
    MarketMonitorSupervisor,
    SupervisorConfig,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTC-USD", "ETH-USD", "SOL-USD"],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_market_monitor/live"),
    )
    parser.add_argument(
        "--event-output-dir",
        type=Path,
        default=Path("output/investment_events"),
    )
    parser.add_argument(
        "--run-seconds",
        type=float,
        default=None,
        help="Optional bounded runtime for validation",
    )
    parser.add_argument("--disable-coinbase", action="store_true")
    parser.add_argument("--disable-kraken", action="store_true")
    parser.add_argument(
        "--enable-binance",
        action="store_true",
        help="Reserved; rejected until USDT basis handling is implemented",
    )
    parser.add_argument("--disable-event-bridge", action="store_true")
    return parser


async def run_monitor(args: argparse.Namespace) -> dict:
    bridge = None
    if not args.disable_event_bridge:
        bridge = MarketEventBridge(
            event_store=EventStore(output_dir=args.event_output_dir)
        )

    supervisor = MarketMonitorSupervisor(
        config=SupervisorConfig(
            symbols=tuple(args.symbols),
            enable_coinbase=not args.disable_coinbase,
            enable_kraken=not args.disable_kraken,
            enable_binance=args.enable_binance,
        ),
        output_dir=args.output_dir,
        event_bridge=bridge,
    )
    await supervisor.run(run_seconds=args.run_seconds)
    return {
        "success": True,
        "symbols": list(args.symbols),
        "collectors": [
            {
                "venue": collector.metrics.venue.value,
                "state": collector.metrics.state.value,
                "messages_received": collector.metrics.messages_received,
                "tickers_emitted": collector.metrics.tickers_emitted,
                "reconnects": collector.metrics.reconnects,
                "sequence_gaps": collector.metrics.sequence_gaps,
                "last_error": collector.metrics.last_error,
            }
            for collector in supervisor.collectors
        ],
        "snapshots_written": supervisor.snapshots_written,
        "events_published": 0 if bridge is None else bridge.events_published,
        "paper_only": True,
        "live_execution": False,
        "credentials_used": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = asyncio.run(run_monitor(args))
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
