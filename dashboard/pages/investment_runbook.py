
"""Investment Runbook Mission Control page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from atlas.services.investment_runbook_service import load_runbook_payload


def render() -> None:
    st.title("Investment Runbook Mission Control")

    payload = load_runbook_payload()

    if not payload["raw"]:
        st.warning("No runbook output found. Run `python scripts/daily_investment_runbook.py` first.")
        return

    decision = payload["decision"]
    simulation = payload["simulation"]

    st.subheader("Decision")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Direction", decision.get("final_direction", "NA"))
    c2.metric("Confidence", pct(decision.get("final_confidence")))
    c3.metric("Target exposure", pct(decision.get("target_net_exposure")))
    c4.metric("Cash", pct(decision.get("target_cash_weight")))

    st.caption(payload["summary"])

    st.subheader("Execution Plan")
    orders = pd.DataFrame(payload["orders"])
    if not orders.empty:
        st.dataframe(orders, use_container_width=True)
    else:
        st.info("No execution orders found.")

    st.subheader("Simulation")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Filled", pct(simulation.get("filled_weight")))
    s2.metric("Waiting", pct(simulation.get("waiting_weight")))
    s3.metric("Cash", pct(simulation.get("cash_weight")))
    s4.metric("Cost drag", pct(simulation.get("total_cost_drag")))

    warnings = simulation.get("warnings", []) or []
    if warnings:
        st.warning(" | ".join(warnings))

    st.subheader("Execution Timeline")
    steps = pd.DataFrame(payload["steps"])
    if not steps.empty:
        timeline = steps[["name", "success", "started", "ended", "returncode"]].copy()
        st.dataframe(timeline, use_container_width=True)

    st.subheader("Historical Run Tracking")
    history = payload["history"]
    if not history.empty:
        st.line_chart(history[["confidence", "target_exposure", "cash_weight", "filled_weight"]])
        st.dataframe(history.tail(25), use_container_width=True)
    else:
        st.info("No historical runbook history yet.")

    with st.expander("Raw runbook JSON"):
        st.json(payload["raw"])


def pct(value) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "NA"


if __name__ == "__main__":
    render()
