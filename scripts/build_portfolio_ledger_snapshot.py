"""Replay fills and build a canonical G.21 portfolio snapshot."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from atlas.investment.ledger import (
    FillEvent,
    LedgerError,
    LedgerSide,
    PortfolioLedger,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--portfolio-id", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_ledger"),
    )
    parser.add_argument("--starting-cash", type=float, default=100000.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        fills_payload = payload["fills"]
        fills = [
            FillEvent(
                fill_id=str(item["fill_id"]),
                broker_order_id=str(item["broker_order_id"]),
                client_order_id=str(item["client_order_id"]),
                symbol=str(item["symbol"]),
                side=LedgerSide(str(item["side"]).upper()),
                quantity=float(item["quantity"]),
                price=float(item["price"]),
                fee=float(item.get("fee", 0.0)),
                timestamp=str(item["timestamp"]),
                currency=str(item.get("currency", "USD")),
                paper_only=bool(item.get("paper_only", True)),
                live_execution=bool(item.get("live_execution", False)),
                metadata=dict(item.get("metadata", {})),
            )
            for item in fills_payload
        ]

        ledger = PortfolioLedger.replay(
            portfolio_id=args.portfolio_id,
            output_dir=args.output_dir,
            fills=fills,
            starting_cash={"USD": args.starting_cash},
        )
        if isinstance(payload.get("prices"), dict):
            ledger.mark_prices(payload["prices"])
        snapshot = ledger.snapshot()
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        LedgerError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({"success": True, "snapshot": asdict(snapshot)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
