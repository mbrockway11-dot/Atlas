"""Service-backed Research Corpus dashboard page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.services.research_corpus_service import ResearchCorpusPayload, build_research_corpus_payload


FILTER_COLUMNS = {
    "entity_type": "Entity Type",
    "function": "Function",
    "expression": "Expression",
    "state": "State",
}

SEARCH_COLUMNS = [
    "entity_id",
    "name",
    "tags",
    "notes",
]


def render_research_corpus_page() -> None:
    """Render the Research Corpus as a thin UI layer over the service."""
    st.header("Research Corpus")
    st.caption("Atlas Database browser powered by the canonical corpus service.")

    payload = build_research_corpus_payload()
    render_research_corpus_payload(payload)


def render_research_corpus_payload(payload: ResearchCorpusPayload) -> None:
    """Render the canonical Research Corpus service payload."""
    if not payload.success:
        st.error("\n".join(payload.errors))
        return

    render_corpus_metrics(payload)
    render_corpus_warnings(payload.warnings)

    if not payload.rows:
        st.info("No indexed entities yet. Build a profile first.")
        return

    df = pd.DataFrame(payload.rows)
    filtered = render_corpus_filters(df)

    st.markdown("### Results")
    st.dataframe(filtered, width="stretch")

    with st.expander("Raw Database View"):
        st.dataframe(df, width="stretch")


def render_corpus_metrics(payload: ResearchCorpusPayload) -> None:
    """Render Research Corpus metrics returned by the service."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Indexed entities", payload.metrics.get("indexed_entities", 0))
    with col2:
        st.metric("Rows", payload.metrics.get("row_count", 0))
    with col3:
        st.metric("Load warnings", payload.metrics.get("load_errors", 0))


def render_corpus_warnings(warnings: list[str]) -> None:
    """Render non-fatal Research Corpus service warnings."""
    if not warnings:
        return

    with st.expander("Corpus load warnings"):
        for warning in warnings:
            st.warning(warning)


def render_corpus_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render UI filters and return the selected dataframe view."""
    st.markdown("### Filters")

    selected_filters = render_select_filters(df)
    search = st.text_input("Search name, tag, notes, or entity ID")

    filtered = apply_select_filters(df, selected_filters)
    return apply_search_filter(filtered, search)


def render_select_filters(df: pd.DataFrame) -> dict[str, str]:
    """Render selectbox filters for the corpus table."""
    selected: dict[str, str] = {}
    columns = st.columns(len(FILTER_COLUMNS))

    for index, (column, label) in enumerate(FILTER_COLUMNS.items()):
        with columns[index]:
            options = sorted(df[column].dropna().astype(str).unique().tolist())
            selected[column] = st.selectbox(label, ["All"] + options)

    return selected


def apply_select_filters(df: pd.DataFrame, selected_filters: dict[str, str]) -> pd.DataFrame:
    """Apply dashboard selectbox filters to a dataframe view."""
    filtered = df.copy()

    for column, selected in selected_filters.items():
        if selected != "All":
            filtered = filtered[filtered[column].astype(str) == selected]

    return filtered


def apply_search_filter(df: pd.DataFrame, search: str) -> pd.DataFrame:
    """Apply dashboard free-text search to a dataframe view."""
    query = search.strip().lower()
    if not query:
        return df

    searchable = df.apply(build_search_blob, axis=1)
    return df[searchable.str.contains(query, case=False, na=False, regex=False)]


def build_search_blob(row: pd.Series) -> str:
    """Build a normalized search string for one corpus row."""
    return " ".join(str(row.get(column, "")) for column in SEARCH_COLUMNS).lower()
