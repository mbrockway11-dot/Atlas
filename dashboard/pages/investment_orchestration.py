"""Read-only G.17 investment orchestration dashboard."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import streamlit as st

from atlas.investment.orchestration.observability import (
    ObservabilityError,
    build_dashboard_snapshot,
)
from atlas.investment.orchestration.reconciliation import (
    ReconciliationError,
    reconcile,
)

SCHEDULER_DECISION = Path("output/investment_scheduler/scheduler_decision.json")
LATEST_REPORT = Path("output/investment_orchestration/latest_report.json")
CHECKPOINT = Path("output/investment_orchestration/checkpoint.json")
HISTORY = Path("output/investment_orchestration/history.jsonl")


def render() -> None:
    st.title("Investment Orchestration")
    st.caption("G.17 read-only observability and reconciliation")

    try:
        snapshot = build_dashboard_snapshot(
            scheduler_decision_path=SCHEDULER_DECISION,
            latest_report_path=LATEST_REPORT,
            checkpoint_path=CHECKPOINT,
            history_path=HISTORY,
        )
    except ObservabilityError as exc:
        st.error(str(exc))
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "History chain",
        "VALID" if snapshot.history_chain_valid else "INVALID",
    )
    col2.metric(
        "Dependency chain",
        "VALID" if snapshot.dependency_chain_valid else "INVALID",
    )
    col3.metric(
        "Duplicate prevention",
        "ACTIVE" if snapshot.duplicate_prevention_enabled else "MISSING",
    )
    col4.metric(
        "Scheduler state",
        "STALE" if snapshot.stale_scheduler_decision else "CURRENT",
    )

    if snapshot.missing_artifacts:
        st.warning(
            "Missing artifacts: " + ", ".join(snapshot.missing_artifacts)
        )
    for warning in snapshot.warnings:
        st.warning(warning)

    if snapshot.scheduler_decision is not None:
        st.subheader("Scheduler decision")
        st.json(snapshot.scheduler_decision)

    if snapshot.latest_report is not None:
        st.subheader("Latest orchestration cycle")
        report = snapshot.latest_report
        st.write(
            {
                "decision_id": report.get("decision_id"),
                "run_id": report.get("run_id"),
                "status": report.get("status"),
                "elapsed_ms": report.get("elapsed_ms"),
                "dry_run": report.get("dry_run"),
            }
        )

        jobs = report.get("jobs", [])
        if isinstance(jobs, list) and jobs:
            st.dataframe(jobs, use_container_width=True, hide_index=True)

    if snapshot.checkpoint is not None:
        st.subheader("Checkpoint")
        st.json(snapshot.checkpoint)

    left, right = st.columns(2)
    with left:
        st.subheader("Latest successful cycle")
        st.json(snapshot.latest_successful_cycle or {})
    with right:
        st.subheader("Latest failed cycle")
        st.json(snapshot.latest_failed_cycle or {})

    if (
        snapshot.scheduler_decision is not None
        and snapshot.latest_report is not None
    ):
        st.subheader("Scheduler reconciliation")
        try:
            report = reconcile(
                snapshot.scheduler_decision,
                snapshot.latest_report,
            )
            st.json(asdict(report))
        except ReconciliationError as exc:
            st.error(str(exc))

    st.info(
        "Read-only dashboard. No execution buttons, command entry, credentials, "
        "broker connectivity, or live-order submission are available."
    )


render()
