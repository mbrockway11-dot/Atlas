from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment.approval import (
    ApprovalError,
    ApprovalService,
    OrderPreview,
)


def safe_preview() -> OrderPreview:
    return OrderPreview(
        client_order_id="client-safe",
        symbol="BTC-USD",
        side="BUY",
        order_type="MARKET",
        quantity=1,
    )


def test_modified_plan_hash_cannot_be_approved(tmp_path: Path) -> None:
    service = ApprovalService(output_dir=tmp_path)
    request = service.create_request(
        decision_id="decision",
        orchestration_run_id="run",
        portfolio_id="portfolio",
        risk_report_id="risk",
        intent_ids=("intent",),
        order_previews=(safe_preview(),),
    )

    with pytest.raises(ApprovalError, match="plan hash"):
        service.decide(
            approval_id=request.approval_id,
            approve=True,
            approver_identity_reference="user:test",
            expected_plan_hash="tampered",
        )


def test_approval_cannot_be_reused(tmp_path: Path) -> None:
    service = ApprovalService(output_dir=tmp_path)
    request = service.create_request(
        decision_id="decision-reuse",
        orchestration_run_id="run-reuse",
        portfolio_id="portfolio",
        risk_report_id="risk",
        intent_ids=("intent",),
        order_previews=(safe_preview(),),
    )

    service.decide(
        approval_id=request.approval_id,
        approve=True,
        approver_identity_reference="user:test",
        expected_plan_hash=request.plan_hash,
    )

    with pytest.raises(ApprovalError, match="not pending"):
        service.decide(
            approval_id=request.approval_id,
            approve=True,
            approver_identity_reference="user:test",
            expected_plan_hash=request.plan_hash,
        )


def test_live_order_preview_is_rejected(tmp_path: Path) -> None:
    service = ApprovalService(output_dir=tmp_path)

    with pytest.raises(ApprovalError, match="paper-only"):
        service.create_request(
            decision_id="decision-live",
            orchestration_run_id="run-live",
            portfolio_id="portfolio",
            risk_report_id="risk",
            intent_ids=("intent",),
            order_previews=(
                OrderPreview(
                    client_order_id="client-live",
                    symbol="BTC-USD",
                    side="BUY",
                    order_type="MARKET",
                    quantity=1,
                    paper_only=False,
                    live_execution=True,
                ),
            ),
        )


def test_unsigned_approver_is_rejected(tmp_path: Path) -> None:
    service = ApprovalService(output_dir=tmp_path)
    request = service.create_request(
        decision_id="decision-signature",
        orchestration_run_id="run-signature",
        portfolio_id="portfolio",
        risk_report_id="risk",
        intent_ids=("intent",),
        order_previews=(safe_preview(),),
    )

    with pytest.raises(ApprovalError, match="approver_identity_reference"):
        service.decide(
            approval_id=request.approval_id,
            approve=True,
            approver_identity_reference="",
            expected_plan_hash=request.plan_hash,
        )
