
"""Performance v2 benchmark."""

from __future__ import annotations


def benchmark_snapshot(pnl: dict) -> dict:
    return {
        "benchmark": "equal_weight_BTC_ETH_SOL",
        "status": "tracking_pending_price_history",
        "portfolio_pnl_pct": pnl.get("pnl_pct", 0.0),
        "note": "Benchmark v2 placeholder until broker-fill mark-to-market price history is enabled.",
    }
