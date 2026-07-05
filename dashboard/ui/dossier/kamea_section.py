
"""Kamea Intelligence section for Atlas dossiers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.layout import divider
from dashboard.ui.metrics import metric_grid


def render_kamea_section(profile: dict[str, Any]) -> None:
    """Render Kamea-derived structural intelligence."""

    divider("Kamea Intelligence")

    graph = profile.get("graph", {})
    identity_stack = graph.get("identity_stack", {}) if isinstance(graph, dict) else {}
    cig = graph.get("cig", {}) if isinstance(graph, dict) else {}
    summary = graph.get("summary", {}) if isinstance(graph, dict) else {}

    raw_kamea = extract_raw_kamea_graph(identity_stack, cig)

    kamea_summary = raw_kamea.get("summary", {}) if isinstance(raw_kamea, dict) else {}

    metric_grid(
        {
            "Source": kamea_summary.get("source", "kamea_identity_graph"),
            "Construction Passes": kamea_summary.get("construction_pass_count", 21),
            "Ciphers": kamea_summary.get("cipher_count", 3),
            "Planets": kamea_summary.get("planet_count", 7),
            "Repeated Nodes": kamea_summary.get("repeated_node_count", "unknown"),
            "Max Node Weight": kamea_summary.get("max_node_weight", "unknown"),
        }
    )

    st.markdown(build_kamea_summary(profile, summary, kamea_summary))

    render_cipher_planet_summary(kamea_summary)
    render_construction_passes(raw_kamea)


def extract_raw_kamea_graph(identity_stack: dict[str, Any], cig: dict[str, Any]) -> dict[str, Any]:
    """Extract raw Kamea graph from supported payload shapes."""

    for source in [
        identity_stack.get("input", {}) if isinstance(identity_stack, dict) else {},
        identity_stack.get("graph_input", {}) if isinstance(identity_stack, dict) else {},
        cig,
    ]:
        if not isinstance(source, dict):
            continue

        identity_graph = source.get("identity_graph", {})
        if isinstance(identity_graph, dict):
            raw = identity_graph.get("raw_kamea_graph")
            if isinstance(raw, dict):
                return raw

        raw = source.get("raw_kamea_graph")
        if isinstance(raw, dict):
            return raw

    return {}


def render_cipher_planet_summary(kamea_summary: dict[str, Any]) -> None:
    """Render cipher and planet activity summaries."""

    ciphers = kamea_summary.get("ciphers", {})
    planets = kamea_summary.get("planets", {})

    if ciphers:
        divider("Cipher Activity")
        metric_grid({str(key): value for key, value in ciphers.items()})

    if planets:
        divider("Planetary Kamea Activity")
        metric_grid({str(key).title(): value for key, value in planets.items()})


def render_construction_passes(raw_kamea: dict[str, Any]) -> None:
    """Render compact construction pass details."""

    passes = raw_kamea.get("construction_passes", []) if isinstance(raw_kamea, dict) else []

    if not isinstance(passes, list) or not passes:
        return

    divider("21 Structural Projections")

    for item in passes:
        if not isinstance(item, dict):
            continue

        cipher = item.get("cipher", "unknown")
        planet = item.get("planet", "unknown")

        with st.expander(f"{cipher} / {planet}", expanded=False):
            metric_grid(
                {
                    "Value Count": item.get("value_count", "unknown"),
                    "Path Length": item.get("path_length", "unknown"),
                    "Repeated Nodes": len(item.get("repeated_nodes", {}) or {}),
                    "Repeated Edges": len(item.get("repeated_edges", {}) or {}),
                }
            )

            st.json(
                {
                    "repeated_nodes": item.get("repeated_nodes", {}),
                    "repeated_edges": item.get("repeated_edges", {}),
                }
            )


def build_kamea_summary(
    profile: dict[str, Any],
    graph_summary: dict[str, Any],
    kamea_summary: dict[str, Any],
) -> str:
    """Build Kamea intelligence summary."""

    role = profile.get("role", "Unknown")
    topology = graph_summary.get("topology_class", profile.get("topology_class", "unknown topology"))
    motif = graph_summary.get("dominant_motif", profile.get("dominant_motif", "unknown motif"))

    construction_passes = kamea_summary.get("construction_pass_count", 21)
    repeated_nodes = kamea_summary.get("repeated_node_count", "unknown")
    max_weight = kamea_summary.get("max_node_weight", "unknown")

    return f"""
### Atlas Interpretation

The Kamea engine is the primary structural source for this dossier.

Atlas projects the profile name through three cipher systems across seven classical planetary Kameas, producing **{construction_passes} structural projections**.

These projections are merged into a Kamea-derived identity graph. Repeated node visits are treated as structural depth, giving Atlas a way to measure recurrence, persistence, convergence, and symbolic pressure.

This profile currently resolves as **{role}**, with **{topology}** topology and a **{motif}** dominant motif.

The Kamea overlay reports **{repeated_nodes} repeated nodes** and a maximum node weight of **{max_weight}**, indicating where symbolic values repeatedly converge across cipher and planetary layers.
"""

