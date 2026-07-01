"""Atlas Streamlit dashboard router."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from pages.compare_profiles import render_compare_profiles_page
from pages.developer_console import render_developer_console_page
from pages.identity_stack_lab import render_identity_stack_lab_page
from pages.intelligence_engine import render_intelligence_engine_page
from pages.morphology_lab import render_morphology_lab_page
from pages.population_intelligence import render_population_intelligence_page
from pages.population_observatory import render_population_observatory_page
from pages.population_topology import render_population_topology_page
from pages.population_validation import render_population_validation_page
from pages.profile_builder import render_profile_builder_page
from pages.profile_library import render_profile_library_page
from pages.profile_observatory import render_profile_observatory_page
from pages.profile_report import render_profile_report_page
from pages.profile_test_lab import render_profile_test_lab_page
from pages.research_corpus import render_research_corpus_page
from pages.research_session import render_research_session_page
from pages.role_calibration_lab import render_role_calibration_lab_page
from pages.statistical_intelligence import render_statistical_intelligence_page
from pages.temporal_intelligence import render_temporal_intelligence_page
from pages.validation_lab import render_validation_lab_page


PageRenderer = Callable[[], None]


def safe_render(label: str, render_fn: PageRenderer) -> None:
    """Render a dashboard page with visible exception output."""
    try:
        render_fn()
    except Exception as exc:
        st.error(f"{label} failed.")
        st.exception(exc)


def build_page_registry() -> dict[str, PageRenderer]:
    """Build the Atlas dashboard page registry."""
    return {
        "Developer Console": render_developer_console_page,
        "Profile Report": render_profile_report_page,
        "Profile Library": render_profile_library_page,
        "Profile Builder": render_profile_builder_page,
        "Profile Observatory": render_profile_observatory_page,
        "Profile Test Lab": render_profile_test_lab_page,
        "Compare Profiles": render_compare_profiles_page,
        "Research Corpus": render_research_corpus_page,
        "Research Session": render_research_session_page,
        "Intelligence Engine": render_intelligence_engine_page,
        "Temporal Intelligence": render_temporal_intelligence_page,
        "Statistical Intelligence": render_statistical_intelligence_page,
        "Population Intelligence": render_population_intelligence_page,
        "Population Observatory": render_population_observatory_page,
        "Population Topology": render_population_topology_page,
        "Population Validation": render_population_validation_page,
        "Validation Lab": render_validation_lab_page,
        "Role Calibration Lab": render_role_calibration_lab_page,
        "Identity Stack Lab": render_identity_stack_lab_page,
        "Morphology Lab": render_morphology_lab_page,
    }


def render_sidebar(pages: dict[str, PageRenderer]) -> str:
    """Render sidebar navigation and return selected page label."""
    st.sidebar.title("Atlas")
    st.sidebar.caption("Deterministic Symbolic Topology Research Dashboard")

    selected = st.sidebar.radio(
        "Navigation",
        list(pages.keys()),
    )

    st.sidebar.divider()
    st.sidebar.caption("Architecture")
    st.sidebar.write("Dashboard → Services → Kernel → Plugins")

    return selected


def main() -> None:
    """Run Atlas dashboard."""
    st.set_page_config(
        page_title="Atlas Dashboard",
        page_icon="🧭",
        layout="wide",
    )

    pages = build_page_registry()
    selected = render_sidebar(pages)

    st.title("Atlas Studio")
    st.caption("Deterministic Symbolic Topology Research Dashboard")

    safe_render(selected, pages[selected])


if __name__ == "__main__":
    main()