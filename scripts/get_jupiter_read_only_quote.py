"""Fetch a read-only Jupiter quote; never build or submit a transaction."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from atlas.investment.solana import (
    JupiterApiError,
    JupiterQuoteRequest,
    JupiterReadOnlyClient,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-mint", required=True)
    parser.add_argument("--output-mint", required=True)
    parser.add_argument("--amount", type=int, required=True)
    parser.add_argument("--slippage-bps", type=int, default=50)
    parser.add_argument("--api-key", default="")
    args = parser.parse_args()

    try:
        quote = JupiterReadOnlyClient(
            api_key=args.api_key or os.getenv("JUPITER_API_KEY", "")
        ).get_quote(
            JupiterQuoteRequest(
                input_mint=args.input_mint,
                output_mint=args.output_mint,
                amount=args.amount,
                slippage_bps=args.slippage_bps,
            )
        )
    except JupiterApiError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({"success": True, "quote": asdict(quote)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
