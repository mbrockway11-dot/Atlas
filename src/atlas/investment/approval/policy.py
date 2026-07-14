"""Approval policy validation for Atlas G.20."""

from __future__ import annotations

from datetime import datetime, timezone

from .contracts import ApprovalRequest, ApprovalStatus
from .service import ApprovalError


def parse_timestamp(value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ApprovalError(f"Invalid ISO timestamp: {value}") from exc
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def assert_request_is_actionable(
    request: ApprovalRequest,
    *,
    expected_plan_hash: str,
    now: datetime | None = None,
) -> None:
    current = now or datetime.now(timezone.utc)

    if request.status != ApprovalStatus.PENDING:
        raise ApprovalError(
            f"Approval request is not pending: {request.status.value}"
        )
    if request.plan_hash != expected_plan_hash:
        raise ApprovalError("Approval request plan hash does not match current plan")
    if not request.paper_only or request.live_execution:
        raise ApprovalError("Approval request violates the paper-only boundary")
    if parse_timestamp(request.expires_at) <= current:
        raise ApprovalError("Approval request has expired")
    if not request.order_previews:
        raise ApprovalError("Approval request has no order previews")
    if any(
        not preview.paper_only or preview.live_execution
        for preview in request.order_previews
    ):
        raise ApprovalError("Order preview violates the paper-only boundary")


__all__ = ["assert_request_is_actionable", "parse_timestamp"]
