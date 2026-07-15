from __future__ import annotations

from atlas.investment.execution.contracts import (
    AccountSnapshot,
)
from atlas.investment.execution_bridge import (
    execute_lyfe_instruction,
)
from atlas.investment.lyfe_bridge.contracts import (
    AtlasStrategyInstruction,
)


def instruction(
    *,
    action: str = "ENTER",
    direction: str = "LONG",
    exposure: float = 0.10,
) -> AtlasStrategyInstruction:
    return AtlasStrategyInstruction(
        instruction_id="atlas:test-decision-001",
        source_system="LYFE",
        strategy_id="v32_ab",
        strategy_version="32.0",
        signal_timestamp_utc=(
            "2026-07-15T00:00:00+00:00"
        ),
        asset="SOL",
        action=action,
        direction=direction,
        requested_exposure=exposure,
        confidence=0.80,
        rationale="Execution Bridge V1 test",
        requires_human_approval=True,
        research_only=True,
        source_decision_sha256="a" * 64,
        source_commit="test-commit",
        dataset_hash="b" * 64,
        metadata={},
    )


def account() -> AccountSnapshot:
    return AccountSnapshot(
        cash=10_000.0,
        positions={},
    )


def test_blocks_generated_order_without_human_approval() -> None:
    report = execute_lyfe_instruction(
        instruction(),
        reference_price=100.0,
        account=account(),
        provider="paper",
        human_approved=False,
        write_outputs=False,
    )

    assert report["success"] is False
    assert report["execution_blocked"] is True
    assert report["status"] == "AWAITING_HUMAN_APPROVAL"
    assert report["counts"]["generated_intents"] == 1
    assert report["execution_results"] == []


def test_runs_complete_paper_execution_pipeline() -> None:
    report = execute_lyfe_instruction(
        instruction(),
        reference_price=100.0,
        account=account(),
        provider="paper",
        human_approved=True,
        write_outputs=False,
    )

    assert report["success"] is True
    assert report["status"] == "COMPLETED"
    assert report["execution_blocked"] is False
    assert report["provider"] == "paper"
    assert report["counts"]["generated_intents"] == 1
    assert report["counts"]["successful_executions"] == 1

    execution = report["execution_results"][0]

    assert execution["provider"] == "paper"
    assert execution["risk"]["approved"] is True
    assert execution["order"]["status"] in {
        "FILLED",
        "PARTIALLY_FILLED",
    }

    assert (
        report["account_after"]["cash"]
        < report["account_before"]["cash"]
    )


def test_no_action_returns_safe_noop() -> None:
    report = execute_lyfe_instruction(
        instruction(
            action="NO_ACTION",
            direction="FLAT",
            exposure=0.0,
        ),
        reference_price=100.0,
        account=account(),
        provider="paper",
        human_approved=False,
        write_outputs=False,
    )

    assert report["success"] is True
    assert report["execution_blocked"] is True
    assert report["status"] == "NO_PORTFOLIO_CHANGE"
    assert report["counts"]["generated_intents"] == 0


def test_registered_mock_broker_route() -> None:
    report = execute_lyfe_instruction(
        instruction(),
        reference_price=100.0,
        account=account(),
        provider="mock",
        human_approved=True,
        broker_kwargs={
            "starting_cash": 10_000.0,
        },
        write_outputs=False,
    )

    assert report["success"] is True
    assert report["provider"] == "mock"
    assert report["counts"]["successful_executions"] == 1

    execution = report["execution_results"][0]

    assert execution["status"] == "SUBMITTED"
    assert (
        execution["broker_response"]["status"]
        == "ACCEPTED"
    )
    assert (
        execution["broker_response"]["live_execution"]
        is False
    )
