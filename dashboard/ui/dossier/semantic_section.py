"""Semantic intelligence section for Atlas dossier."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.components.dossier_common import confidence_label, data_expander


def render_semantic_section(payload: dict[str, Any]) -> None:
    """Render semantic intelligence domains from canonical payload."""
    semantic = payload.get("semantic", {})

    if not isinstance(semantic, dict) or not semantic.get("success"):
        return

    st.markdown("## Semantic Intelligence")

    executive = semantic.get("executive_summary", "")
    if executive:
        with st.container(border=True):
            st.markdown("### Executive Synthesis")
            st.markdown(executive)

    confidence = semantic.get("confidence", {})
    if confidence:
        st.caption(f"Semantic Confidence: {confidence_label(confidence)}")

    domains = semantic.get("domains", [])
    if not isinstance(domains, list):
        return

    for domain in domains:
        render_semantic_domain(domain)


def render_semantic_domain(domain: dict[str, Any]) -> None:
    """Render one semantic domain card."""
    if not isinstance(domain, dict):
        return

    title = domain.get("title") or domain.get("domain") or "Semantic Domain"
    summary = domain.get("summary", "")
    confidence = domain.get("confidence", {})
    evidence = domain.get("evidence", [])

    with st.container(border=True):
        st.markdown(f"### {title}")

        if confidence:
            st.caption(f"Confidence: {confidence_label(confidence)}")

        if summary:
            st.markdown(summary)

        if evidence:
            data_expander("Evidence", evidence, expanded=False)
