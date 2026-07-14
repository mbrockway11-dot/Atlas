from __future__ import annotations

from pathlib import Path

from atlas.investment.approval import (
    ApprovalService,
    ApprovalStatus,
    OrderPreview,
    read_history,
    validate_history,
)


def preview() -> OrderPreview:
    return OrderPreview(
        client_order_id="client-1",
        symbol="BTC-USD",
        side="BUY",
        order_type="LIMIT",
        quantity=0.1,
        limit_price=50000,
    )


def test_create_and_approve_request(tmp_path: Path) -> None:
    service = ApprovalService(output_dir=tmp_path)
    request = service.create_request(
        decision_id="decision-1",
        orchestration_run_id="run-1",
        portfolio_id="portfolio-1",
        risk_report_id="risk-1",
        intent_ids=("intent-1",),
        order_previews=(preview(),),
    )

    decision = service.decide(
        approval_id=request.approval_id,
        approve=True,
        approver_identity_reference="user:test",
        expected_plan_hash=request.plan_hash,
        reason="approved for paper execution",
    )

    assert request.status == ApprovalStatus.PENDING
    assert decision.status == ApprovalStatus.APPROVED
    assert decision.paper_only is True
    assert decision.live_execution is False

    history = read_history(tmp_path / "approval_history.jsonl")
    validate_history(history)
    assert len(history) == 2
