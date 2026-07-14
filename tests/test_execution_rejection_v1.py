from __future__ import annotations

from pathlib import Path

from atlas.investment.approval import (
    ApprovalService,
    ApprovalStatus,
    OrderPreview,
)


def test_reject_request(tmp_path: Path) -> None:
    service = ApprovalService(output_dir=tmp_path)
    request = service.create_request(
        decision_id="decision-reject",
        orchestration_run_id="run-reject",
        portfolio_id="portfolio",
        risk_report_id="risk",
        intent_ids=("intent",),
        order_previews=(
            OrderPreview(
                client_order_id="client-reject",
                symbol="ETH-USD",
                side="SELL",
                order_type="MARKET",
                quantity=1,
            ),
        ),
    )

    decision = service.decide(
        approval_id=request.approval_id,
        approve=False,
        approver_identity_reference="user:reviewer",
        expected_plan_hash=request.plan_hash,
        reason="risk review rejected",
    )

    assert decision.status == ApprovalStatus.REJECTED
    assert decision.reason == "risk review rejected"
