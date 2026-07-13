"""Read-only Atlas paper execution dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.investment.execution.dashboard import (
    build_paper_execution_dashboard_model,
)


STATUS_ICON = {
    "HEALTHY": "??",
    "ATTENTION": "??",
    "DEGRADED": "??",
    "CRITICAL": "??",
}


def render_paper_execution_page() -> None:
    st.title("Paper Execution")

    st.caption(
        "Broker-neutral paper trading observatory. "
        "Read only. No order submission or live credentials."
    )

    model = (
        build_paper_execution_dashboard_model()
    )

    render_header(model)
    render_safety(model)
    render_portfolio_plan(model)
    render_latest_execution(model)
    render_account(model)
    render_lifecycle(model)
    render_history(model)
    render_paths(model)


def render_header(
    model: dict[str, Any],
) -> None:
    status = str(
        model.get(
            "status",
            "UNKNOWN",
        )
    )

    icon = STATUS_ICON.get(
        status,
        "?",
    )

    st.subheader(
        f"{icon} Execution Status: {status}"
    )

    st.write(
        model.get(
            "summary",
            "",
        )
    )

    plan = model.get(
        "intent_plan",
        {},
    )

    execution = model.get(
        "latest_execution",
        {},
    )

    lifecycle = model.get(
        "lifecycle",
        {},
    )

    columns = st.columns(4)

    columns[0].metric(
        "Generated Intents",
        plan.get(
            "counts",
            {},
        ).get(
            "generated_intents",
            0,
        ),
    )

    columns[1].metric(
        "Latest Fills",
        len(
            execution.get(
                "fills",
                [],
            )
        ),
    )

    columns[2].metric(
        "Open Orders",
        lifecycle.get(
            "open_order_count",
            0,
        ),
    )

    columns[3].metric(
        "Lifecycle Chain",
        (
            "VALID"
            if lifecycle.get(
                "chain_valid",
                False,
            )
            else "INVALID"
        ),
    )


def render_safety(
    model: dict[str, Any],
) -> None:
    st.subheader(
        "Execution Safety Contract"
    )

    safety = model.get(
        "safety",
        {},
    )

    columns = st.columns(4)

    columns[0].metric(
        "Mode",
        "PAPER",
    )

    columns[1].metric(
        "Live Execution",
        str(
            safety.get(
                "live_execution",
                False,
            )
        ),
    )

    columns[2].metric(
        "Credentials Used",
        str(
            safety.get(
                "live_credentials_used",
                False,
            )
        ),
    )

    columns[3].metric(
        "Broker Neutral",
        str(
            safety.get(
                "broker_neutral",
                True,
            )
        ),
    )

    if (
        safety.get(
            "live_execution",
            False,
        )
        or safety.get(
            "live_credentials_used",
            False,
        )
    ):
        st.error(
            "Paper execution safety contract has been violated."
        )
    else:
        st.success(
            "Paper-only execution boundary is intact."
        )

    with st.expander(
        "Safety details",
        expanded=False,
    ):
        st.json(safety)


def render_portfolio_plan(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader(
        "Portfolio Intent Plan"
    )

    plan = model.get(
        "intent_plan",
        {},
    )

    if not plan.get(
        "exists",
        False,
    ):
        st.info(
            "No portfolio intent plan is available."
        )
        return

    columns = st.columns(4)

    columns[0].metric(
        "Account Equity",
        money(
            plan.get(
                "account_equity",
                0.0,
            )
        ),
    )

    columns[1].metric(
        "Target Invested",
        percent(
            plan.get(
                "target_weight_total",
                0.0,
            )
        ),
    )

    columns[2].metric(
        "Turnover",
        percent(
            plan.get(
                "total_turnover_weight",
                0.0,
            )
        ),
    )

    columns[3].metric(
        "Cash Buffer",
        percent(
            plan.get(
                "minimum_cash_weight",
                0.0,
            )
        ),
    )

    st.caption(
        "Plan ID: "
        + str(
            plan.get(
                "plan_id",
                "",
            )
        )
    )

    tabs = st.tabs([
        "Targets",
        "Rebalance Lines",
        "Order Intents",
    ])

    with tabs[0]:
        render_table(
            plan.get(
                "targets",
                [],
            )
        )

    with tabs[1]:
        render_table(
            plan.get(
                "rebalance_lines",
                [],
            )
        )

    with tabs[2]:
        render_table(
            plan.get(
                "intents",
                [],
            )
        )


def render_latest_execution(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader(
        "Latest Paper Execution"
    )

    execution = model.get(
        "latest_execution",
        {},
    )

    if not execution.get(
        "exists",
        False,
    ):
        st.info(
            "No paper execution report is available."
        )
        return

    risk = execution.get(
        "risk",
        {},
    )

    order = execution.get(
        "order",
        {},
    )

    columns = st.columns(4)

    columns[0].metric(
        "Risk Approved",
        str(
            risk.get(
                "approved",
                False,
            )
        ),
    )

    columns[1].metric(
        "Order Status",
        str(
            order.get(
                "status",
                "UNKNOWN",
            )
        ),
    )

    columns[2].metric(
        "Filled Quantity",
        order.get(
            "filled_quantity",
            0.0,
        ),
    )

    columns[3].metric(
        "Fees",
        money(
            order.get(
                "fee_paid",
                0.0,
            )
        ),
    )

    if not risk.get(
        "approved",
        False,
    ):
        reasons = risk.get(
            "reason_codes",
            [],
        )

        st.warning(
            "Risk rejection: "
            + (
                ", ".join(
                    str(value)
                    for value in reasons
                )
                or "unspecified"
            )
        )

    with st.expander(
        "Intent",
        expanded=False,
    ):
        st.json(
            execution.get(
                "intent",
                {},
            )
        )

    with st.expander(
        "Risk decision",
        expanded=False,
    ):
        st.json(risk)

    with st.expander(
        "Order",
        expanded=True,
    ):
        st.json(order)

    st.write("**Fills**")

    render_table(
        execution.get(
            "fills",
            [],
        )
    )


def render_account(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader(
        "Paper Account"
    )

    execution = model.get(
        "latest_execution",
        {},
    )

    account = execution.get(
        "account_after",
        {},
    )

    if not account:
        st.info(
            "No paper account snapshot is available."
        )
        return

    columns = st.columns(5)

    columns[0].metric(
        "Cash",
        money(
            account.get(
                "cash",
                0.0,
            )
        ),
    )

    columns[1].metric(
        "Net Liquidation",
        money(
            account.get(
                "net_liquidation_value",
                0.0,
            )
        ),
    )

    columns[2].metric(
        "Gross Exposure",
        money(
            account.get(
                "gross_exposure",
                0.0,
            )
        ),
    )

    columns[3].metric(
        "Realized P&L",
        money(
            account.get(
                "realized_pnl",
                0.0,
            )
        ),
    )

    columns[4].metric(
        "Daily P&L",
        money(
            account.get(
                "daily_pnl",
                0.0,
            )
        ),
    )

    st.write("**Positions**")

    render_table(
        execution.get(
            "positions",
            [],
        )
    )


def render_lifecycle(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader(
        "Order Lifecycle"
    )

    lifecycle = model.get(
        "lifecycle",
        {},
    )

    columns = st.columns(4)

    columns[0].metric(
        "Tracked Orders",
        lifecycle.get(
            "record_count",
            0,
        ),
    )

    columns[1].metric(
        "Open Orders",
        lifecycle.get(
            "open_order_count",
            0,
        ),
    )

    columns[2].metric(
        "Terminal Orders",
        lifecycle.get(
            "terminal_order_count",
            0,
        ),
    )

    columns[3].metric(
        "Transitions",
        lifecycle.get(
            "transition_count",
            0,
        ),
    )

    if lifecycle.get(
        "chain_valid",
        False,
    ):
        st.success(
            "Lifecycle transition chain is valid."
        )
    else:
        st.error(
            "Lifecycle transition chain is invalid."
        )

        for error in lifecycle.get(
            "chain_errors",
            [],
        ):
            st.write(
                "- " + str(error)
            )

    tabs = st.tabs([
        "All Orders",
        "Open Orders",
        "Transitions",
    ])

    with tabs[0]:
        render_table(
            lifecycle.get(
                "records",
                [],
            )
        )

    with tabs[1]:
        render_table(
            lifecycle.get(
                "open_orders",
                [],
            )
        )

    with tabs[2]:
        render_table(
            lifecycle.get(
                "transitions",
                [],
            )
        )


def render_history(
    model: dict[str, Any],
) -> None:
    st.divider()
    st.subheader(
        "Execution History"
    )

    history = model.get(
        "execution_history",
        {},
    )

    st.caption(
        "Events: "
        + str(
            history.get(
                "event_count",
                0,
            )
        )
    )

    render_table(
        history.get(
            "events",
            [],
        )
    )


def render_paths(
    model: dict[str, Any],
) -> None:
    with st.expander(
        "Runtime artifact paths",
        expanded=False,
    ):
        st.json(
            model.get(
                "paths",
                {},
            )
        )


def render_table(
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        st.info(
            "No records are available."
        )
        return

    frame = pd.DataFrame(
        rows
    )

    st.dataframe(
        frame,
        width="stretch",
        hide_index=True,
    )


def money(
    value: Any,
) -> str:
    try:
        return (
            f"${float(value):,.2f}"
        )
    except (
        TypeError,
        ValueError,
    ):
        return "$0.00"


def percent(
    value: Any,
) -> str:
    try:
        return (
            f"{float(value) * 100:.2f}%"
        )
    except (
        TypeError,
        ValueError,
    ):
        return "0.00%"


if __name__ == "__main__":
    render_paper_execution_page()
