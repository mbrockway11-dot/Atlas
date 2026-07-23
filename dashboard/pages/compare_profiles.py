"""Compare Profiles page."""

from __future__ import annotations
import pandas as pd
import streamlit as st

from atlas.library.profile_library import list_saved_profiles

from atlas.services.compare_profiles_service import (
    build_compare_profiles_payload,
)

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

    payload = build_compare_profiles_payload(
        profile_a_key,
        profile_b_key,
        normalization_mode=normalization_mode,
    )

    if not payload.success:
        st.error("\n".join(payload.errors))
        return

    render_similarity_summary(payload.comparison)
    render_score_interpretation(payload.comparison)
    render_planet_similarity(payload.comparison)
    render_planet_agreement_matrix(payload.planet_agreement_matrix)
    render_planet_drilldown(payload.planet_agreement_matrix)
    render_global_feature_delta(payload.vector_a, payload.vector_b)
    render_planet_feature_delta(payload.vector_a, payload.vector_b)


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


def format_float(value) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"

