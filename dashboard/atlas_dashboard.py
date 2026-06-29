"""Atlas Studio v2 main router with debug checkpoints."""

from __future__ import annotations

import traceback

import streamlit as st

st.set_page_config(
    page_title="Atlas Studio",
    page_icon="🜂",
    layout="wide",
)


DEBUG = True


def debug(message: str) -> None:
    """Render debug checkpoint."""
    if DEBUG:
        st.sidebar.caption(f"DEBUG: {message}")


def safe_render(page_name: str, render_fn) -> None:
    """Render a page and show errors instead of blanking."""
    try:
        debug(f"Rendering {page_name}")
        render_fn()
        debug(f"Rendered {page_name}")
    except Exception:
        st.error(f"{page_name} failed.")
        st.code(traceback.format_exc())


def main() -> None:
    """Run Atlas Studio."""
    debug("main started")

    st.title("Atlas Studio")
    st.caption("Deterministic Symbolic Topology Research Dashboard")

    debug("loading page imports")

    from pages.compare_profiles import render_compare_profiles_page
    from pages.identity_stack_lab import render_identity_stack_lab_page
    from pages.morphology_lab import render_morphology_lab_page
    from pages.population_intelligence import render_population_intelligence_page
    from pages.population_observatory import render_population_observatory_page
    from pages.profile_builder import render_profile_builder_page
    from pages.profile_library import render_profile_library_page
    from pages.profile_observatory import render_profile_observatory_page
    from pages.profile_test_lab import render_profile_test_lab_page
    from pages.research_corpus import render_research_corpus_page
    from pages.role_calibration_lab import render_role_calibration_lab_page
    from pages.validation_lab import render_validation_lab_page

    debug("page imports loaded")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Profile Builder",
            "Profile Observatory",
            "Population Observatory",
            "Population Intelligence",
            "Identity Stack Lab",
            "Morphology Lab",
            "Profile Test Lab",
            "Role Calibration Lab",
            "Validation Lab",
            "Profile Library",
            "Compare Profiles",
            "Research Corpus",
        ],
    )

    debug(f"selected page: {page}")

    if page == "Profile Builder":
        safe_render("Profile Builder", render_profile_builder_page)

    elif page == "Profile Observatory":
        safe_render("Profile Observatory", render_profile_observatory_page)

    elif page == "Population Observatory":
        safe_render(
            "Population Observatory",
            render_population_observatory_page,
        )

    elif page == "Population Intelligence":
        safe_render(
            "Population Intelligence",
            render_population_intelligence_page,
        )

    elif page == "Identity Stack Lab":
        safe_render("Identity Stack Lab", render_identity_stack_lab_page)

    elif page == "Morphology Lab":
        safe_render("Morphology Lab", render_morphology_lab_page)

    elif page == "Profile Test Lab":
        safe_render("Profile Test Lab", render_profile_test_lab_page)

    elif page == "Role Calibration Lab":
        safe_render("Role Calibration Lab", render_role_calibration_lab_page)

    elif page == "Validation Lab":
        safe_render("Validation Lab", render_validation_lab_page)

    elif page == "Profile Library":
        safe_render("Profile Library", render_profile_library_page)

    elif page == "Compare Profiles":
        safe_render("Compare Profiles", render_compare_profiles_page)

    elif page == "Research Corpus":
        safe_render("Research Corpus", render_research_corpus_page)


if __name__ == "__main__":
    main()