
"""Investment Regime Validation Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.investment_regime_service import build_investment_regime_payload


DEFAULT_ROOT = r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"


def render_investment_regime_validation_lab_page() -> None:
    """Render Investment Regime Validation Lab."""
    st.header("Investment Regime Validation Lab")
    st.caption("Validate strategy outcomes across trend, volatility, drawdown, asset, and leadership regimes.")

    root = st.text_input("Investment engine root", value=DEFAULT_ROOT)
    rerun = st.toggle("Rerun regime validation", value=True)

    if not st.button("Run Regime Validation", type="primary"):
        st.info("Run regime validation against the sigil-engine output folder.")
        return

    with st.spinner("Running regime validation..."):
        payload = build_investment_regime_payload(root=root, rerun=rerun)

    if not payload.get("success"):
        st.error(payload.get("error", "Regime validation failed."))
        st.json(payload)
        return

    render_summary(payload)
    render_warnings(payload)
    render_return_columns(payload)
    render_regime_tables(payload)
    render_raw(payload)


def render_summary(payload: dict) -> None:
    """Render summary."""
    report = payload.get("report", {}) or {}

    st.markdown("## Regime Summary")
    st.info(payload.get("summary", ""))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price Rows", report.get("price_rows", 0))
    c2.metric("Regime Rows", report.get("regime_rows", 0))
    c3.metric("Outcome Rows", report.get("outcome_rows", 0))
    c4.metric("Joined Rows", report.get("joined_rows", 0))

    c5, c6 = st.columns(2)
    c5.metric("Warnings", len(payload.get("warnings", [])))
    c6.metric("Outcome Source", report.get("outcome_source", "n/a"))


def render_warnings(payload: dict) -> None:
    """Render warnings."""
    st.markdown("## Warnings")

    warnings = payload.get("warnings", []) or []

    if not warnings:
        st.success("No warnings.")
        return

    for warning in warnings:
        st.warning(warning)


def render_return_columns(payload: dict) -> None:
    """Render return-column selector."""
    summary = payload.get("return_summary", {}) or {}
    columns = summary.get("return_columns", []) or []

    st.markdown("## Return Columns")

    if not columns:
        st.info("No return columns detected.")
        return

    st.dataframe(
        pd.DataFrame([{"return_column": col} for col in columns]),
        width="stretch",
    )


def render_regime_tables(payload: dict) -> None:
    """Render regime performance tables."""
    summary = payload.get("return_summary", {}) or {}
    summaries = summary.get("summaries", {}) or {}

    if not summaries:
        st.info("No regime summaries available.")
        return

    selected_col = st.selectbox("Select return column", list(summaries.keys()))
    data = summaries.get(selected_col, {}) or {}

    st.markdown(f"## Regime Performance: `{selected_col}`")

    overall = data.get("overall", {}) or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Count", overall.get("count", 0))
    c2.metric("Win Rate", format_number(overall.get("win_rate")))
    c3.metric("Mean", format_number(overall.get("mean")))
    c4.metric("Median", format_number(overall.get("median")))

    tabs = st.tabs([
        "Trend",
        "Volatility",
        "Drawdown",
        "Leadership Asset",
        "Trade Asset",
    ])

    with tabs[0]:
        render_group_table(data.get("by_trend_regime", {}) or {})

    with tabs[1]:
        render_group_table(data.get("by_volatility_regime", {}) or {})

    with tabs[2]:
        render_group_table(data.get("by_drawdown_regime", {}) or {})

    with tabs[3]:
        render_group_table(data.get("by_leadership_asset", {}) or {})

    with tabs[4]:
        render_group_table(data.get("by_asset", {}) or {})


def render_group_table(grouped: dict) -> None:
    """Render grouped regime table."""
    if not grouped:
        st.info("No grouped data available.")
        return

    rows = []
    for key, values in grouped.items():
        rows.append(
            {
                "group": key,
                "count": values.get("count"),
                "win_rate": values.get("win_rate"),
                "mean": values.get("mean"),
                "median": values.get("median"),
                "min": values.get("min"),
                "max": values.get("max"),
            }
        )

    df = pd.DataFrame(rows)

    if not df.empty and "mean" in df.columns:
        df = df.sort_values("mean", ascending=False, na_position="last")

    st.dataframe(df, width="stretch")


def render_raw(payload: dict) -> None:
    """Render raw payload."""
    with st.expander("Raw Regime Validation Payload", expanded=False):
        st.json(payload)


def format_number(value) -> str:
    """Format numeric values."""
    try:
        return f"{float(value):.4f}"
    except Exception:
        return "n/a"
