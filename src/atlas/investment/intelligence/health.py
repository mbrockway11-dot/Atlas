
"""Portfolio-system health checks."""

from __future__ import annotations


def build_health_checks(inputs: dict) -> list[dict]:
    ledger = inputs.get("broker_ledger", {}) or {}
    mtm = inputs.get("mark_to_market", {}) or {}
    portfolio = inputs.get("portfolio_state", {}) or {}
    performance = inputs.get("performance", {}) or {}
    learning = inputs.get("learning", {}) or {}
    risk = inputs.get("risk", {}) or {}
    safety = inputs.get("safety", {}) or {}
    core = inputs.get("core", {}) or {}

    reconciliation = ledger.get("reconciliation", {}) or {}

    checks = [
        check(
            "accounting_reconciliation",
            reconciliation.get("balanced") is True,
            "Broker Ledger is mathematically reconciled.",
            "Broker Ledger is not reconciled.",
        ),
        check(
            "mark_to_market",
            mtm.get("success") is True,
            "Mark-to-Market v4 is healthy.",
            "Mark-to-Market v4 is unavailable or failed.",
        ),
        check(
            "portfolio_state",
            portfolio.get("success") is True,
            "Portfolio State is available.",
            "Portfolio State is unavailable or failed.",
        ),
        check(
            "performance",
            performance.get("success") is True,
            "Performance Engine is healthy.",
            "Performance Engine failed.",
        ),
        check(
            "learning",
            learning.get("success") is True,
            "Learning Engine is healthy.",
            "Learning Engine failed.",
        ),
        check(
            "risk",
            risk.get("success") is True,
            "Risk Engine is healthy.",
            "Risk Engine failed.",
        ),
        check_safety(safety),
        check_core(core),
    ]

    return checks


def summarize_health(checks: list[dict]) -> dict:
    pass_count = sum(
        1 for row in checks
        if row.get("status") == "PASS"
    )
    warn_count = sum(
        1 for row in checks
        if row.get("status") == "WARN"
    )
    fail_count = sum(
        1 for row in checks
        if row.get("status") == "FAIL"
    )

    if fail_count:
        label = "CRITICAL"
    elif warn_count:
        label = "HEALTHY_WITH_WARNINGS"
    else:
        label = "HEALTHY"

    return {
        "health_label": label,
        "check_count": len(checks),
        "pass_count": pass_count,
        "warning_count": warn_count,
        "failure_count": fail_count,
        "healthy": fail_count == 0,
    }


def check(
    name: str,
    condition: bool,
    pass_message: str,
    fail_message: str,
) -> dict:
    return {
        "name": name,
        "status": "PASS" if condition else "FAIL",
        "message": pass_message if condition else fail_message,
    }


def check_safety(safety: dict) -> dict:
    status = str(safety.get("status") or "UNKNOWN").upper()

    if status == "REJECTED":
        return {
            "name": "trade_safety",
            "status": "WARN",
            "message": (
                "Safety Governor currently blocks execution. "
                "Capital remains protected."
            ),
        }

    if status == "APPROVED_WITH_WARNINGS":
        return {
            "name": "trade_safety",
            "status": "WARN",
            "message": "Safety Governor approved with warnings.",
        }

    return {
        "name": "trade_safety",
        "status": "PASS",
        "message": f"Safety Governor status: {status}.",
    }


def check_core(core: dict) -> dict:
    success = core.get("success") is True

    nodes = (
        core.get("nodes")
        or core.get("node_results")
        or []
    )

    failed_nodes = [
        row.get("name")
        for row in nodes
        if isinstance(row, dict)
        and row.get("success") is False
    ]

    return {
        "name": "atlas_core",
        "status": "PASS" if success and not failed_nodes else "FAIL",
        "message": (
            "Atlas Core completed successfully."
            if success and not failed_nodes
            else f"Atlas Core failed nodes: {failed_nodes}."
        ),
    }
