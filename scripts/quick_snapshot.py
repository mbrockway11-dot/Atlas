"""Fast current-price snapshot for frequent mark-to-market ticks.

The websocket market monitor carries ~1-4 min of connection/keepalive overhead
per run -- fine for a daily rebalance, far too heavy to run every few minutes.
Marking the book only needs current prices, so this pulls them directly via
yfinance (a few seconds for the universe) and writes the same snapshot shape
`run_forward_paper.py --mark-only` reads. The daily rebalance still rebuilds the
full monitor snapshot; this is only the lightweight price refresh for marks.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

UNIVERSE = [
    "BTC-USD", "ETH-USD", "SOL-USD", "AAVE-USD", "ADA-USD",
    "AVAX-USD", "BNB-USD", "LINK-USD", "XRP-USD", "DOGE-USD",
]
OUT = Path("output/investment_market_data/latest_market_snapshot.json")


def main() -> int:
    data = yf.download(
        UNIVERSE, period="1d", interval="1m",
        progress=False, threads=True, auto_adjust=False,
    )
    try:
        close = data["Close"]
    except (KeyError, TypeError):
        print("No price data returned.", file=sys.stderr)
        return 1

    prices: dict[str, float] = {}
    for ticker in UNIVERSE:
        try:
            series = close[ticker].dropna()
            if len(series):
                prices[ticker] = round(float(series.iloc[-1]), 8)
        except (KeyError, IndexError):
            continue
    if not prices:
        print("No usable prices.", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).isoformat()
    snapshot = {
        "snapshot_id": "QUICK-" + now,
        "generated_at": now,
        "provider_order": ["yfinance"],
        "success": True,
        "reference_prices": prices,
        "quotes": [
            {"symbol": t, "last": p, "midpoint": p, "provider": "yfinance"}
            for t, p in prices.items()
        ],
        "symbols_requested": UNIVERSE,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", "utf-8")
    print(f"quick snapshot: {len(prices)} prices -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
