
"""Portfolio State snapshots."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


SNAPSHOTS_CSV = Path("output/investment_portfolio_state/portfolio_state_snapshots.csv")


def append_state_snapshot(state: dict) -> None:
    SNAPSHOTS_CSV.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "timestamp": state.get("timestamp"),
        "success": state.get("success"),
        "mode": state.get("mode"),
        "current_equity": (state.get("equity", {}) or {}).get("current_equity"),
        "pnl": (state.get("equity", {}) or {}).get("pnl"),
        "pnl_pct": (state.get("equity", {}) or {}).get("pnl_pct"),
        "risky_weight": (state.get("exposure", {}) or {}).get("risky_weight"),
        "cash_weight": (state.get("exposure", {}) or {}).get("cash_weight"),
        "reserved_cash_weight": (state.get("exposure", {}) or {}).get("reserved_cash_weight"),
        "gross_exposure": (state.get("exposure", {}) or {}).get("gross_exposure"),
        "net_exposure": (state.get("exposure", {}) or {}).get("net_exposure"),
        "direction": (state.get("decision", {}) or {}).get("direction"),
        "confidence": (state.get("decision", {}) or {}).get("confidence"),
        "target_net_exposure": (state.get("decision", {}) or {}).get("target_net_exposure"),
        "risk_label": (state.get("decision", {}) or {}).get("risk_label"),
        "risky_position_count": (state.get("counts", {}) or {}).get("risky_position_count"),
        "pending_order_count": (state.get("counts", {}) or {}).get("pending_order_count"),
    }

    new = pd.DataFrame([row])

    if SNAPSHOTS_CSV.exists():
        old = pd.read_csv(SNAPSHOTS_CSV)
        out = pd.concat([old, new], ignore_index=True)
    else:
        out = new

    out.to_csv(SNAPSHOTS_CSV, index=False)
