
"""Autonomous Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.autonomous_service import (
    build_autonomous_director_payload,
    list_autonomous_profiles,
)


def render_autonomous_lab_page() -> None:
    """Render Autonomous Lab."""
    st.header("Autonomous Lab")
    st.caption("Phase V loop: evidence ? memory ? experiments ? scheduler ? theory ? falsification ? prediction ? learning.")

    profiles = list_autonomous_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        limit = st.slider("Profile limit", 20, min(300, len(profiles)), min(50, len(profiles)))

    with c2:
        max_schedule_items = st.slider("Scheduled questions", 1, 10, 3)

    with c3:
        force = st.toggle("Force recompile", value=False)

    holdout_ratio = st.slider("Prediction holdout ratio", 0.05, 0.50, 0.20, 0.05)
    goal = st.text_input("Director goal", value="general_autonomous_research")
    export = st.toggle("Export reports", value=True)

    selected_profiles = st.multiselect(
        "Optional profile subset",
        profiles,
        default=[],
    )

    use_profiles = selected_profiles or None
    effective_limit = None if selected_profiles else limit

    if not st.button("Run Autonomous Learning Cycle", type="primary"):
        st.info("Run the full Phase V autonomous research loop.")
        return

    with st.spinner("Running Autonomous Learning Cycle..."):
        payload = build_autonomous_director_payload(
            use_profiles,
            limit=effective_limit,
            force=force,
            goal=goal,
            max_schedule_items=max_schedule_items,
            holdout_ratio=holdout_ratio,
            export=export,
        )

    if not payload.get("success"):
        st.error("Autonomous Lab failed.")
        st.json(payload)
        return

    report = payload.get("autonomous", {})

    render_summary(payload)
    render_director_status(payload)
    render_confidence(report)
    render_learning(report)
    render_experiment_plan(report)
    render_theory(report)
    render_falsification(report)
    render_prediction(report)
    render_evidence(report)
    render_memory(report)
    render_raw(report)


def render_summary(payload: dict) -> None:
    """Render executive summary."""
    st.markdown("## Autonomous Summary")
    st.info(payload.get("summary", ""))

    learning = payload.get("learning_update", {})
    theory = payload.get("theory", {})
    prediction = payload.get("prediction", {})
    falsification = payload.get("falsification", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", payload.get("record_count", 0))
    c2.metric("Learning Score", format_number(learning.get("learning_score")))
    c3.metric("Promoted Theories", theory.get("promoted_count", 0))
    c4.metric("Challenges", falsification.get("challenge_count", 0))

    if prediction.get("success"):
        scores = prediction.get("benchmark", {}).get("scores", {})
        c5, c6 = st.columns(2)
        c5.metric("Prediction MAE", format_number(scores.get("mean_absolute_error")))
        c6.metric("Accuracy", scores.get("accuracy_label", "n/a"))




def render_director_status(payload: dict) -> None:
    """Render Director status."""
    st.markdown("## Director Status")

    director = payload.get("director", {})
    health = payload.get("health", {})
    checkpoints = payload.get("checkpoints", {})
    state = director.get("state", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Director State", state.get("state", "n/a"))
    c2.metric("Health", "healthy" if health.get("healthy") else "warnings")
    c3.metric("Warnings", health.get("warning_count", 0))
    c4.metric("Checkpoints", checkpoints.get("checkpoint_count", 0))

    if health.get("warnings"):
        st.warning("\\n".join(health.get("warnings", [])))

    with st.expander("Director State History", expanded=False):
        st.json(state.get("history", []))

    with st.expander("Director Checkpoints", expanded=False):
        st.json(checkpoints)




def render_confidence(report: dict) -> None:
    """Render Scientific Confidence panel."""
    st.markdown("## Scientific Confidence")

    confidence = report.get("scientific_confidence", {})

    if not confidence:
        st.info("No scientific confidence report available.")
        return

    st.info(confidence.get("summary", ""))

    c1, c2 = st.columns(2)
    c1.metric("Scientific Confidence", format_number(confidence.get("scientific_confidence")))
    c2.metric("Confidence Label", confidence.get("confidence_label", "n/a"))

    components = confidence.get("components", {}) or {}

    if components:
        rows = [
            {"component": key, "score": value}
            for key, value in components.items()
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch")

    with st.expander("Confidence Inputs", expanded=False):
        st.json(confidence.get("inputs", {}))


def render_learning(report: dict) -> None:
    """Render learning update."""
    st.markdown("## Learning Update")

    update = report.get("learning_update", {})

    c1, c2 = st.columns(2)
    c1.metric("Learning Label", update.get("learning_label", "n/a"))
    c2.metric("Signals", update.get("signal_count", 0))

    signals = update.get("signals", [])
    if signals:
        st.dataframe(pd.DataFrame(signals), width="stretch")


def render_experiment_plan(report: dict) -> None:
    """Render experiment generation and schedule."""
    st.markdown("## Experiment Plan & Scheduler")

    plan = report.get("experiment_plan", {})
    scheduler = report.get("scheduler", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Generated", plan.get("generated_count", 0))
    c2.metric("Selected", plan.get("selected_count", 0))
    c3.metric("Scheduled", scheduler.get("schedule", {}).get("scheduled_count", 0))

    tabs = st.tabs(["Selected Questions", "Schedule", "Scheduler Raw"])

    with tabs[0]:
        selected = plan.get("selected_questions", [])
        if selected:
            st.dataframe(pd.DataFrame(selected), width="stretch")
        else:
            st.info("No selected questions.")

    with tabs[1]:
        scheduled = scheduler.get("schedule", {}).get("scheduled_items", [])
        if scheduled:
            st.dataframe(pd.DataFrame(scheduled), width="stretch")
        else:
            st.info("No scheduled items.")

    with tabs[2]:
        st.json(scheduler)


def render_theory(report: dict) -> None:
    """Render theory report."""
    st.markdown("## Theory Engine")

    theory = report.get("theory", {})
    st.info(theory.get("summary", ""))

    c1, c2, c3 = st.columns(3)
    c1.metric("Evidence", theory.get("evidence_count", 0))
    c2.metric("Candidates", theory.get("candidate_count", 0))
    c3.metric("Promoted", theory.get("promoted_count", 0))

    theories = theory.get("theories", [])
    if theories:
        rows = [
            {
                "theory_id": item.get("theory_id"),
                "label": item.get("label"),
                "status": item.get("status"),
                "theory_score": item.get("theory_score"),
                "strength": item.get("theory_strength"),
                "evidence_count": item.get("evidence_count"),
            }
            for item in theories
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch")


def render_falsification(report: dict) -> None:
    """Render falsification report."""
    st.markdown("## Falsification Engine")

    falsification = report.get("falsification", {})
    st.info(falsification.get("summary", ""))

    challenges = falsification.get("challenges", [])

    if not challenges:
        st.info("No theory challenges available.")
        return

    rows = [
        {
            "theory_id": item.get("theory_id"),
            "label": item.get("label"),
            "status": item.get("status"),
            "original_score": item.get("original_score"),
            "adjusted_score": item.get("adjusted_score"),
            "counterexamples": item.get("counterexample_count"),
            "contradictions": item.get("contradiction_count"),
            "rivals": item.get("rival_model_count"),
        }
        for item in challenges
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_prediction(report: dict) -> None:
    """Render prediction report."""
    st.markdown("## Prediction Challenge")

    prediction = report.get("prediction", {})

    if not prediction.get("success"):
        st.warning(prediction.get("summary", "Prediction unavailable."))
        return

    st.info(prediction.get("summary", ""))

    scores = prediction.get("benchmark", {}).get("scores", {})
    targets = scores.get("targets", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Mean Absolute Error", format_number(scores.get("mean_absolute_error")))
    c2.metric("Max Absolute Error", format_number(scores.get("max_absolute_error")))
    c3.metric("Accuracy Label", scores.get("accuracy_label", "n/a"))

    if targets:
        rows = [
            {
                "target": key,
                **value,
            }
            for key, value in targets.items()
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch")


def render_evidence(report: dict) -> None:
    """Render evidence registry."""
    st.markdown("## Evidence Registry")

    evidence = report.get("evidence_registry", {})
    records = evidence.get("records", {}) or {}

    c1, c2 = st.columns(2)
    c1.metric("Evidence Records", len(records))
    c2.metric("Relations", len(evidence.get("relations", []) or []))

    if records:
        rows = list(records.values())
        st.dataframe(pd.DataFrame(rows), width="stretch")


def render_memory(report: dict) -> None:
    """Render research memory."""
    st.markdown("## Research Memory")

    memory = report.get("memory", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Experiments", len(memory.get("experiments", {}) or {}))
    c2.metric("Evidence", len(memory.get("evidence", {}) or {}))
    c3.metric("Hypotheses", len(memory.get("hypotheses", {}) or {}))

    with st.expander("Memory JSON", expanded=False):
        st.json(memory)


def render_raw(report: dict) -> None:
    """Render raw autonomous report."""
    with st.expander("Raw Autonomous JSON", expanded=False):
        st.json(report)


def format_number(value) -> str:
    """Format numeric value."""
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "n/a"
