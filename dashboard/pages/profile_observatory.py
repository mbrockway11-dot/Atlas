"""Profile Observatory page."""

from __future__ import annotations

import json
import traceback

import pandas as pd
import streamlit as st

from atlas.acf.builder import export_acf_profile
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.overlay import build_composite_overlay
from atlas.research import build_profile_matrix_rows
from atlas.resonance import build_resonance_field
from components.ive_panel import render_ive_panel
from components.observatory.calibration import render_calibration_view
from components.observatory.functional_role_v2 import render_functional_role_v2
from components.observatory.graph_evolution_3d import render_graph_evolution_3d
from components.observatory.header import render_observatory_header


def render_profile_observatory_page() -> None:
    """Render Profile Observatory page."""
    st.header("Profile Observatory")
    st.caption("Inspect one individual from identity -> vector -> graph evolution -> resonance.")

    profiles = list_saved_profiles()

    if not profiles:
        st.info("No saved profiles yet. Build a profile first.")
        return

    selected = st.selectbox("Profile", profiles)
    acf = load_or_repair_acf(selected)

    if acf is None:
        st.error(f"No ACF found for `{selected}`. Rebuild this profile first.")
        return

    safe_section("Header", lambda: render_observatory_header(acf))

    (
        tab_identity_vector,
        tab_fingerprint,
        tab_graph_3d,
        tab_emanations,
        tab_overlay,
        tab_resonance,
        tab_historical,
        tab_calibration,
        tab_research,
    ) = st.tabs(
        [
            "Identity Vector",
            "Identity Fingerprint",
            "Graph Evolution 3D",
            "21 Emanations",
            "Composite Overlay",
            "Resonance Field",
            "Historical Layers",
            "Calibration",
            "Research",
        ]
    )

    with tab_identity_vector:
        safe_section("Identity Vector", lambda: render_ive_panel(acf))

    with tab_fingerprint:
        safe_section("Identity Fingerprint", lambda: render_identity_fingerprint(acf))

    with tab_graph_3d:
        safe_section("Graph Evolution 3D", lambda: render_graph_evolution_3d(acf))

    with tab_emanations:
        safe_section("21 Emanations", lambda: render_emanation_summary(acf))

    with tab_overlay:
        safe_section("Composite Overlay", lambda: render_composite_overlay(acf))

    with tab_resonance:
        safe_section("Resonance Field", lambda: render_resonance_field(acf))

    with tab_historical:
        safe_section("Historical Layers", lambda: render_layer_explorer(acf))

    with tab_calibration:
        safe_section("Calibration", lambda: render_calibration_view(acf))

    with tab_research:
        safe_section("Research Matrix", lambda: render_research_matrix(acf))
        safe_section("Legacy Debug", lambda: render_legacy_debug(acf))


def safe_section(name: str, render_fn) -> None:
    """Render a section and show errors instead of blanking the page."""
    try:
        render_fn()
    except Exception:
        st.error(f"{name} failed.")
        st.code(traceback.format_exc())


def load_or_repair_acf(profile_key: str) -> dict | None:
    """Load ACF and repair older exports if needed."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if not acf_path.exists():
        return None

    data = json.loads(acf_path.read_text(encoding="utf-8"))

    required_keys = {
        "identity",
        "essence",
        "identity_graph",
        "identity_persistence",
        "invariant_analysis",
    }

    if required_keys.issubset(data.keys()):
        return data

    name = data["identity"]["name"]
    entity_type = data["identity"].get("entity_type", "person")

    export_acf_profile(
        name=name,
        output_path=acf_path,
        entity_type=entity_type,
    )

    return json.loads(acf_path.read_text(encoding="utf-8"))


def render_identity_fingerprint(acf: dict) -> None:
    """Render canonical individual fingerprint."""
    st.markdown("## Identity Fingerprint")

    overlay = build_composite_overlay(acf)
    resonance_field = build_resonance_field(overlay)
    resonance_core = build_resonance_core_from_field(resonance_field)

    identity = acf["identity"]

    st.markdown(f"### {identity['name']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historical Layers", acf["identity_graph"]["layer_count"])
    c2.metric("Composite Nodes", overlay["summary"]["composite_node_count"])
    c3.metric("Core Nodes", resonance_core["node_count"])
    c4.metric("Core Edges", resonance_core["edge_count"])

    st.divider()

    render_functional_role_v2(acf)

    st.divider()

    st.markdown("### Resonance Core Summary")

    summary = resonance_field["summary"]

    c13, c14, c15 = st.columns(3)
    c13.metric(
        "Core",
        f"{summary['core_node_count']} nodes / {summary['core_edge_count']} edges",
    )
    c14.metric(
        "Adaptive",
        f"{summary['adaptive_node_count']} nodes / {summary['adaptive_edge_count']} edges",
    )
    c15.metric(
        "Peripheral",
        f"{summary['peripheral_node_count']} nodes / {summary['peripheral_edge_count']} edges",
    )

    st.markdown("### Top Core Nodes")
    st.dataframe(
        clean_display_dataframe(pd.DataFrame(resonance_core["summary"]["top_nodes"])),
        width="stretch",
    )

    st.markdown("### Top Core Edges")
    st.dataframe(
        clean_display_dataframe(pd.DataFrame(resonance_core["summary"]["top_edges"])),
        width="stretch",
    )

    render_legacy_classification_expander(acf)


def render_emanation_summary(acf: dict) -> None:
    """Render 21 emanations summary."""
    st.markdown("## 21 Emanations")

    rows = build_profile_matrix_rows(acf)
    dataframe = pd.DataFrame(rows)

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(dataframe))
    c2.metric("Ciphers", dataframe["cipher"].nunique())
    c3.metric("Planets", dataframe["planet"].nunique())

    grouped = dataframe.groupby(["cipher", "planet"]).agg(
        {
            "unique_nodes": "mean",
            "unique_edges": "mean",
            "node_coverage": "mean",
            "density": "mean",
            "entropy": "mean",
            "max_depth": "mean",
            "self_loops": "mean",
            "graph_coherence": "mean",
            "core_survival_score": "mean",
            "attractor_stability": "mean",
        }
    ).reset_index()

    st.dataframe(grouped, width="stretch")

    with st.expander("Full 21-layer matrix"):
        st.dataframe(dataframe, width="stretch")


def render_composite_overlay(acf: dict) -> None:
    """Render composite overlay."""
    st.markdown("## Composite Overlay")

    overlay = build_composite_overlay(acf)
    summary = overlay["summary"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Composite Nodes", summary["composite_node_count"])
    c2.metric("Composite Edges", summary["composite_edge_count"])
    c3.metric("Triple-Cipher Nodes", summary["triple_cipher_node_count"])
    c4.metric("Triple-Cipher Edges", summary["triple_cipher_edge_count"])

    c5, c6 = st.columns(2)
    c5.metric("Multi-Planet Nodes", summary["multi_planet_node_count"])
    c6.metric("Multi-Planet Edges", summary["multi_planet_edge_count"])

    st.markdown("### Top Resonant Nodes")
    st.dataframe(
        clean_display_dataframe(pd.DataFrame(summary["top_resonant_nodes"])),
        width="stretch",
    )

    st.markdown("### Top Resonant Edges")
    st.dataframe(
        clean_display_dataframe(pd.DataFrame(summary["top_resonant_edges"])),
        width="stretch",
    )

    with st.expander("Raw Composite Overlay"):
        st.json(overlay)


def render_resonance_field(acf: dict) -> None:
    """Render resonance field."""
    st.markdown("## Resonance Field")

    overlay = build_composite_overlay(acf)
    resonance_field = build_resonance_field(overlay)
    summary = resonance_field["summary"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Core Nodes", summary["core_node_count"])
    c2.metric("Adaptive Nodes", summary["adaptive_node_count"])
    c3.metric("Peripheral Nodes", summary["peripheral_node_count"])

    c4, c5, c6 = st.columns(3)
    c4.metric("Core Edges", summary["core_edge_count"])
    c5.metric("Adaptive Edges", summary["adaptive_edge_count"])
    c6.metric("Peripheral Edges", summary["peripheral_edge_count"])

    st.markdown("### Top Resonant Nodes")
    st.dataframe(
        clean_display_dataframe(pd.DataFrame(summary["top_resonant_nodes"])),
        width="stretch",
    )

    st.markdown("### Top Resonant Edges")
    st.dataframe(
        clean_display_dataframe(pd.DataFrame(summary["top_resonant_edges"])),
        width="stretch",
    )

    with st.expander("Core Nodes"):
        st.dataframe(
            clean_display_dataframe(pd.DataFrame(resonance_field["core"]["nodes"])),
            width="stretch",
        )

    with st.expander("Adaptive Nodes"):
        st.dataframe(
            clean_display_dataframe(pd.DataFrame(resonance_field["adaptive"]["nodes"])),
            width="stretch",
        )

    with st.expander("Peripheral Nodes"):
        st.dataframe(
            clean_display_dataframe(pd.DataFrame(resonance_field["peripheral"]["nodes"])),
            width="stretch",
        )


def render_layer_explorer(acf: dict) -> None:
    """Render 21-layer explorer."""
    st.markdown("## Historical Layer Explorer")

    layers = acf["identity_graph"]["layers"]
    layer_options = [layer["layer_id"] for layer in layers]

    selected_layer_id = st.selectbox("Layer", layer_options)
    layer = next(item for item in layers if item["layer_id"] == selected_layer_id)

    path_views = layer["features"]["path_views"]
    visit_history = path_views["analysis_path"]["visit_history"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Cipher", layer["cipher"])
    c2.metric("Planet", layer["planet"])
    c3.metric("Grid Size", layer["grid_size"])
    c4.metric("Max Depth", visit_history["max_depth"])

    st.markdown("### Analysis Path")
    st.write(path_views["analysis_path"]["wrapped_values"])

    st.markdown("### Visual Path")
    st.write(path_views["render_path"]["wrapped_values"])

    st.markdown("### Node Weights")
    st.dataframe(
        dict_table(path_views["analysis_path"]["node_weights"], "node", "weight"),
        width="stretch",
    )

    st.markdown("### Edge Weights")
    st.dataframe(
        dict_table(path_views["analysis_path"]["edge_weights"], "edge", "weight"),
        width="stretch",
    )

    st.markdown("### Visit History")
    st.dataframe(pd.DataFrame(visit_history["visits"]), width="stretch")

    with st.expander("Raw Layer JSON"):
        st.json(layer)


def render_research_matrix(acf: dict) -> None:
    """Render research matrix rows from current ACF."""
    st.markdown("## Current Profile Research Matrix")

    rows = build_profile_matrix_rows(acf)
    dataframe = pd.DataFrame(rows)

    st.dataframe(dataframe, width="stretch")

    csv = dataframe.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download current_profile_matrix.csv",
        data=csv,
        file_name="current_profile_matrix.csv",
        mime="text/csv",
    )


def render_legacy_debug(acf: dict) -> None:
    """Render legacy debug data only in collapsed form."""
    with st.expander("Legacy Debug: invariant_analysis planetary_contrast"):
        contrast = acf["invariant_analysis"]["planetary_contrast"]
        st.warning(
            "Legacy planetary contrast still uses old scoring. Keep this for debugging only."
        )
        st.json(contrast)


def render_legacy_classification_expander(acf: dict) -> None:
    """Render legacy classification only as collapsed diagnostic."""
    with st.expander("Legacy Classification Diagnostics"):
        st.warning(
            "This is Atlas v1 legacy classification from acf['essence']['classification']. "
            "Atlas v2 Functional Role above is the primary classification."
        )

        classification = acf.get("essence", {}).get("classification", {})
        function = classification.get("function", {})

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Legacy Role", function.get("role", "unknown"))
        c2.metric("Legacy Subtype", function.get("subtype", "legacy"))
        c3.metric("Legacy Confidence", str(function.get("confidence", "legacy")))
        c4.metric("Legacy Hybrid", str(function.get("is_hybrid", False)))

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Legacy Driver", format_float(function.get("driver")))
        c6.metric("Legacy Amplifier", format_float(function.get("amplifier")))
        c7.metric("Legacy Regulator", format_float(function.get("regulator")))
        c8.metric("Legacy Margin", format_float(function.get("margin")))

        st.write(function.get("reason", "No legacy classification reason supplied."))

        with st.expander("Raw Legacy Classification JSON"):
            st.json(classification)


def build_resonance_core_from_field(resonance_field: dict) -> dict:
    """Build resonance core from resonance field."""
    core_nodes = sorted(
        resonance_field["core"]["nodes"],
        key=lambda node: node["resonance_index"],
        reverse=True,
    )

    core_edges = sorted(
        resonance_field["core"]["edges"],
        key=lambda edge: edge["resonance_index"],
        reverse=True,
    )

    return {
        "node_count": len(core_nodes),
        "edge_count": len(core_edges),
        "nodes": core_nodes,
        "edges": core_edges,
        "summary": {
            "top_nodes": core_nodes[:10],
            "top_edges": core_edges[:10],
        },
    }


def clean_display_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert list/dict/object cells into display-safe strings."""
    if dataframe.empty:
        return dataframe

    output = dataframe.copy()

    for column in output.columns:
        output[column] = output[column].map(clean_display_value)

    return output


def clean_display_value(value):
    """Convert nested values into readable strings for Streamlit tables."""
    if isinstance(value, list):
        if not value:
            return ""

        if all(isinstance(item, str) for item in value):
            return ", ".join(value)

        if all(isinstance(item, dict) for item in value):
            return "; ".join(
                json.dumps(item, ensure_ascii=False, sort_keys=True)
                for item in value
            )

        return ", ".join(str(item) for item in value)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    return value


def dict_table(data: dict, key_name: str, value_name: str) -> pd.DataFrame:
    """Convert dictionary to dataframe."""
    return pd.DataFrame(
        [
            {
                key_name: key,
                value_name: value,
            }
            for key, value in data.items()
        ]
    )


def format_float(value) -> str:
    """Format numeric value safely."""
    if value is None:
        return "n/a"

    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)