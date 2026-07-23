"""Kamea Consciousness Flow dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from atlas.services.kamea_consciousness_flow_service import (
    build_kamea_consciousness_flow_payload,
    list_kamea_flow_profiles,
    render_riverbed_for_profile,
    render_unified_shape_for_profile,
)
from atlas.services.temporal_intelligence_service import (
    build_temporal_intelligence_payload,
)


def render_kamea_consciousness_flow_page() -> None:
    st.title("Kamea Consciousness Flow")
    st.caption("Identity as ordered current through seven planetary filters. Deterministic symbolic structure—not empirical consciousness measurement.")
    profiles = list_kamea_flow_profiles()
    if not profiles:
        st.warning("No canonical profile payloads are available.")
        return
    default_a = profiles.index("nikola_tesla") if "nikola_tesla" in profiles else 0
    default_b = profiles.index("thomas_edison") if "thomas_edison" in profiles else min(1, len(profiles) - 1)
    left, right = st.columns(2)
    profile_a = left.selectbox("First profile", profiles, index=default_a)
    profile_b = right.selectbox("Second profile", profiles, index=default_b)
    payload = build_kamea_consciousness_flow_payload(profile_a, profile_b)
    if not payload.get("success"):
        st.error("Kamea Flow could not be built.")
        st.json(payload)
        return
    for warning in payload.get("warnings", []):
        st.warning(warning)
    report_a = payload["reports"]["profile_a"]
    report_b = payload["reports"]["profile_b"]
    confluence = payload.get("confluence", {}) or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{profile_a}: tributaries", report_a["tributaries"]["tributary_count"])
    c2.metric(f"{profile_b}: tributaries", report_b["tributaries"]["tributary_count"])
    c3.metric("Shared riverbed nodes", confluence.get("summary", {}).get("shared_invariant_node_count", 0))
    c4.metric("Shared channels", confluence.get("summary", {}).get("shared_invariant_edge_count", 0))
    tab_a, tab_b, tab_pair, tab_method = st.tabs([profile_a, profile_b, "Confluence", "Method"])
    with tab_a:
        _render_profile(report_a, profile_a)
    with tab_b:
        _render_profile(report_b, profile_b)
    with tab_pair:
        rows = pd.DataFrame(confluence.get("planetary_confluences", []))
        columns = [column for column in ["planet", "shared_node_count", "shared_edge_count", "opposing_current_count", "node_jaccard", "edge_jaccard"] if column in rows]
        st.dataframe(rows[columns] if columns else rows, use_container_width=True, hide_index=True)
        st.json(confluence.get("summary", {}))
        shape_rows = pd.DataFrame(confluence.get("shape_confluence", {}).get("planetary_shape_comparisons", []))
        st.subheader("Normalized geometric confluence")
        st.dataframe(shape_rows, use_container_width=True, hide_index=True)
        _render_dynamics_experiment(profile_a, profile_b)
    with tab_method:
        st.json(report_a.get("interpretive_model", {}))
        st.markdown("Each cipher–planet construction is an independent tributary. Same-planet nodes and directed channels reproduced across at least two cipher streams form the invariant riverbed. Cross-profile confluence compares those riverbeds without treating matching numbers from different planetary squares as equivalent.")


def _render_profile(report: dict, profile_key: str) -> None:
    summary = report["riverbed"]["summary"]
    flow_metrics = report["metrics"]["metrics"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Flow steps", report["flow"]["step_count"])
    c2.metric("Invariant nodes", summary["invariant_node_count"])
    c3.metric("Invariant channels", summary["invariant_edge_count"])
    c4.metric("Recurrence", flow_metrics["recurrence_ratio"])
    rows = report["riverbed"]["planetary_riverbeds"]
    st.dataframe(pd.DataFrame(rows)[["planet", "stream_count", "invariant_node_count", "invariant_edge_count", "node_consensus_ratio", "edge_consensus_ratio"]], use_container_width=True, hide_index=True)
    st.subheader("Unified normalized shape")
    st.image(render_unified_shape_for_profile(report, profile_key).encode("utf-8"), use_container_width=True)
    st.caption("All seven Kamea sizes share one coordinate field. Colors identify planetary filters; line patterns identify ciphers. Circle=start, bar=end.")
    _render_star_layers(profile_key)
    planet = st.selectbox("Planetary filter", [row["planet"] for row in rows], key=f"planet-{id(report)}")
    svg = render_riverbed_for_profile(report, planet)
    if svg:
        st.image(svg.encode("utf-8"), use_container_width=True)


def _render_star_layers(profile_key: str) -> None:
    """Render corrected sidereal and separate IAU constellation placements."""
    temporal = build_temporal_intelligence_payload(profile_key)
    if not temporal.get("success"):
        st.warning("Temporal chart layers are unavailable for this profile.")
        return

    data = temporal.get("data", {})
    sidereal = data.get("sidereal", {})
    constellations = data.get("astronomical_constellations", {})
    sidereal_planets = sidereal.get("planets", {})
    constellation_planets = constellations.get("planets", {})

    st.subheader("Lahiri sidereal chart")
    st.caption(
        "The Vedic layer remains a 12-sign Lahiri zodiac. It is not mixed with "
        "the unequal astronomical constellation layer below."
    )
    sidereal_rows = [
        {
            "planet": planet,
            "sign": row.get("sign", ""),
            "degree_in_sign": row.get("degree_in_sign"),
            "sidereal_longitude": row.get("longitude"),
            "retrograde": row.get("retrograde", False),
        }
        for planet, row in sidereal_planets.items()
    ]
    st.dataframe(pd.DataFrame(sidereal_rows), use_container_width=True, hide_index=True)

    st.subheader("IAU astronomical constellations (includes Ophiuchus)")
    st.caption(
        "Actual sky position includes planetary latitude. Ecliptic projection "
        "shows which of the 13 unequal Sun-path constellations lies at that longitude."
    )
    constellation_rows = [
        {
            "planet": planet,
            "actual_sky": row.get("actual_constellation", ""),
            "ecliptic_projection": row.get("ecliptic_path_constellation", ""),
            "ophiuchus": bool(row.get("is_ophiuchus")),
        }
        for planet, row in constellation_planets.items()
    ]
    st.dataframe(
        pd.DataFrame(constellation_rows),
        use_container_width=True,
        hide_index=True,
    )

    metrics = temporal.get("metrics", {})
    if metrics.get("house_count", 0) == 0:
        st.warning(
            "Houses and angles are disabled because the historical birth time/location "
            "is not sufficiently resolved. Moon timing should be treated as sensitive."
        )


def _render_dynamics_experiment(profile_a: str, profile_b: str) -> None:
    """Render any saved bounded dynamics experiment for this pair."""
    root = Path(__file__).resolve().parents[2]
    output_dir = root / "output" / "kamea_star_behavior"
    candidates = [
        output_dir / f"{profile_a}__{profile_b}.json",
        output_dir / f"{profile_b}__{profile_a}.json",
    ]
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    experiment = payload.get("dynamics_experiment", {})
    st.subheader("Registered symbolic-dynamics experiments")
    st.caption(
        "These are falsifiable, research-only hypotheses. None is a retained or causal finding."
    )
    rows = [
        {
            "hypothesis": item.get("hypothesis_id", ""),
            "status": item.get("status", ""),
            "statement": item.get("statement", ""),
            "falsification_test": item.get("falsification_test", ""),
        }
        for item in experiment.get("hypotheses", [])
    ]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.metric("Retained findings", experiment.get("retained_findings", 0))
