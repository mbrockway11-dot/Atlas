"""Read-only public multi-venue market monitor dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

OUTPUT_DIR = Path("output/investment_market_monitor/live")


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


st.title("Multi-Venue Market Monitor")
st.caption("Public Coinbase and Kraken market data — read only")

status = read_json(OUTPUT_DIR / "monitor_status.json")
if status is None:
    st.info(
        "No runtime status exists. Run scripts/run_public_market_monitor.py first."
    )
else:
    st.subheader("Collector health")
    collectors = status.get("collectors", [])
    if collectors:
        st.dataframe(collectors, use_container_width=True, hide_index=True)
    st.write(
        {
            "snapshots_written": status.get("snapshots_written"),
            "latest_ticker_count": status.get("latest_ticker_count"),
            "paper_only": status.get("paper_only"),
            "live_execution": status.get("live_execution"),
            "credentials_used": status.get("credentials_used"),
        }
    )

snapshot_paths = sorted(
    path
    for path in OUTPUT_DIR.glob("*.json")
    if path.name != "monitor_status.json"
)
for path in snapshot_paths:
    snapshot = read_json(path)
    if snapshot is None:
        continue
    consolidated = snapshot.get("consolidated", {})
    st.subheader(str(snapshot.get("symbol", path.stem)))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Best bid", consolidated.get("best_bid"))
    col2.metric("Best ask", consolidated.get("best_ask"))
    col3.metric("Spread bps", consolidated.get("spread_bps"))
    col4.metric(
        "Divergence bps",
        consolidated.get("cross_venue_divergence_bps"),
    )
    st.dataframe(
        snapshot.get("tickers", []),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        snapshot.get("health", []),
        use_container_width=True,
        hide_index=True,
    )

st.info(
    "This page has no execution controls, credentials, account access, "
    "or order-submission capability."
)
