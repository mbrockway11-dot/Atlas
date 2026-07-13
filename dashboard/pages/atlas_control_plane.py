"""Atlas Studio read-only Control Plane page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.investment.control_plane_dashboard import (
    build_control_plane_dashboard_model,
)
from atlas.investment.control_plane_operator import (
    build_dispatch_preflight,
    build_operator_preflight,
    create_guarded_approval,
    dispatch_guarded_approval,
    reconcile_guarded_dispatch,
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
    render_operator_controls()
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



def render_operator_controls() -> None:
    st.divider()
    st.subheader("Guarded Operator Controls")

    st.warning(
        "These controls use backend preflight validation. "
        "No raw command execution exists in this page."
    )

    approval_tab, dispatch_tab, reconcile_tab = st.tabs([
        "Approve",
        "Dispatch",
        "Reconcile",
    ])

    with approval_tab:
        render_approval_control()

    with dispatch_tab:
        render_dispatch_control()

    with reconcile_tab:
        render_reconcile_control()


def render_approval_control() -> None:
    try:
        preflight = build_operator_preflight()
    except Exception as error:
        st.error(
            "Approval preflight failed: "
            + str(error)
        )
        return

    render_preflight_summary(
        preflight
    )

    if not preflight.get(
        "success",
        False,
    ):
        st.info(
            "Approval is unavailable until preflight is READY."
        )
        return

    expected = str(
        preflight.get(
            "approval_confirmation",
            "",
        )
    )

    eligible_count = len(
        preflight.get(
            "eligible_job_ids",
            [],
        )
    )

    with st.form(
        "guarded_approval_form"
    ):
        approved_by = st.text_input(
            "Approved by",
            value="",
        )

        ttl_minutes = st.number_input(
            "Approval lifetime in minutes",
            min_value=1,
            max_value=240,
            value=30,
            step=1,
        )

        max_steps = st.number_input(
            "Maximum approved steps",
            min_value=1,
            max_value=max(
                1,
                eligible_count,
            ),
            value=min(
                1,
                max(
                    1,
                    eligible_count,
                ),
            ),
            step=1,
        )

        st.code(expected)

        confirmation = st.text_input(
            "Type the exact approval phrase"
        )

        submitted = st.form_submit_button(
            "Create signed approval",
            type="primary",
        )

    if submitted:
        try:
            result = create_guarded_approval(
                approved_by=approved_by,
                confirmation=confirmation,
                ttl_minutes=int(
                    ttl_minutes
                ),
                max_steps=int(
                    max_steps
                ),
            )

            st.success(
                "Signed approval created."
            )

            st.json(
                result.get(
                    "approval",
                    {},
                )
            )

        except Exception as error:
            st.error(str(error))


def render_dispatch_control() -> None:
    try:
        preflight = (
            build_dispatch_preflight()
        )
    except Exception as error:
        st.error(
            "Dispatch preflight failed: "
            + str(error)
        )
        return

    render_preflight_summary(
        preflight
    )

    if not preflight.get(
        "success",
        False,
    ):
        st.info(
            "Dispatch is unavailable until preflight is READY."
        )
        return

    expected = str(
        preflight.get(
            "dispatch_confirmation",
            "",
        )
    )

    st.write(
        "**Approved jobs:** "
        + ", ".join(
            preflight.get(
                "approved_job_ids",
                [],
            )
        )
    )

    with st.form(
        "guarded_dispatch_form"
    ):
        timeout_seconds = st.number_input(
            "Per-job timeout in seconds",
            min_value=30,
            max_value=7200,
            value=1800,
            step=30,
        )

        continue_on_failure = st.checkbox(
            "Continue after a failed approved job",
            value=False,
        )

        st.code(expected)

        confirmation = st.text_input(
            "Type the exact dispatch phrase"
        )

        submitted = st.form_submit_button(
            "Dispatch approved scope",
            type="primary",
        )

    if submitted:
        try:
            result = (
                dispatch_guarded_approval(
                    confirmation=confirmation,
                    timeout_seconds=int(
                        timeout_seconds
                    ),
                    continue_on_failure=(
                        continue_on_failure
                    ),
                )
            )

            if result.get(
                "success",
                False,
            ):
                st.success(
                    "Controlled dispatch completed."
                )
            else:
                st.error(
                    "Controlled dispatch reported failure."
                )

            st.json({
                "approval_id": result.get(
                    "approval_id",
                    "",
                ),
                "run_id": result.get(
                    "run_id",
                    "",
                ),
                "approved_job_ids": (
                    result.get(
                        "approved_job_ids",
                        [],
                    )
                ),
            })

        except Exception as error:
            st.error(str(error))


def render_reconcile_control() -> None:
    st.write(
        "Reconciliation is read-only. It verifies "
        "scope, provenance, and post-dispatch health."
    )

    confirmed = st.checkbox(
        "I understand reconciliation does not execute jobs.",
        value=False,
        key="reconcile_confirmation",
    )

    if st.button(
        "Reconcile latest guarded dispatch",
        disabled=not confirmed,
    ):
        try:
            report = (
                reconcile_guarded_dispatch()
            )

            outcome = str(
                report.get(
                    "outcome",
                    "UNKNOWN",
                )
            )

            if outcome in {
                "RECONCILED",
                "PARTIALLY_REPAIRED",
                "NO_PROGRESS",
            }:
                st.success(
                    "Reconciliation completed: "
                    + outcome
                )
            else:
                st.error(
                    "Reconciliation completed: "
                    + outcome
                )

            st.write(
                report.get(
                    "summary",
                    "",
                )
            )

        except Exception as error:
            st.error(str(error))


def render_preflight_summary(
    preflight: dict[str, Any],
) -> None:
    status = str(
        preflight.get(
            "status",
            "UNKNOWN",
        )
    )

    icon = STATUS_ICON.get(
        status,
        "?",
    )

    st.markdown(
        f"### {icon} Preflight: {status}"
    )

    st.write(
        preflight.get(
            "reason",
            "",
        )
    )

    counts = preflight.get(
        "counts",
        {},
    )

    if counts:
        columns = st.columns(4)

        metric(
            columns[0],
            "Eligible",
            counts.get(
                "eligible_steps",
                0,
            ),
        )

        metric(
            columns[1],
            "Pruned Current",
            counts.get(
                "pruned_current_jobs",
                0,
            ),
        )

        metric(
            columns[2],
            "Blocked",
            counts.get(
                "blocked_jobs",
                0,
            ),
        )

        metric(
            columns[3],
            "Unknown",
            counts.get(
                "unknown_jobs",
                0,
            ),
        )

    with st.expander(
        "Preflight details",
        expanded=False,
    ):
        safe = {
            key: value
            for key, value
            in preflight.items()
            if key not in {
                "effective_plan",
                "eligible_steps",
            }
        }

        st.json(safe)



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
