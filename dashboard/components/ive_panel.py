"""Identity Vector Engine dashboard panel."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.compiled.calibration import (
    load_calibration_vectors_from_artifacts,
)
from atlas.ive import (
    build_identity_vector,
    build_planet_relationship_matrix,
    identity_vector_to_dict,
    relationship_matrix_to_dict,
)


NORMALIZATION_MODES = [
    "raw",
    "percentile",
    "minmax",
    "zscore",
]


def render_ive_panel(acf: dict) -> None:
    """Render Identity Vector Engine summary."""
    st.markdown("## Identity Vector Engine")

    normalization_mode = st.selectbox(
        "Normalization Mode",
        NORMALIZATION_MODES,
        index=0,
        help=(
            "Raw mode uses the profile's direct bounded measurements. "
            "Percentile, minmax, and zscore use saved profiles as calibration corpus."
        ),
    )

    use_library_calibration = normalization_mode != "raw"

    calibration_vectors = (
        load_calibration_vectors()
        if use_library_calibration
        else None
    )

    if normalization_mode == "raw":
        st.info(
            "Raw mode is best for inspecting one profile directly. "
            "It does not compare the profile against a population."
        )
    else:
        calibration_count = calibration_profile_count(calibration_vectors)

        if calibration_count < 2:
            st.warning(
                f"{normalization_mode} mode needs more saved profiles for useful calibration. "
                f"Current calibration profiles: {calibration_count}. "
                "Build at least 3-5 profiles for meaningful results."
            )
        else:
            st.success(
                f"Using {calibration_count} saved profiles as calibration corpus "
                f"with `{normalization_mode}` normalization."
            )

    identity_vector = build_identity_vector(
        acf,
        normalization_mode=normalization_mode,
        calibration_vectors=calibration_vectors,
    )
    relationship_matrix = build_planet_relationship_matrix(identity_vector)

    render_global_summary(identity_vector)
    render_planet_vectors(identity_vector)
    render_relationship_matrix(relationship_matrix)
    render_quality(identity_vector)

    with st.expander("Raw Identity Vector JSON"):
        st.json(identity_vector_to_dict(identity_vector))

    with st.expander("Raw Relationship Matrix JSON"):
        st.json(relationship_matrix_to_dict(relationship_matrix))


@st.cache_data(show_spinner="Loading compiled calibration corpus...")
def load_calibration_vectors() -> list:
    """Load the calibration corpus from compiled artifacts.

    Reads the compiled runtime layer rather than reparsing every saved ACF,
    which is the difference between a few megabytes and several gigabytes
    per dashboard render.
    """
    return load_calibration_vectors_from_artifacts()


def calibration_profile_count(calibration_vectors: list | None) -> int:
    """Return how many distinct profiles a calibration corpus covers."""
    if not calibration_vectors:
        return 0

    return len({vector.name for vector in calibration_vectors})


def render_global_summary(identity_vector) -> None:
    """Render global IdentityVector metrics."""
    st.markdown("### Global Identity Metrics")

    features = identity_vector.global_features
    quality = identity_vector.quality
    diagnostics = identity_vector.diagnostics

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Balance", format_float(features["planet_balance_index"]))
    c2.metric("Complexity", format_float(features["structural_complexity_index"]))
    c3.metric("Stability", format_float(features["structural_stability_index"]))
    c4.metric("Completeness", format_float(quality["completeness"]))

    c5, c6, c7 = st.columns(3)

    c5.metric("Dominant Coherence", diagnostics["dominant_coherence_planet"])
    c6.metric("Dominant Stability", diagnostics["dominant_stability_planet"])
    c7.metric("Dominant Entropy", diagnostics["dominant_entropy_planet"])

    dataframe = pd.DataFrame(
        [
            {
                "metric": key,
                "value": value,
            }
            for key, value in features.items()
        ]
    )

    st.dataframe(dataframe, width="stretch")


def render_planet_vectors(identity_vector) -> None:
    """Render seven composite planet vectors."""
    st.markdown("### Composite Planet Vectors")

    rows = []

    for planet, vector in identity_vector.planets.items():
        row = {
            "planet": planet,
            "source_count": vector.source_count,
            "source_ciphers": ", ".join(vector.source_ciphers),
        }
        row.update(vector.features)
        rows.append(row)

    dataframe = pd.DataFrame(rows)

    st.dataframe(dataframe, width="stretch")

    chart_features = [
        "graph_coherence",
        "core_survival_score",
        "attractor_stability",
        "entropy",
        "node_coverage",
    ]

    for feature in chart_features:
        if feature in dataframe.columns:
            st.markdown(f"#### {feature}")
            st.bar_chart(dataframe.set_index("planet")[feature], width="stretch")


def render_relationship_matrix(matrix) -> None:
    """Render planet relationship matrices."""
    st.markdown("### Planet Relationship Matrix")

    tab_similarity, tab_distance, tab_agreement, tab_diagnostics = st.tabs(
        [
            "Similarity",
            "Distance",
            "Agreement",
            "Diagnostics",
        ]
    )

    with tab_similarity:
        st.dataframe(
            pd.DataFrame(matrix.similarity),
            width="stretch",
        )

    with tab_distance:
        st.dataframe(
            pd.DataFrame(matrix.distance),
            width="stretch",
        )

    with tab_agreement:
        st.dataframe(
            pd.DataFrame(matrix.agreement),
            width="stretch",
        )

    with tab_diagnostics:
        st.json(matrix.diagnostics)


def render_quality(identity_vector) -> None:
    """Render IdentityVector quality metadata."""
    st.markdown("### Vector Quality")

    quality = identity_vector.quality

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Planet Count", quality["planet_count"])
    c2.metric("Source Completeness", format_float(quality["source_completeness"]))
    c3.metric("Mean Calibration Size", format_float(quality["mean_calibration_size"]))
    c4.metric("Min Calibration Size", quality["minimum_calibration_size"])

    quality_dataframe = pd.DataFrame(
        [
            {
                "quality_metric": str(key),
                "value": format_table_value(value),
            }
            for key, value in quality.items()
        ]
    )

    st.dataframe(
        quality_dataframe,
        width="stretch",
    )

def format_float(value) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"

def format_table_value(value) -> str:
    """Format mixed values for dashboard tables."""
    if value is None:
        return "n/a"

    if isinstance(value, float):
        return f"{value:.4f}"

    return str(value)
