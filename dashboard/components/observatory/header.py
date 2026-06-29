"""Observatory header component."""

import streamlit as st


def render_observatory_header(acf: dict) -> None:
    """Render top-level profile header."""
    identity = acf["identity"]
    metadata = acf["metadata"]

    st.subheader(identity["name"])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Entity Type", identity["entity_type"])
    c2.metric("Historical Layers", 21)
    c3.metric("Analysis Count", metadata["analysis_count"])
    c4.metric("Deterministic", str(metadata["deterministic"]))

    st.caption(
        "Identity Resonance Field built from 21 historical Kamea layers, "
        "visit histories, persistence structure, and residual topology."
    )