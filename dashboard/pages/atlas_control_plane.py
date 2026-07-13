"""Atlas Studio read-only Control Plane page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.investment.control_plane_dashboard import (
    build_control_plane_dashboard_model,
)


STATUS_ICON = {
    "HEALTHY": "?",
    "DEGRADED": "??",
    "CRITICAL": "??",
    "READY": "??",
    "BLOCKED": "??",
    "NO_ACTION": "?",
    "NO_PROGRESS": "?",
    "RECONCILED": "?",
    "PARTIALLY_REPAIRED": "??",
    "FAILED": "??",
    "SCOPE_VIOLATION": "??",
    "UNKNOWN": "?",
    "NONE": "?",
}


def render() -> None:
    st.title("Atlas Control Plane")

    st.caption(
        "Read-only operational view of system health, "
        "remediation, approvals, provenance, and reconciliation."
    )

    refresh = st.button(
        "Refresh control plane",
        type="primary",
    )

    with st.spinner(
        "Building canonical control-plane view..."
    ):
        model = (
            build_control_plane_dashboard_model(
                refresh=True
            )
        )

    render_header(model)
    render_components(model)
    render_scheduler(model)
    render_remediation(model)
    render_approval(model)
    render_reconciliation(model)
    render_provenance(model)
    render_contract(model)

    if refresh:
        st.success(
            "Control-plane outputs refreshed."
        )


def render_header(
    model: dict[str, Any],
) -> None:
    status = str(
        model.get(
            "overall_status",
            "UNKNOWN",
        )
    )

    icon = STATUS_ICON.get(
        status,
        "?",
    )

    st.subheader(
        f"{icon} Overall Status: {status}"
    )

    st.write(
        model.get(
            "summary",
            "",
        )
    )

    counts = model.get(
        "counts",
        {},
    )

    columns = st.columns(5)

    metric(
        columns[0],
        "Healthy",
        counts.get(
            "healthy_components",
            0,
        ),
    )

    metric(
        columns[1],
        "Degraded",
        counts.get(
            "degraded_components",
            0,
        ),
    )

    metric(
        columns[2],
        "Critical",
        counts.get(
            "critical_components",
            0,
        ),
    )

    metric(
        columns[3],
        "Actions",
        counts.get(
            "recommended_actions",
            0,
        ),
    )

    metric(
        columns[4],
        "Generated",
        model.get(
            "generated_at",
            "",
        ),
    )


def render_components(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader("Component Health")

    rows = model.get(
        "component_rows",
        [],
    )

    if not rows:
        st.info(
            "No component health data is available."
        )
        return

    columns = st.columns(
        min(4, len(rows))
    )

    for index, row in enumerate(rows):
        container = columns[
            index % len(columns)
        ]

        status = str(
            row.get(
                "status",
                "UNKNOWN",
            )
        )

        icon = STATUS_ICON.get(
            status,
            "?",
        )

        with container:
            st.markdown(
                "### "
                + icon
                + " "
                + display_name(
                    row.get(
                        "component",
                        "",
                    )
                )
            )

            st.metric(
                "Status",
                status,
            )

            st.caption(
                str(
                    row.get(
                        "summary",
                        "",
                    )
                )
            )

            issue_count = int(
                row.get(
                    "issue_count",
                    0,
                )
                or 0
            )

            st.write(
                f"Issues: **{issue_count}**"
            )

            with st.expander(
                "Metrics",
                expanded=False,
            ):
                st.json(
                    row.get(
                        "metrics",
                        {},
                    )
                )


def render_scheduler(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader("Scheduler and DAG")

    scheduler = model.get(
        "scheduler",
        {},
    )

    counts = scheduler.get(
        "counts",
        {},
    )

    columns = st.columns(6)

    for column, label, key in (
        (
            columns[0],
            "Current",
            "current_jobs",
        ),
        (
            columns[1],
            "Ready",
            "ready_jobs",
        ),
        (
            columns[2],
            "Blocked",
            "blocked_jobs",
        ),
        (
            columns[3],
            "Dirty",
            "dirty_jobs",
        ),
        (
            columns[4],
            "Direct Dirty",
            "directly_dirty_jobs",
        ),
        (
            columns[5],
            "Propagated",
            "propagated_dirty_jobs",
        ),
    ):
        metric(
            column,
            label,
            counts.get(
                key,
                0,
            ),
        )

    rows = scheduler.get(
        "rows",
        [],
    )

    if not rows:
        st.info(
            "No scheduler rows are available."
        )
        return

    frame = pd.DataFrame(rows)

    preferred = [
        "schedule_rank",
        "job_id",
        "status",
        "reason",
        "blocking_dependencies",
        "dirty_roots",
        "dirty_depth",
        "invalidation_reason",
    ]

    visible = [
        column
        for column in preferred
        if column in frame.columns
    ]

    status_options = sorted(
        frame[
            "status"
        ].dropna().astype(str).unique()
    ) if "status" in frame.columns else []

    selected_statuses = (
        st.multiselect(
            "Filter scheduler statuses",
            options=status_options,
            default=status_options,
        )
    )

    if (
        selected_statuses
        and "status"
        in frame.columns
    ):
        frame = frame[
            frame[
                "status"
            ].astype(str).isin(
                selected_statuses
            )
        ]

    st.dataframe(
        frame[
            visible
            if visible
            else frame.columns.tolist()
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_remediation(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader("Remediation Plan")

    remediation = model.get(
        "remediation",
        {},
    )

    status = str(
        remediation.get(
            "plan_status",
            "UNKNOWN",
        )
    )

    execution = remediation.get(
        "execution",
        {},
    )

    columns = st.columns(4)

    metric(
        columns[0],
        "Plan Status",
        status,
    )

    metric(
        columns[1],
        "Mode",
        execution.get(
            "mode",
            "NONE",
        ),
    )

    metric(
        columns[2],
        "Executable",
        execution.get(
            "executable",
            False,
        ),
    )

    metric(
        columns[3],
        "Authorized",
        execution.get(
            "authorized",
            False,
        ),
    )

    st.warning(
        "This page is read-only. The displayed command "
        "is advisory and is not executed by Atlas Studio."
    )

    command = str(
        execution.get(
            "recommended_command",
            "",
        )
    )

    if command:
        st.code(
            command,
            language="powershell",
        )

    steps = remediation.get(
        "steps",
        [],
    )

    if steps:
        frame = pd.DataFrame(steps)

        preferred = [
            "step",
            "job_id",
            "severity",
            "priority",
            "prerequisite_plan_jobs",
            "source_action_types",
            "blocked_by_structure",
        ]

        visible = [
            column
            for column in preferred
            if column in frame.columns
        ]

        st.dataframe(
            frame[
                visible
                if visible
                else frame.columns.tolist()
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success(
            "No executable remediation steps are currently required."
        )

    actions = model.get(
        "recommended_actions",
        [],
    )

    with st.expander(
        "Source recommendations",
        expanded=False,
    ):
        if actions:
            st.dataframe(
                pd.DataFrame(actions),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write(
                "No source recommendations."
            )


def render_approval(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader("Latest Approval")

    approval = model.get(
        "approval",
        {},
    )

    if not approval.get(
        "present",
        False,
    ):
        st.info(
            "No remediation approval is present."
        )
        return

    used = bool(
        approval.get(
            "used",
            False,
        )
    )

    columns = st.columns(4)

    metric(
        columns[0],
        "Approval",
        approval.get(
            "approval_id",
            "",
        ),
    )

    metric(
        columns[1],
        "Approved By",
        approval.get(
            "approved_by",
            "",
        ),
    )

    metric(
        columns[2],
        "Used",
        used,
    )

    metric(
        columns[3],
        "Approved Jobs",
        len(
            approval.get(
                "approved_job_ids",
                [],
            )
        ),
    )

    st.write(
        "**Expires:** "
        + str(
            approval.get(
                "expires_at",
                "",
            )
        )
    )

    st.write(
        "**Dispatch run:** "
        + str(
            approval.get(
                "dispatch_run_id",
                "",
            )
        )
    )

    st.write(
        "**Approved job IDs:**"
    )

    st.code(
        "\n".join(
            approval.get(
                "approved_job_ids",
                [],
            )
        )
        or "(none)"
    )

    st.caption(
        "Approval signatures, nonces, and signing secrets "
        "are intentionally hidden."
    )


def render_reconciliation(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader("Latest Dispatch Reconciliation")

    reconciliation = model.get(
        "reconciliation",
        {},
    )

    if not reconciliation.get(
        "present",
        False,
    ):
        st.info(
            "No reconciliation report is present."
        )
        return

    outcome = str(
        reconciliation.get(
            "outcome",
            "UNKNOWN",
        )
    )

    icon = STATUS_ICON.get(
        outcome,
        "?",
    )

    st.markdown(
        f"### {icon} {outcome}"
    )

    st.write(
        reconciliation.get(
            "summary",
            "",
        )
    )

    columns = st.columns(4)

    metric(
        columns[0],
        "Scope Valid",
        reconciliation.get(
            "scope_valid",
            False,
        ),
    )

    metric(
        columns[1],
        "Plan Hash Valid",
        reconciliation.get(
            "plan_hash_matches",
            False,
        ),
    )

    metric(
        columns[2],
        "Attempted",
        len(
            reconciliation.get(
                "attempted_job_ids",
                [],
            )
        ),
    )

    metric(
        columns[3],
        "Repaired",
        len(
            reconciliation.get(
                "repaired_job_ids",
                [],
            )
        ),
    )

    before = reconciliation.get(
        "before",
        {},
    )

    after = reconciliation.get(
        "after",
        {},
    )

    delta = reconciliation.get(
        "delta",
        {},
    )

    comparison = pd.DataFrame([
        {
            "metric": "Health Status",
            "before": before.get(
                "health_status",
                "",
            ),
            "after": after.get(
                "health_status",
                "",
            ),
            "delta": "",
        },
        {
            "metric": "Recommendations",
            "before": before.get(
                "recommendation_count",
                0,
            ),
            "after": after.get(
                "recommendation_count",
                0,
            ),
            "delta": delta.get(
                "recommendations_resolved",
                0,
            ),
        },
        {
            "metric": "Execution Steps",
            "before": before.get(
                "execution_step_count",
                0,
            ),
            "after": after.get(
                "execution_step_count",
                0,
            ),
            "delta": delta.get(
                "execution_steps_reduced",
                0,
            ),
        },
    ])

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

    violations = reconciliation.get(
        "unapproved_job_ids",
        [],
    )

    if violations:
        st.error(
            "Unapproved jobs were detected: "
            + ", ".join(violations)
        )


def render_provenance(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader("Execution Provenance")

    provenance = model.get(
        "provenance",
        {},
    )

    latest = provenance.get(
        "latest_index",
        {},
    )

    columns = st.columns(4)

    metric(
        columns[0],
        "Events",
        provenance.get(
            "event_count",
            0,
        ),
    )

    metric(
        columns[1],
        "Indexed Events",
        latest.get(
            "event_count",
            0,
        ),
    )

    metric(
        columns[2],
        "Indexed Jobs",
        latest.get(
            "indexed_jobs",
            0,
        ),
    )

    metric(
        columns[3],
        "Updated",
        latest.get(
            "updated_at",
            "",
        ),
    )

    events = provenance.get(
        "events",
        [],
    )

    if events:
        frame = pd.DataFrame(events)

        st.dataframe(
            frame,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No provenance events are available."
        )


def render_contract(
    model: dict[str, Any],
) -> None:
    st.divider()

    with st.expander(
        "Dashboard Safety Contract",
        expanded=False,
    ):
        st.json(
            model.get(
                "contract",
                {},
            )
        )


def metric(
    container,
    label: str,
    value: Any,
) -> None:
    container.metric(
        label,
        value,
    )


def display_name(
    value: Any,
) -> str:
    return str(value).replace(
        "_",
        " ",
    ).title()


render()
