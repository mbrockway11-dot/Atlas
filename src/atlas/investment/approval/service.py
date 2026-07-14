"""Supervised execution approval service for Atlas G.20."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .contracts import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    OrderPreview,
    SCHEMA_VERSION,
)
from .persistence import (
    append_history,
    atomic_write_json,
    compute_hash,
    read_history,
    validate_history,
)


class ApprovalError(RuntimeError):
    """Approval validation or state transition failure."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def canonical_plan_hash(
    *,
    decision_id: str,
    orchestration_run_id: str,
    portfolio_id: str,
    risk_report_id: str,
    intent_ids: Iterable[str],
    order_previews: Iterable[OrderPreview],
) -> str:
    payload = {
        "decision_id": decision_id,
        "orchestration_run_id": orchestration_run_id,
        "portfolio_id": portfolio_id,
        "risk_report_id": risk_report_id,
        "intent_ids": sorted(str(item) for item in intent_ids),
        "order_previews": [asdict(item) for item in order_previews],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _next_approval_id() -> str:
    return f"approval-{secrets.token_hex(10)}"


def _latest_record_for(
    history: list[dict[str, Any]],
    approval_id: str,
) -> dict[str, Any] | None:
    for record in reversed(history):
        if record.get("approval_id") == approval_id:
            return record
    return None


class ApprovalService:
    def __init__(self, *, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.latest_path = output_dir / "latest_approval.json"
        self.history_path = output_dir / "approval_history.jsonl"

    def create_request(
        self,
        *,
        decision_id: str,
        orchestration_run_id: str,
        portfolio_id: str,
        risk_report_id: str,
        intent_ids: Iterable[str],
        order_previews: Iterable[OrderPreview],
        expires_in_minutes: int = 30,
        metadata: Mapping[str, Any] | None = None,
    ) -> ApprovalRequest:
        previews = tuple(order_previews)
        intents = tuple(str(item) for item in intent_ids)

        if not decision_id.strip():
            raise ApprovalError("decision_id is required")
        if not orchestration_run_id.strip():
            raise ApprovalError("orchestration_run_id is required")
        if not portfolio_id.strip():
            raise ApprovalError("portfolio_id is required")
        if not risk_report_id.strip():
            raise ApprovalError("risk_report_id is required")
        if not intents:
            raise ApprovalError("At least one intent_id is required")
        if not previews:
            raise ApprovalError("At least one order preview is required")
        if expires_in_minutes < 1 or expires_in_minutes > 1440:
            raise ApprovalError("expires_in_minutes must be between 1 and 1440")
        if any(
            not preview.paper_only or preview.live_execution
            for preview in previews
        ):
            raise ApprovalError("Order previews must remain paper-only")

        history = read_history(self.history_path)
        validate_history(history)
        previous_hash = history[-1]["approval_hash"] if history else ""

        requested_at = utc_now()
        expires_at = requested_at + timedelta(minutes=expires_in_minutes)
        plan_hash = canonical_plan_hash(
            decision_id=decision_id,
            orchestration_run_id=orchestration_run_id,
            portfolio_id=portfolio_id,
            risk_report_id=risk_report_id,
            intent_ids=intents,
            order_previews=previews,
        )

        request = ApprovalRequest(
            approval_id=_next_approval_id(),
            decision_id=decision_id,
            orchestration_run_id=orchestration_run_id,
            portfolio_id=portfolio_id,
            risk_report_id=risk_report_id,
            intent_ids=intents,
            order_previews=previews,
            requested_at=iso(requested_at),
            expires_at=iso(expires_at),
            status=ApprovalStatus.PENDING,
            approver_identity_reference=None,
            approval_hash="",
            previous_record_hash=previous_hash,
            plan_hash=plan_hash,
            paper_only=True,
            live_execution=False,
            metadata=dict(metadata or {}),
        )
        payload = asdict(request)
        payload["approval_hash"] = compute_hash(payload)
        request = replace(request, approval_hash=payload["approval_hash"])

        atomic_write_json(self.latest_path, asdict(request))
        append_history(self.history_path, asdict(request))
        return request

    def decide(
        self,
        *,
        approval_id: str,
        approve: bool,
        approver_identity_reference: str,
        expected_plan_hash: str,
        reason: str = "",
        now: datetime | None = None,
    ) -> ApprovalDecision:
        from .policy import assert_request_is_actionable

        history = read_history(self.history_path)
        validate_history(history)
        current = _latest_record_for(history, approval_id)
        if current is None:
            raise ApprovalError(f"Approval request not found: {approval_id}")

        current_status = ApprovalStatus(str(current.get("status", "")))
        if current_status != ApprovalStatus.PENDING:
            raise ApprovalError(
                f"Approval request is not pending: {current_status.value}"
            )

        request = ApprovalRequest(
            approval_id=str(current["approval_id"]),
            decision_id=str(current["decision_id"]),
            orchestration_run_id=str(current["orchestration_run_id"]),
            portfolio_id=str(current["portfolio_id"]),
            risk_report_id=str(current["risk_report_id"]),
            intent_ids=tuple(current["intent_ids"]),
            order_previews=tuple(
                OrderPreview(**item) for item in current["order_previews"]
            ),
            requested_at=str(current["requested_at"]),
            expires_at=str(current["expires_at"]),
            status=ApprovalStatus(str(current["status"])),
            approver_identity_reference=current.get("approver_identity_reference"),
            approval_hash=str(current["approval_hash"]),
            previous_record_hash=str(current["previous_record_hash"]),
            plan_hash=str(current["plan_hash"]),
            paper_only=bool(current.get("paper_only", True)),
            live_execution=bool(current.get("live_execution", False)),
            metadata=dict(current.get("metadata", {})),
        )

        assert_request_is_actionable(
            request,
            expected_plan_hash=expected_plan_hash,
            now=now,
        )
        if not approver_identity_reference.strip():
            raise ApprovalError("approver_identity_reference is required")

        status = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        decided_at = iso(now or utc_now())
        decision = ApprovalDecision(
            approval_id=approval_id,
            status=status,
            decided_at=decided_at,
            approver_identity_reference=approver_identity_reference,
            reason=reason,
            approval_hash="",
            previous_record_hash=history[-1]["approval_hash"],
            plan_hash=request.plan_hash,
            paper_only=True,
            live_execution=False,
        )
        payload = asdict(decision)
        payload["approval_hash"] = compute_hash(payload)
        decision = replace(decision, approval_hash=payload["approval_hash"])

        atomic_write_json(self.latest_path, asdict(decision))
        append_history(self.history_path, asdict(decision))
        return decision


__all__ = [
    "ApprovalError",
    "ApprovalService",
    "canonical_plan_hash",
]
