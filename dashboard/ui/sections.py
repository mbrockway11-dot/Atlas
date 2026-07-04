"""Atlas UI section helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st


def page_header(title: str, subtitle: str = "") -> None:
    """Render a consistent page header."""
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def atlas_section(title: str, body: str = "", *, expanded: bool = True) -> None:
    """Render a reusable Atlas section."""
    if expanded:
        st.subheader(title)
        if body:
            st.markdown(body)
    else:
        with st.expander(title, expanded=False):
            if body:
                st.markdown(body)


def developer_section(payload: dict[str, Any], *, expanded: bool = False) -> None:
    """Render developer/debug data."""
    with st.expander("Developer", expanded=expanded):
        st.json(payload)
