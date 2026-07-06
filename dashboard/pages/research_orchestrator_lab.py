
"""Research Orchestrator Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.research_orchestrator_service import (
    build_research_orchestrator_payload,
    list_research_profiles,
)


def render_research_orchestrator_lab_page() -> None:
    """Render Research Orchestrator Lab."""
    st.header("Research Orchestrator Lab")
    st.caption("Plan ? prioritize ? execute Discovery, Causality, Knowledge ? extract research insights.")

    profiles = list_research_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        limit = st.slider("Profile limit", 10, min(200, len(profiles)), min(50, len(profiles)))

    with c2:
        max_tasks = st.slider("Max tasks", 1, 10, 3)

    with c3:
        force = st.toggle("Force recompile", value=False)

    selected_profiles = st.multiselect(
        "Optional profile subset",
        profiles,
        default=[],
    )

    use_profiles = selected_profiles or None
    effective_limit = None if selected_profiles else limit

    if not st.button("Run Research Orchestrator", type="primary"):
        st.info("Run orchestration to let Atlas plan and execute research tasks.")
        return

    with st.spinner("Running Research Orchestrator..."):
        payload = build_research_orchestrator_payload(
            use_profiles,
            limit=effective_limit,
            force=force,
            max_tasks=max_tasks,
        )

    if not payload.get("success"):
        st.error("Research Orchestrator failed.")
        st.json(payload)
        return

    report = payload.get("orchestration", {})

    render_summary(payload)
    render_plan(report)
    render_schedule(report)
    render_execution(report)
    render_insights(report)
    render_raw(report)


def render_summary(payload: dict) -> None:
    """Render summary."""
    st.markdown("## Research Summary")
    st.info(payload.get("summary", ""))

    c1, c2 = st.columns(2)
    c1.metric("Records", payload.get("record_count", 0))
    c2.metric("Insights", len(payload.get("insights", [])))


def render_plan(report: dict) -> None:
    """Render research plan."""
    st.markdown("## Research Plan")

    plan = report.get("plan", {})
    tasks = plan.get("tasks", [])

    if not tasks:
        st.info("No tasks planned.")
        return

    rows = []
    for task in tasks:
        rows.append(
            {
                "task_id": task.get("task_id"),
                "goal_id": task.get("goal_id"),
                "question": task.get("question"),
                "priority": task.get("priority"),
                "rank_score": task.get("rank_score"),
                "ready": task.get("ready"),
                "engines": ", ".join(task.get("engines", []) or []),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_schedule(report: dict) -> None:
    """Render schedule."""
    st.markdown("## Execution Schedule")

    schedule = report.get("schedule", {})
    tasks = schedule.get("scheduled_tasks", [])

    if tasks:
        st.dataframe(pd.DataFrame(tasks), width="stretch")
    else:
        st.info("No scheduled tasks.")


def render_execution(report: dict) -> None:
    """Render execution details."""
    st.markdown("## Execution")

    execution = report.get("execution", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Tasks", execution.get("task_count", 0))
    c2.metric("Completed", execution.get("completed_count", 0))
    c3.metric("Skipped", execution.get("skipped_count", 0))

    results = execution.get("results", [])

    for result in results:
        with st.expander(result.get("task_id", "Task"), expanded=False):
            st.write(result.get("summary", ""))
            st.json({
                "success": result.get("success"),
                "status": result.get("status"),
                "question": result.get("question"),
                "engines": result.get("engines"),
            })


def render_insights(report: dict) -> None:
    """Render extracted insights."""
    st.markdown("## Extracted Insights")

    insights = report.get("insights", [])

    if not insights:
        st.info("No insights extracted.")
        return

    st.dataframe(pd.DataFrame(insights), width="stretch")


def render_raw(report: dict) -> None:
    """Render raw report."""
    with st.expander("Raw Research Orchestrator JSON", expanded=False):
        st.json(report)
