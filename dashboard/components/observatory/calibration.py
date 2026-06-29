"""Observatory calibration component."""

import pandas as pd
import streamlit as st

from atlas.research import (
    build_population_baselines,
    build_profile_matrix_rows,
    compute_profile_zscores,
)


DISPLAY_ZSCORES = [
    "node_coverage",
    "density",
    "entropy",
    "axis_strength",
    "unique_nodes",
    "unique_edges",
    "max_node_weight",
    "max_depth",
    "self_loops",
]


def render_calibration_view(acf: dict) -> None:
    """Render calibrated z-score research view."""
    st.markdown("## Calibrated Research View")

    rows = build_profile_matrix_rows(acf)
    baselines = build_population_baselines(rows)
    calibrated = compute_profile_zscores(rows, baselines)

    st.warning(
        "Current calibration is using this profile as its own temporary baseline. "
        "This verifies the UI wiring, but true z-scores require a population matrix "
        "from many profiles."
    )

    dataframe = calibration_dataframe(calibrated)

    st.dataframe(
        dataframe,
        use_container_width=True,
    )

    with st.expander("Raw calibrated layer data"):
        st.json(calibrated)


def calibration_dataframe(calibrated: list[dict]) -> pd.DataFrame:
    """Convert calibrated rows to a compact dataframe."""
    rows = []

    for row in calibrated:
        output = {
            "cipher": row["cipher"],
            "planet": row["planet"],
            "grid_size": row["grid_size"],
            "sequence_length": row["sequence_length"],
            "node_coverage": row["node_coverage"],
            "entropy": row["entropy"],
            "density": row["density"],
            "max_depth": row["max_depth"],
            "self_loops": row["self_loops"],
        }

        for metric in DISPLAY_ZSCORES:
            output[f"{metric}_z"] = row["zscores"][metric]

        rows.append(output)

    return pd.DataFrame(rows)