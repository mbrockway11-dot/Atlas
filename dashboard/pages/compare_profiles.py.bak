"""Compare Profiles page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from atlas.acf.builder import export_acf_profile
from atlas.comparison import compare_planet_agreement
from atlas.ive import (
    build_identity_vector,
    compare_identity_vectors,
    identity_similarity_to_dict,
)
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


NORMALIZATION_MODES = [
    "raw",
    "percentile",
    "minmax",
    "zscore",
]


def render_compare_profiles_page() -> None:
    """Render Compare Profiles page."""
    st.header("Compare Profiles")
    st.caption(
        "Compare saved profiles using the Identity Vector Engine, "
        "Planet Agreement Matrix, and feature-level divergence diagnostics."
    )

    profiles = list_saved_profiles()

    if len(profiles) < 2:
        st.info("Build at least two profiles first.")
        return

    col1, col2 = st.columns(2)

    with col1:
        profile_a_key = st.selectbox(
            "Profile A",
            profiles,
            key="compare_profile_a",
        )

    with col2:
        profile_b_key = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="compare_profile_b",
        )

    normalization_mode = st.selectbox(
        "Normalization Mode",
        NORMALIZATION_MODES,
        index=1 if len(profiles) >= 3 else 0,
        help=(
            "Raw compares direct bounded measurements. "
            "Percentile, minmax, and zscore use saved profiles as calibration corpus."
        ),
    )

    if profile_a_key == profile_b_key:
        st.warning("Choose two different profiles.")
        return

    if not st.button("Compare Profiles", type="primary"):
        return

    acf_a = load_or_repair_acf(profile_a_key)
    acf_b = load_or_repair_acf(profile_b_key)

    if acf_a is None or acf_b is None:
        st.error("Could not load one or both ACF profiles.")
        return

    calibration_acfs = (
        load_calibration_acfs()
        if normalization_mode != "raw"
        else None
    )

    render_ive_comparison(
        acf_a=acf_a,
        acf_b=acf_b,
        calibration_acfs=calibration_acfs,
        normalization_mode=normalization_mode,
    )


def load_or_repair_acf(profile_key: str) -> dict | None:
    """Load ACF and repair older exports if required."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if not acf_path.exists():
        return None

    data = json.loads(acf_path.read_text(encoding="utf-8"))

    required_keys = {
        "identity",
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


def load_calibration_acfs() -> list[dict]:
    """Load saved ACF profiles as calibration corpus."""
    calibration_acfs = []

    for profile_key in list_saved_profiles():
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.exists():
            continue

        try:
            calibration_acfs.append(
                json.loads(acf_path.read_text(encoding="utf-8"))
            )
        except json.JSONDecodeError:
            continue

    return calibration_acfs


def render_ive_comparison(
    *,
    acf_a: dict,
    acf_b: dict,
    calibration_acfs: list[dict] | None,
    normalization_mode: str,
) -> None:
    """Render Identity Vector Engine comparison."""
    name_a = acf_a["identity"]["name"]
    name_b = acf_b["identity"]["name"]

    st.subheader(f"{name_a} ↔ {name_b}")

    if normalization_mode == "raw":
        st.info("Using raw bounded IdentityVector measurements.")
    else:
        calibration_count = len(calibration_acfs or [])
        st.info(
            f"Using `{normalization_mode}` normalization with "
            f"{calibration_count} calibration profiles."
        )

    vector_a = build_identity_vector(
        acf=acf_a,
        calibration_acfs=calibration_acfs,
        normalization_mode=normalization_mode,
    )
    vector_b = build_identity_vector(
        acf=acf_b,
        calibration_acfs=calibration_acfs,
        normalization_mode=normalization_mode,
    )

    comparison = compare_identity_vectors(vector_a, vector_b)
    planet_matrix = build_planet_agreement_from_vectors(vector_a, vector_b)

    render_similarity_summary(comparison)
    render_planet_similarity(comparison)
    render_planet_agreement_matrix(planet_matrix)
    render_global_feature_delta(vector_a, vector_b)
    render_planet_feature_delta(vector_a, vector_b)

    with st.expander("Raw IVE Similarity JSON"):
        st.json(identity_similarity_to_dict(comparison))

    with st.expander("Raw Planet Agreement Matrix JSON"):
        st.json(planet_agreement_to_dict(planet_matrix))


def build_planet_agreement_from_vectors(vector_a, vector_b):
    """Build Planet Agreement Matrix from IdentityVector planet features."""
    fingerprint_a = {
        planet: vector.features
        for planet, vector in vector_a.planets.items()
    }

    fingerprint_b = {
        planet: vector.features
        for planet, vector in vector_b.planets.items()
    }

    confidence_a = {
        planet: 1.0
        for planet in vector_a.planets
    }

    confidence_b = {
        planet: 1.0
        for planet in vector_b.planets
    }

    return compare_planet_agreement(
        fingerprint_a=fingerprint_a,
        fingerprint_b=fingerprint_b,
        confidence_a=confidence_a,
        confidence_b=confidence_b,
    )


def render_similarity_summary(comparison) -> None:
    """Render top-level comparison metrics."""
    st.markdown("## Identity Similarity Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Composite Similarity", format_float(comparison.composite_similarity))
    c2.metric("Global Similarity", format_float(comparison.global_similarity))
    c3.metric("Relationship Similarity", format_float(comparison.relationship_similarity))
    c4.metric("Global Distance", format_float(comparison.global_distance))

    diagnostics = comparison.diagnostics

    c5, c6, c7 = st.columns(3)

    c5.metric("Strongest Planet Match", diagnostics["strongest_planet_match"])
    c6.metric("Weakest Planet Match", diagnostics["weakest_planet_match"])
    c7.metric("Most Divergent Planet", diagnostics["most_divergent_planet"])

def render_score_interpretation(comparison) -> None:
    """Explain how the similarity scores relate to one another."""

    st.markdown("## Score Interpretation")

    global_similarity = comparison.global_similarity
    relationship_similarity = comparison.relationship_similarity
    composite_similarity = comparison.composite_similarity

    gap = relationship_similarity - global_similarity

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Relationship − Global Gap",
        format_float(gap),
    )

    c2.metric(
        "Composite Similarity",
        format_float(composite_similarity),
    )

    c3.metric(
        "Shared Planets",
        str(comparison.diagnostics["shared_planet_count"]),
    )

    st.markdown("### Interpretation")

    if relationship_similarity >= 0.90 and global_similarity >= 0.90:
        st.success(
            "These identities are highly aligned both globally and internally. "
            "Atlas detects similar overall structural fingerprints and very similar "
            "relationships between planetary layers."
        )

    elif relationship_similarity >= 0.90 and global_similarity < 0.90:
        st.info(
            "The internal planetary relationships are highly aligned, but the overall "
            "structural fingerprint differs more. This suggests similar organization "
            "with different absolute expression."
        )

    elif relationship_similarity < 0.90 and global_similarity >= 0.90:
        st.warning(
            "The overall feature profile is similar, but the relationships between "
            "planetary layers differ. The identities share comparable measurements "
            "but organize them differently."
        )

    else:
        st.warning(
            "Both global structure and planetary relationships differ. "
            "Atlas detects limited structural correspondence between these identities."
        )

def render_planet_similarity(comparison) -> None:
    """Render per-planet similarity table."""
    st.markdown("## Planet Similarity")

    rows = []

    for planet, similarity in comparison.planet_similarity.items():
        rows.append(
            {
                "planet": planet,
                "similarity": similarity,
                "distance": comparison.planet_distance[planet],
                "agreement": comparison.planet_agreement[planet],
            }
        )

    dataframe = pd.DataFrame(rows)

    st.dataframe(dataframe, width="stretch")

    if not dataframe.empty:
        st.bar_chart(
            dataframe.set_index("planet")["similarity"],
            width="stretch",
        )


def render_planet_agreement_matrix(matrix) -> None:
    """Render Planet Agreement Matrix diagnostics."""
    st.markdown("## Planet Agreement Matrix")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Overall Similarity", format_float(matrix.overall_similarity))
    c2.metric("Planet Agreement", format_float(matrix.planet_agreement))
    c3.metric("Dominant Match", matrix.dominant_match)
    c4.metric("Dominant Divergence", matrix.dominant_divergence)

    rows = []

    for row in matrix.rows:
        rows.append(
            {
                "planet": row.planet,
                "similarity": row.similarity,
                "distance": row.distance,
                "confidence": row.confidence,
                "strongest_matches": ", ".join(row.strongest_matches),
                "strongest_differences": ", ".join(row.strongest_differences),
            }
        )

    dataframe = pd.DataFrame(rows)

    st.markdown("### Planet-Level Agreement")
    st.dataframe(dataframe, width="stretch")

    if not dataframe.empty:
        st.bar_chart(
            dataframe.set_index("planet")["similarity"],
            width="stretch",
        )

    render_planet_drilldown(matrix)


def render_planet_drilldown(matrix) -> None:
    """Render selected-planet feature-distance drilldown."""
    st.markdown("### Planet Drilldown")

    planet_names = [
        row.planet
        for row in matrix.rows
    ]

    if not planet_names:
        st.info("No planet rows available.")
        return

    default_index = (
        planet_names.index(matrix.dominant_divergence)
        if matrix.dominant_divergence in planet_names
        else 0
    )

    selected_planet = st.selectbox(
        "Inspect Planet",
        planet_names,
        index=default_index,
    )

    selected_row = next(
        row
        for row in matrix.rows
        if row.planet == selected_planet
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Similarity", format_float(selected_row.similarity))
    c2.metric("Distance", format_float(selected_row.distance))
    c3.metric("Confidence", format_float(selected_row.confidence))

    col_match, col_difference = st.columns(2)

    with col_match:
        st.markdown("#### Strongest Matches")
        if selected_row.strongest_matches:
            for feature in selected_row.strongest_matches:
                st.write(f"- `{feature}`")
        else:
            st.info("No strongest matches available.")

    with col_difference:
        st.markdown("#### Strongest Differences")
        if selected_row.strongest_differences:
            for feature in selected_row.strongest_differences:
                st.write(f"- `{feature}`")
        else:
            st.info("No strongest differences available.")

    detail_rows = [
        {
            "feature": feature,
            "distance": distance,
        }
        for feature, distance in selected_row.feature_distances.items()
    ]

    detail = pd.DataFrame(detail_rows)

    if detail.empty:
        st.info("No feature-distance detail available for this planet.")
        return

    detail = detail.sort_values("distance", ascending=False)

    st.markdown("#### Feature Distance Ranking")
    st.dataframe(detail, width="stretch")

    st.markdown("#### Top Divergence Features")
    st.bar_chart(
        detail.head(12).set_index("feature")["distance"],
        width="stretch",
    )


def render_global_feature_delta(vector_a, vector_b) -> None:
    """Render global feature deltas."""
    st.markdown("## Global Feature Differences")

    rows = []

    shared_features = sorted(
        set(vector_a.global_features)
        & set(vector_b.global_features)
    )

    for feature in shared_features:
        value_a = vector_a.global_features[feature]
        value_b = vector_b.global_features[feature]

        rows.append(
            {
                "feature": feature,
                "value_a": value_a,
                "value_b": value_b,
                "absolute_difference": abs(value_a - value_b),
            }
        )

    dataframe = pd.DataFrame(rows).sort_values(
        "absolute_difference",
        ascending=False,
    )

    st.dataframe(dataframe, width="stretch")


def render_planet_feature_delta(vector_a, vector_b) -> None:
    """Render planet-level feature deltas."""
    st.markdown("## Planet Feature Differences")

    rows = []

    shared_planets = [
        planet
        for planet in vector_a.planets
        if planet in vector_b.planets
    ]

    for planet in shared_planets:
        features_a = vector_a.planets[planet].features
        features_b = vector_b.planets[planet].features

        shared_features = sorted(
            set(features_a)
            & set(features_b)
        )

        for feature in shared_features:
            value_a = features_a[feature]
            value_b = features_b[feature]

            rows.append(
                {
                    "planet": planet,
                    "feature": feature,
                    "value_a": value_a,
                    "value_b": value_b,
                    "absolute_difference": abs(value_a - value_b),
                }
            )

    dataframe = pd.DataFrame(rows).sort_values(
        "absolute_difference",
        ascending=False,
    )

    st.dataframe(dataframe, width="stretch")

    top = dataframe.head(20)

    if not top.empty:
        st.markdown("### Top 20 Separating Planet Features")
        st.dataframe(top, width="stretch")


def planet_agreement_to_dict(matrix) -> dict:
    """Convert Planet Agreement Matrix to a JSON-safe dictionary."""
    return {
        "overall_similarity": matrix.overall_similarity,
        "planet_similarity": matrix.planet_similarity,
        "planet_confidence": matrix.planet_confidence,
        "planet_variance": matrix.planet_variance,
        "planet_agreement": matrix.planet_agreement,
        "dominant_match": matrix.dominant_match,
        "dominant_divergence": matrix.dominant_divergence,
        "rows": [
            {
                "planet": row.planet,
                "similarity": row.similarity,
                "distance": row.distance,
                "confidence": row.confidence,
                "strongest_matches": row.strongest_matches,
                "strongest_differences": row.strongest_differences,
                "feature_distances": row.feature_distances,
            }
            for row in matrix.rows
        ],
    }


def format_float(value) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"
