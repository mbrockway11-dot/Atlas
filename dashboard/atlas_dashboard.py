"""Atlas Streamlit dashboard router."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from atlas.services.autonomous_service import build_autonomous_lab_payload

from atlas.services.mission_control_service import build_mission_control_status

from pages.atlas_ai import render_atlas_ai_page
from pages.autonomous_lab import render_autonomous_lab_page
from pages.compare_profiles import render_compare_profiles_page
from pages.comparison_lab import render_comparison_lab_page
from pages.developer_console import render_developer_console_page
from pages.discovery_lab import render_discovery_lab_page
from pages.dynamics_lab import render_dynamics_lab_page
from pages.decision_lab import render_decision_lab_page
from pages.evidence_explorer import render_evidence_explorer_page
from pages.evolution_lab import render_evolution_lab_page
from pages.graph_explorer import render_graph_explorer_page
from pages.identity_stack_lab import render_identity_stack_lab_page
from pages.intelligence_engine import render_intelligence_engine_page
from pages.knowledge_lab import render_knowledge_lab_page
from pages.morphology_lab import render_morphology_lab_page
from pages.narrative_intelligence import render_narrative_intelligence_page
from pages.population_intelligence import render_population_intelligence_page
from pages.population_observatory import render_population_observatory_page
from pages.population_topology import render_population_topology_page
from pages.population_validation import render_population_validation_page
from pages.profile_builder import render_profile_builder_page
from pages.profile_library import render_profile_library_page
from pages.profile_observatory import render_profile_observatory_page
from pages.profile_report import render_profile_report_page
from pages.profile_test_lab import render_profile_test_lab_page
from pages.relationship_report import render_relationship_report_page
from pages.research_corpus import render_research_corpus_page
from pages.research_orchestrator_lab import render_research_orchestrator_lab_page
from pages.research_session import render_research_session_page
from pages.simulation_lab import render_simulation_lab_page
from pages.role_calibration_lab import render_role_calibration_lab_page
from pages.statistical_intelligence import render_statistical_intelligence_page
from pages.systems_engineering_report import render_systems_engineering_report_page
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
    "Atlas AI": render_atlas_ai_page,
    "Developer Console": render_developer_console_page,

        # Intelligence Reports
        "Profile Report": render_profile_report_page,
        "Narrative Intelligence": render_narrative_intelligence_page,
        "Relationship Report": render_relationship_report_page,
        "Evidence Explorer": render_evidence_explorer_page,

        # Profile Tools
        "Profile Library": render_profile_library_page,
        "Profile Builder": render_profile_builder_page,
        "Profile Observatory": render_profile_observatory_page,
        "Profile Test Lab": render_profile_test_lab_page,
        "Compare Profiles": render_compare_profiles_page,
        "Comparison Lab": render_comparison_lab_page,

        # Research
        "Research Corpus": render_research_corpus_page,
        "Research Orchestrator": render_research_orchestrator_lab_page,
        "Research Session": render_research_session_page,

        # Intelligence
        "Intelligence Engine": render_intelligence_engine_page,
        "Temporal Intelligence": render_temporal_intelligence_page,
        "Statistical Intelligence": render_statistical_intelligence_page,
        "Systems Engineering Report": render_systems_engineering_report_page,
        "Simulation Lab": render_simulation_lab_page,
        "Evolution Lab": render_evolution_lab_page,
        "Decision Lab": render_decision_lab_page,
        "Dynamics Lab": render_dynamics_lab_page,
        "Discovery Lab": render_discovery_lab_page,
        "Knowledge Lab": render_knowledge_lab_page,
        "Population Intelligence": render_population_intelligence_page,
        "Population Observatory": render_population_observatory_page,
        "Population Topology": render_population_topology_page,
        "Population Validation": render_population_validation_page,

        # Validation
        "Validation Lab": render_validation_lab_page,
        "Role Calibration Lab": render_role_calibration_lab_page,

        # Graph / Identity
        "Graph Explorer": render_graph_explorer_page,
        "Identity Stack Lab": render_identity_stack_lab_page,
        "Morphology Lab": render_morphology_lab_page,
    }


def render_sidebar(pages: dict[str, PageRenderer]) -> str:
    """Render sidebar navigation and return selected page label."""
    st.sidebar.title("Atlas")
    st.sidebar.caption("Deterministic Intelligence Operating System")

    selected = st.sidebar.radio(
        "Navigation",
        list(pages.keys()),
    )

    st.sidebar.divider()
    st.sidebar.caption("Architecture")
    st.sidebar.write("Dashboard â†’ Services â†’ AtlasProfile â†’ Kernel â†’ Plugins")

    return selected




def render_autonomous_mission_control() -> None:
    """Render Autonomous Phase V Mission Control metrics."""
    st.markdown("### Phase V ? Autonomous Scientific Research")

    try:
        payload = build_autonomous_lab_payload(
            limit=50,
            max_schedule_items=2,
            force=False,
        )
    except Exception as exc:
        st.warning(f"Autonomous metrics unavailable: {exc}")
        return

    autonomous = payload.get("autonomous", {})
    learning = autonomous.get("learning_update", {})
    theory = autonomous.get("theory", {})
    prediction = autonomous.get("prediction", {})
    falsification = autonomous.get("falsification", {})
    evidence = autonomous.get("evidence_registry", {})
    memory = autonomous.get("memory", {})
    scheduler = autonomous.get("scheduler", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Autonomous Loop", learning.get("learning_label", "offline"))
    c2.metric("Learning Score", format_number(learning.get("learning_score")))
    c3.metric("Evidence Records", len(evidence.get("records", {}) or {}))
    c4.metric("Memory Items", memory_item_count(memory))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Generated Questions", autonomous.get("experiment_plan", {}).get("generated_count", 0))
    c6.metric("Scheduled", scheduler.get("schedule", {}).get("scheduled_count", 0))
    c7.metric("Promoted Theories", theory.get("promoted_count", 0))
    c8.metric("Theory Challenges", falsification.get("challenge_count", 0))

    confidence = autonomous.get("scientific_confidence", {}) or {}

    if confidence:
        c9, c10, c11, c12 = st.columns(4)
        c9.metric("Scientific Confidence", format_number(confidence.get("scientific_confidence")))
        c10.metric("Confidence Label", confidence.get("confidence_label", "n/a"))

        components = confidence.get("components", {}) or {}
        c11.metric("Evidence Score", format_number(components.get("evidence_score")))
        c12.metric("Prediction Score", format_number(components.get("prediction_score")))

    if prediction.get("success"):
        scores = prediction.get("benchmark", {}).get("scores", {})
        c13, c14 = st.columns(2)
        c13.metric("Prediction MAE", format_number(scores.get("mean_absolute_error")))
        c14.metric("Prediction Accuracy", scores.get("accuracy_label", "n/a"))


def memory_item_count(memory: dict) -> int:
    """Count memory items."""
    return (
        len(memory.get("experiments", {}) or {})
        + len(memory.get("evidence", {}) or {})
        + len(memory.get("hypotheses", {}) or {})
    )


def format_number(value) -> str:
    """Format numeric values."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "n/a"

def render_mission_control() -> None:
    """Render Atlas mission-control summary."""
    status = build_mission_control_status()
    systems = status["systems"]
    engines = status["engines"]

    st.markdown("## Mission Control")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Architecture", status["architecture"])
    c2.metric("Tests", status["tests"]["label"])
    c3.metric("Atlas Version", status["atlas_version"])
    c4.metric("Kernel", systems["kernel"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Narrative Engine", engines["narrative"])
    c6.metric("Relationship Engine", engines["relationship"])
    c7.metric("Evidence Explorer", engines["evidence"])
    c8.metric("Graph Explorer", engines["graph_explorer"])

    c9, c10, c11, c12 = st.columns(4)
    c9.metric("Temporal Runtime", systems["temporal_runtime"])
    c10.metric("Graph Intelligence", systems["graph_intelligence"])
    c11.metric("Population", systems["population"])
    c12.metric("IVE", systems["ive"])

    st.success(status["summary"])
    st.info(f"Current development focus: {status['current_focus']}")

    with st.expander("Raw Mission Control Status", expanded=False):
        st.json(status)


def main() -> None:
    """Run Atlas dashboard."""
    st.set_page_config(
        page_title="Atlas Studio",
        page_icon="ðŸ§­",
        layout="wide",
    )

    pages = build_page_registry()
    selected = render_sidebar(pages)

    st.title("Atlas Studio")
    st.markdown("### Deterministic Intelligence Operating System")

    st.caption(
        "A unified platform for deterministic identity, temporal, topological, "
        "graph, relationship, and population intelligenceâ€”designed for research, "
        "interpretation, and discovery."
    )

    render_mission_control()

    st.divider()

    safe_render(selected, pages[selected])


if __name__ == "__main__":
    main()
