"""Shared Structural Codex dashboard renderer."""

from __future__ import annotations

import json

import streamlit as st


def render_structural_codex(codex: dict, *, heading_level: int = 2) -> None:
    """Render an evidence-backed Codex without hiding its metric basis."""
    if not codex.get("success"):
        st.error("Structural Codex could not be generated.")
        for error in codex.get("errors", []):
            st.error(error)
        return

    prefix = "#" * max(1, min(heading_level, 6))
    st.markdown(f"{prefix} {codex.get('title', 'THE STRUCTURAL CODEX')}")
    st.markdown(f"### {codex.get('name', '')}")

    birth = codex.get("birth", {}) or {}
    st.caption(
        " • ".join(
            str(value or "unknown")
            for value in (birth.get("date"), birth.get("time"), birth.get("place"))
        )
    )

    archetype = codex.get("archetype", {}) or {}
    st.markdown("### Codex Archetype")
    st.markdown(f"# **{archetype.get('label', 'Unresolved')}**")
    confidence = archetype.get("confidence", {}) or {}
    c1, c2, c3 = st.columns(3)
    c1.metric("Structural Role", archetype.get("structural_role", "unresolved"))
    c2.metric("Subtype", archetype.get("structural_subtype", "unresolved"))
    c3.metric("Confidence", f"{confidence.get('percent', 0)}%")

    for index, section in enumerate(codex.get("sections", [])):
        with st.expander(section.get("title", "Untitled Section"), expanded=index == 0):
            st.write(section.get("summary", ""))
            for claim in section.get("claims", []):
                st.caption(
                    f"{claim.get('claim_type', 'claim')} · "
                    f"{claim.get('confidence_label', 'unrated')} · "
                    f"evidence: {', '.join(claim.get('evidence_refs', [])) or 'none'}"
                )
                st.write(claim.get("text", ""))

            metrics = section.get("metrics", [])
            if metrics:
                st.markdown("**Metric basis**")
                st.dataframe(
                    [
                        {
                            "id": row.get("id"),
                            "metric": row.get("label"),
                            "value": row.get("value"),
                            "unit": row.get("unit"),
                            "kind": row.get("evidence_kind"),
                            "method": row.get("method"),
                            "source": row.get("source"),
                        }
                        for row in metrics
                    ],
                    width="stretch",
                    hide_index=True,
                )

    population = codex.get("population_context", {}) or {}
    if population.get("available"):
        with st.expander("Closest Structural Neighbors", expanded=False):
            st.dataframe(
                [
                    {
                        "profile": row.get("profile_key"),
                        "name": row.get("name"),
                        "similarity_percent": row.get("similarity_percent"),
                        "shared": "; ".join(row.get("shared", [])),
                    }
                    for row in population.get("neighbors", [])
                ],
                width="stretch",
                hide_index=True,
            )

    with st.expander("Full Evidence Registry", expanded=False):
        st.dataframe(codex.get("evidence_registry", []), width="stretch", hide_index=True)

    with st.expander("Method and Limitations", expanded=False):
        methodology = codex.get("methodology", {}) or {}
        st.json({key: value for key, value in methodology.items() if key != "limitations"})
        for limitation in methodology.get("limitations", []):
            st.warning(limitation)

    profile_key = codex.get("profile_key", "profile")
    c1, c2 = st.columns(2)
    c1.download_button(
        "Download Structural Codex Markdown",
        data=(codex.get("exports", {}) or {}).get("markdown", ""),
        file_name=f"{profile_key}_structural_codex.md",
        mime="text/markdown",
    )
    c2.download_button(
        "Download Structural Codex JSON",
        data=json.dumps(codex, indent=2, ensure_ascii=False),
        file_name=f"{profile_key}_structural_codex.json",
        mime="application/json",
    )
