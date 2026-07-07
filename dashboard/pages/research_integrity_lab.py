
"""Research Integrity Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.integrity_service import (
    build_research_integrity_payload,
    list_integrity_profiles,
)


def render_research_integrity_lab_page() -> None:
    """Render Research Integrity Lab."""
    st.header("Research Integrity Lab")
    st.caption("Audit Scientific Confidence, Provenance, Timeline, Director health, checkpoints, and exports.")

    profiles = list_integrity_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        limit = st.slider("Profile limit", 20, min(300, len(profiles)), min(50, len(profiles)))

    with c2:
        max_schedule_items = st.slider("Scheduled questions", 1, 10, 2)

    with c3:
        force = st.toggle("Force recompile", value=False)

    holdout_ratio = st.slider("Prediction holdout ratio", 0.05, 0.50, 0.20, 0.05)

    goal = st.text_input("Integrity audit goal", value="research_integrity_audit")
    export = st.toggle("Export integrity package", value=True)

    selected_profiles = st.multiselect(
        "Optional profile subset",
        profiles,
        default=[],
    )

    use_profiles = selected_profiles or None
    effective_limit = None if selected_profiles else limit

    if not st.button("Run Research Integrity Audit", type="primary"):
        st.info("Run an integrity audit across Director health, confidence, provenance, timeline, and exports.")
        return

    with st.spinner("Running Research Integrity Audit..."):
        payload = build_research_integrity_payload(
            use_profiles,
            limit=effective_limit,
            force=force,
            goal=goal,
            max_schedule_items=max_schedule_items,
            holdout_ratio=holdout_ratio,
            export=export,
        )

    if not payload.get("success"):
        st.error("Research Integrity audit failed.")
        st.json(payload)
        return

    render_integrity_summary(payload)
    render_director_health(payload)
    render_confidence(payload)
    render_provenance(payload)
    render_timeline(payload)
    render_checkpoints(payload)
    render_export(payload)
    render_raw(payload)


def render_integrity_summary(payload: dict) -> None:
    """Render integrity summary."""
    st.markdown("## Integrity Summary")
    st.info(payload.get("summary", ""))

    c1, c2, c3, c4 = st.columns(4)

    health = payload.get("health", {}) or {}
    confidence = payload.get("scientific_confidence", {}) or {}
    provenance = payload.get("provenance", {}) or {}
    timeline = payload.get("timeline", {}) or {}

    c1.metric("Records", payload.get("record_count", 0))
    c2.metric("Health", "healthy" if health.get("healthy") else "warnings")
    c3.metric("Confidence", format_number(confidence.get("scientific_confidence")))
    c4.metric("Timeline Events", (timeline.get("summary", {}) or {}).get("event_count", 0))

    graph_summary = ((provenance.get("graph", {}) or {}).get("summary", {}) or {})
    c5, c6, c7 = st.columns(3)
    c5.metric("Provenance Nodes", graph_summary.get("node_count", 0))
    c6.metric("Provenance Edges", graph_summary.get("edge_count", 0))
    c7.metric("Confidence Label", confidence.get("confidence_label", "n/a"))


def render_director_health(payload: dict) -> None:
    """Render Director health."""
    st.markdown("## Director Health")

    health = payload.get("health", {}) or {}
    director = payload.get("director", {}) or {}
    state = director.get("state", {}) or {}

    c1, c2, c3 = st.columns(3)
    c1.metric("State", state.get("state", "n/a"))
    c2.metric("Healthy", str(bool(health.get("healthy"))))
    c3.metric("Warnings", health.get("warning_count", 0))

    if health.get("warnings"):
        st.warning("\\n".join(health.get("warnings", [])))

    with st.expander("Director State History", expanded=False):
        st.json(state.get("history", []))


def render_confidence(payload: dict) -> None:
    """Render Scientific Confidence."""
    st.markdown("## Scientific Confidence")

    confidence = payload.get("scientific_confidence", {}) or {}

    if not confidence:
        st.info("No confidence report available.")
        return

    st.info(confidence.get("summary", ""))

    components = confidence.get("components", {}) or {}
    inputs = confidence.get("inputs", {}) or {}

    tabs = st.tabs(["Components", "Inputs"])

    with tabs[0]:
        if components:
            st.dataframe(
                pd.DataFrame([{"component": key, "score": value} for key, value in components.items()]),
                width="stretch",
            )
        else:
            st.info("No confidence components.")

    with tabs[1]:
        if inputs:
            st.dataframe(
                pd.DataFrame([{"input": key, "value": value} for key, value in inputs.items()]),
                width="stretch",
            )
        else:
            st.info("No confidence inputs.")


def render_provenance(payload: dict) -> None:
    """Render Provenance."""
    st.markdown("## Research Provenance")

    provenance = payload.get("provenance", {}) or {}

    if not provenance:
        st.info("No provenance report available.")
        return

    st.info(provenance.get("summary", ""))

    graph = provenance.get("graph", {}) or {}
    graph_summary = graph.get("summary", {}) or {}

    st.markdown("### Object Types")
    object_types = graph_summary.get("object_types", {}) or {}

    if object_types:
        st.dataframe(
            pd.DataFrame([{"object_type": key, "count": value} for key, value in object_types.items()]),
            width="stretch",
        )

    tabs = st.tabs(["Nodes", "Edges", "Registry", "Lineage"])

    with tabs[0]:
        nodes = graph.get("nodes", []) or []
        st.dataframe(pd.DataFrame(nodes), width="stretch") if nodes else st.info("No nodes.")

    with tabs[1]:
        edges = graph.get("edges", []) or []
        st.dataframe(pd.DataFrame(edges), width="stretch") if edges else st.info("No edges.")

    with tabs[2]:
        registry = provenance.get("registry", {}) or {}
        objects = registry.get("objects", {}) or {}
        rows = [
            {
                "id": key,
                "type": value.get("type"),
                "label": value.get("label"),
                "created_at": value.get("created_at"),
            }
            for key, value in objects.items()
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch") if rows else st.info("No registry objects.")

    with tabs[3]:
        lineage = provenance.get("lineage", {}) or {}
        relations = lineage.get("relations", []) or []
        st.dataframe(pd.DataFrame(relations), width="stretch") if relations else st.info("No lineage relations.")


def render_timeline(payload: dict) -> None:
    """Render Timeline."""
    st.markdown("## Research Timeline")

    timeline = payload.get("timeline", {}) or {}

    if not timeline:
        st.info("No timeline report available.")
        return

    st.info(timeline.get("text_summary", ""))

    summary = timeline.get("summary", {}) or {}
    counts = summary.get("event_type_counts", {}) or {}

    if counts:
        st.markdown("### Event Types")
        st.dataframe(
            pd.DataFrame([{"event_type": key, "count": value} for key, value in counts.items()]),
            width="stretch",
        )

    events = timeline.get("events", []) or []

    rows = [
        {
            "timestamp": event.get("timestamp"),
            "event_type": event.get("event_type"),
            "title": event.get("title"),
            "source_id": event.get("source_id"),
            "summary": event.get("summary"),
        }
        for event in events
    ]

    st.markdown("### Events")
    st.dataframe(pd.DataFrame(rows), width="stretch") if rows else st.info("No timeline events.")

    if events:
        selected_event_id = st.selectbox(
            "Inspect timeline event",
            [event.get("event_id") for event in events],
        )
        selected = next((event for event in events if event.get("event_id") == selected_event_id), None)
        if selected:
            with st.expander("Selected Timeline Event", expanded=False):
                st.json(selected)


def render_checkpoints(payload: dict) -> None:
    """Render checkpoints."""
    st.markdown("## Director Checkpoints")

    checkpoints = payload.get("checkpoints", {}) or {}
    rows = checkpoints.get("checkpoints", []) or []

    c1, c2 = st.columns(2)
    c1.metric("Checkpoint Count", checkpoints.get("checkpoint_count", 0))
    c2.metric("Failed Count", checkpoints.get("failed_count", 0))

    st.dataframe(pd.DataFrame(rows), width="stretch") if rows else st.info("No checkpoints.")


def render_export(payload: dict) -> None:
    """Render export report."""
    st.markdown("## Export Package")

    export = payload.get("export")

    if not export:
        st.info("Export disabled or unavailable.")
        return

    st.info(export.get("summary", ""))

    files = ((export.get("export", {}) or {}).get("files", {}) or {})

    if files:
        st.dataframe(
            pd.DataFrame([{"artifact": key, "path": value} for key, value in files.items()]),
            width="stretch",
        )
    else:
        st.info("No export files.")


def render_raw(payload: dict) -> None:
    """Render raw payload."""
    with st.expander("Raw Integrity Payload", expanded=False):
        st.json(payload)


def format_number(value) -> str:
    """Format numeric values."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "n/a"
