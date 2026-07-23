"""Historical Event–Relationship Transit Validation research dashboard."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from atlas.services.historical_validation_service import build_historical_validation_dashboard_payload


def render_historical_transit_validation_page() -> None:
    st.title("Historical Event–Relationship Transit Validation")
    st.caption("Research and falsification only. Astronomical geometry is not evidence that transits cause historical outcomes.")
    initial = build_historical_validation_dashboard_payload()
    if not initial.get("success"):
        st.warning("Run scripts/run_historical_event_relationship_validation.py first.")
        st.json(initial)
        return
    options = initial.get("event_options", [])
    labels = {f"{row['start_date']} — {row['name']}": row["event_id"] for row in options}
    selected_label = st.selectbox("Historical event", list(labels))
    selected_date = st.date_input("Relationship network date", value=date.fromisoformat(next(row["start_date"] for row in options if row["event_id"] == labels[selected_label])))
    payload = build_historical_validation_dashboard_payload(event_id=labels[selected_label], selected_date=selected_date.isoformat())
    metrics = payload.get("metrics", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profiles", metrics.get("profiles", 0))
    c2.metric("Events", metrics.get("events", 0))
    c3.metric("Relationships", metrics.get("relationships", 0))
    c4.metric("Retained Findings", metrics.get("retained_findings", 0))
    for warning in payload.get("warnings", []):
        st.warning(warning)

    astronomical, historical, statistical, symbolic, quality, sources, downloads = st.tabs([
        "Astronomical", "Historical", "Statistical", "Symbolic Ontology", "Quality", "Sources", "Downloads"
    ])
    data = payload["data"]
    with astronomical:
        st.info(payload["labels"]["astronomical"])
        exposures = pd.DataFrame(data.get("exposures", []))
        if exposures.empty:
            st.info("No in-orb exposures for the selected event.")
        else:
            columns = [column for column in ["profile_key", "transit_planet", "natal_target", "aspect", "minimum_orb", "closest_date", "applying_separating", "retrograde_at_anchor", "duration_days_in_orb", "repeated_hit_count", "contact_stable_across_birth_time_range", "fast_moon_uncertainty"] if column in exposures]
            st.dataframe(exposures[columns].sort_values(["profile_key", "minimum_orb"]), use_container_width=True, hide_index=True)
            timeline = exposures.groupby(["closest_date", "profile_key"], as_index=False).size()
            st.plotly_chart(px.line(timeline, x="closest_date", y="size", color="profile_key", markers=True, title="Transit exposure timeline"), use_container_width=True)
        st.subheader("Relationship-level simultaneous exposures")
        st.dataframe(pd.DataFrame(data.get("relationship_exposures", [])), use_container_width=True, hide_index=True)
    with historical:
        st.info(payload["labels"]["historical"])
        st.json(payload.get("selected_event", {}))
        st.subheader("Documented participation and outcomes")
        st.dataframe(pd.DataFrame(data.get("participations", [])), use_container_width=True, hide_index=True)
        st.subheader(f"Relationships active on {payload.get('selected_date')}")
        st.dataframe(pd.DataFrame(data.get("active_relationships", [])), use_container_width=True, hide_index=True)
        st.subheader("Event and matched control windows")
        st.dataframe(pd.DataFrame(data.get("windows", [])), use_container_width=True, hide_index=True)
    with statistical:
        st.info(payload["labels"]["statistical"])
        results = pd.DataFrame(data.get("validation", []))
        st.dataframe(results, use_container_width=True, hide_index=True)
        if not results.empty:
            chart = results[["hypothesis_id", "effect_size_rate_difference"]].copy()
            st.plotly_chart(px.bar(chart, x="hypothesis_id", y="effect_size_rate_difference", title="Matched event-minus-control effect sizes"), use_container_width=True)
        permutations = pd.DataFrame(data.get("permutations", []))
        if not permutations.empty:
            st.plotly_chart(px.histogram(permutations, x="permuted_effect_size", color="hypothesis_id", barmode="overlay", title="Permutation distributions"), use_container_width=True)
        st.error("No famous example or uncorrected p-value is treated as validation. Rejected and underpowered hypotheses remain visible.")
    with symbolic:
        st.info(payload["labels"]["symbolic"])
        ontology = data.get("ontology", {})
        st.markdown(f"**Ontology:** `{ontology.get('ontology_id', 'unavailable')}`")
        st.caption(ontology.get("description", ""))
        st.subheader("Preregistered hypothesis interpretations")
        for hypothesis in data.get("hypotheses", []):
            interpretation = hypothesis.get("symbolic_interpretation", {})
            with st.expander(hypothesis.get("hypothesis_id", "Hypothesis")):
                st.write(interpretation.get("symbolic_statement", "No interpretation available."))
                st.json({
                    "ontology_refs": interpretation.get("ontology_refs", []),
                    "source_refs": interpretation.get("source_refs", []),
                    "eligible_outcome_categories": interpretation.get("eligible_outcome_categories", []),
                    "empirical_evidence": interpretation.get("empirical_evidence", False),
                    "causal_claim": interpretation.get("causal_claim", False),
                })
        st.subheader("Distinct measured interpretations")
        st.dataframe(pd.DataFrame(data.get("interpretations", [])), use_container_width=True, hide_index=True)
        st.warning("Symbolic meanings define hypotheses to test. They are not counted as historical facts or statistical evidence.")
    with quality:
        st.json(data.get("quality", {}))
        st.dataframe(pd.DataFrame(data.get("missing_data", [])), use_container_width=True, hide_index=True)
    with sources:
        st.info("Historical claims must resolve to these source IDs.")
        for source in data.get("sources", []):
            st.markdown(f"- [{source.get('title')}]({source.get('url')}) — {source.get('publisher')} (`{source.get('source_id')}`)")
    with downloads:
        for item in payload.get("downloads", []):
            path = Path(item["path"])
            st.download_button(item["name"], data=path.read_bytes(), file_name=path.name, key=f"historical_download_{path.name}")


def render() -> None:
    render_historical_transit_validation_page()
