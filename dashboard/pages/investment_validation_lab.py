
"""Investment Validation Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.investment_validation_service import build_investment_validation_payload


DEFAULT_ROOT = r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"


def render_investment_validation_lab_page() -> None:
    """Render Investment Validation Lab."""
    st.header("Investment Validation Lab")
    st.caption("Audit trading outputs, sample size, missingness, signals, forward returns, and validation risks.")

    root = st.text_input("Investment engine root", value=DEFAULT_ROOT)
    rerun_audit = st.toggle("Rerun audit", value=True)

    if not st.button("Run Investment Validation", type="primary"):
        st.info("Run validation against the sigil-engine output folder.")
        return

    with st.spinner("Running investment validation..."):
        payload = build_investment_validation_payload(root=root, rerun_audit=rerun_audit)

    if not payload.get("success"):
        st.error(payload.get("error", "Investment validation failed."))
        st.json(payload)
        return

    render_summary(payload)
    render_warnings(payload)
    render_file_inventory(payload)
    render_signals(payload)
    render_forward_returns(payload)
    render_raw(payload)


def render_summary(payload: dict) -> None:
    st.markdown("## Validation Summary")
    st.info(payload.get("summary", ""))

    audit = payload.get("audit", {}) or {}
    files = payload.get("files", {}) or {}

    total_expected = 0
    total_found = 0
    total_rows = 0

    for group_files in files.values():
        for item in group_files:
            total_expected += 1
            if item.get("status") == "ok":
                total_found += 1
                total_rows += int(item.get("rows", 0) or 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected Files", total_expected)
    c2.metric("Found Files", total_found)
    c3.metric("Rows Scanned", total_rows)
    c4.metric("Warnings", len(payload.get("warnings", [])))


def render_warnings(payload: dict) -> None:
    st.markdown("## Warnings")

    warnings = payload.get("warnings", []) or []

    if not warnings:
        st.success("No warnings.")
        return

    for warning in warnings:
        st.warning(warning)


def render_file_inventory(payload: dict) -> None:
    st.markdown("## File Inventory")

    rows = []
    for group, group_files in (payload.get("files", {}) or {}).items():
        for item in group_files:
            rows.append(
                {
                    "group": group,
                    "path": item.get("path"),
                    "resolved_path": item.get("resolved_path"),
                    "status": item.get("status"),
                    "rows": item.get("rows"),
                    "columns": item.get("column_count"),
                    "date_min": item.get("date_min"),
                    "date_max": item.get("date_max"),
                    "asset_count": item.get("asset_count"),
                    "duplicate_rows": item.get("duplicate_rows"),
                    "duplicate_asset_timestamps": item.get("duplicate_asset_timestamps"),
                }
            )

    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch")
    else:
        st.info("No file inventory available.")


def render_signals(payload: dict) -> None:
    st.markdown("## Signal Audit")

    signals = payload.get("signals", {}) or {}
    files = signals.get("files", []) or []

    c1, c2 = st.columns(2)
    c1.metric("Signal Files Found", signals.get("signal_files_found", 0))
    c2.metric("Signal File Reports", len(files))

    if not files:
        st.info("No signal files found.")
        return

    rows = []
    for item in files:
        rows.append(
            {
                "path": item.get("path"),
                "rows": item.get("rows"),
                "asset_count": item.get("asset_count"),
                "rows_by_asset": item.get("rows_by_asset"),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")

    with st.expander("Signal details", expanded=False):
        st.json(files)


def render_forward_returns(payload: dict) -> None:
    st.markdown("## Forward Return Audit")

    reports = ((payload.get("forward_returns", {}) or {}).get("reports", []) or [])

    if not reports:
        st.info("No forward return reports available.")
        return

    for report in reports:
        st.markdown(f"### `{report.get('path')}`")

        summary = report.get("summary", {}) or {}
        rows = []

        for col, values in summary.items():
            rows.append(
                {
                    "return_column": col,
                    "count": values.get("count"),
                    "win_rate_gt_0": values.get("win_rate_gt_0"),
                    "mean": values.get("mean"),
                    "median": values.get("median"),
                    "min": values.get("min"),
                    "max": values.get("max"),
                }
            )

        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch")

        with st.expander("By-asset forward returns", expanded=False):
            st.json(summary)


def render_raw(payload: dict) -> None:
    with st.expander("Raw Investment Validation Payload", expanded=False):
        st.json(payload)
