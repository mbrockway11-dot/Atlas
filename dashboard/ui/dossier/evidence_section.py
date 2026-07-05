
"""Evidence section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_evidence_section(profile: dict[str, Any]) -> None:
    """Render evidence records."""

    divider("Evidence")

    evidence = profile.get("evidence", [])

    if not isinstance(evidence, list):
        evidence = []

    semantic = profile.get("semantic", {})
    synthesis = profile.get("structural_synthesis", {})

    semantic_evidence = semantic.get("evidence", []) if isinstance(semantic, dict) else []
    synthesis_evidence = synthesis.get("evidence", []) if isinstance(synthesis, dict) else []

    all_evidence = []
    all_evidence.extend(evidence)
    if isinstance(semantic_evidence, list):
        all_evidence.extend(semantic_evidence)
    if isinstance(synthesis_evidence, list):
        all_evidence.extend(synthesis_evidence)

    metric_grid(
        {
            "Direct Evidence": len(evidence),
            "Semantic Evidence": len(semantic_evidence) if isinstance(semantic_evidence, list) else 0,
            "Synthesis Evidence": len(synthesis_evidence) if isinstance(synthesis_evidence, list) else 0,
            "Total Records": len(all_evidence),
        }
    )

    st.markdown(build_evidence_summary(all_evidence))

    if not all_evidence:
        st.info("No evidence records are available for this dossier.")
        return

    for index, item in enumerate(all_evidence, start=1):
        render_evidence_record(index, item)


def render_evidence_record(index: int, item: Any) -> None:
    """Render one evidence record."""

    if not isinstance(item, dict):
        with st.expander(f"Evidence {index}", expanded=False):
            st.write(item)
        return

    source = item.get("source", "unknown source")
    claim = item.get("claim", "No claim provided.")
    basis = item.get("basis", {})

    with st.expander(f"{index}. {source}", expanded=False):
        st.markdown("#### Claim")
        st.markdown(str(claim))

        if basis:
            st.markdown("#### Basis")
            st.json(basis)


def build_evidence_summary(evidence: list[Any]) -> str:
    """Build readable evidence summary."""

    return f"""
Atlas evidence records preserve the reasoning basis behind the dossier.

Evidence does not function as proof of a personality claim. It records which deterministic layers supported a synthesis statement: classification, graph summary, topology, resonance, fingerprint, semantic domains, temporal context, and direct service outputs.

This dossier currently exposes **{len(evidence)} evidence record(s)**.
"""

