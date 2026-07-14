from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from atlas.investment.approval import (
    ApprovalError,
    ApprovalService,
    OrderPreview,
)


def test_expired_request_cannot_be_approved(tmp_path: Path) -> None:
    service = ApprovalService(output_dir=tmp_path)
    request = service.create_request(
        decision_id="decision-expired",
        orchestration_run_id="run-expired",
        portfolio_id="portfolio",
        risk_report_id="risk",
        intent_ids=("intent",),
        order_previews=(
            OrderPreview(
                client_order_id="client-expired",
                symbol="SOL-USD",
                side="BUY",
                order_type="MARKET",
                quantity=1,
            ),
        ),
        expires_in_minutes=1,
    )

    future = datetime.now(timezone.utc) + timedelta(minutes=2)

    with pytest.raises(ApprovalError, match="expired"):
        service.decide(
            approval_id=request.approval_id,
            approve=True,
            approver_identity_reference="user:test",
            expected_plan_hash=request.plan_hash,
            now=future,
        )
