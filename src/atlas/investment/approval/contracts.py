"""Canonical approval contracts for Atlas G.20."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


SCHEMA_VERSION = "g20.execution_approval.v1"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class OrderPreview:
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    limit_price: float | None = None
    stop_price: float | None = None
    time_in_force: str = "DAY"
    paper_only: bool = True
    live_execution: bool = False


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    decision_id: str
    orchestration_run_id: str
    portfolio_id: str
    risk_report_id: str
    intent_ids: tuple[str, ...]
    order_previews: tuple[OrderPreview, ...]
    requested_at: str
    expires_at: str
    status: ApprovalStatus
    approver_identity_reference: str | None
    approval_hash: str
    previous_record_hash: str
    plan_hash: str
    paper_only: bool = True
    live_execution: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    status: ApprovalStatus
    decided_at: str
    approver_identity_reference: str
    reason: str
    approval_hash: str
    previous_record_hash: str
    plan_hash: str
    paper_only: bool = True
    live_execution: bool = False


__all__ = [
    "SCHEMA_VERSION",
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalStatus",
    "OrderPreview",
]
