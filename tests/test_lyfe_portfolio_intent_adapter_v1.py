from __future__ import annotations

import pytest

from atlas.investment.execution.contracts import (
    AccountSnapshot,
)
from atlas.investment.execution.portfolio_bridge import (
    RebalancePolicy,
)
from atlas.investment.lyfe_bridge.contracts import (
    AtlasStrategyInstruction,
)
from atlas.investment.lyfe_bridge.portfolio_intent import (
    build_lyfe_portfolio_intent_plan,
    map_lyfe_instruction_to_target,
)


def _instruction(
    *,
    action: str = "ENTER",
    direction: str = "LONG",
    exposure: float = 0.25,
    asset: str = "SOL",
) -> AtlasStrategyInstruction:
    return AtlasStrategyInstruction(
        instruction_id="atlas:test-decision",
        source_system="LYFE",
        strategy_id="V32_AB",
        strategy_version="32.0.0",
        signal_timestamp_utc=(
            "2026-07-14T00:00:00+00:00"
        ),
        asset=asset,
        action=action,
        direction=direction,
        requested_exposure=exposure,
        confidence=0.82,
        rationale="Test decision.",
        requires_human_approval=True,
        research_only=True,
        source_decision_sha256=(
            "a" * 64
        ),
    )


def test_long_instruction_maps_to_target() -> None:
    mapping = map_lyfe_instruction_to_target(
        _instruction(),
        reference_price=150.0,
    )

    assert mapping.executable is True
    assert mapping.status == "LONG_TARGET_READY"
    assert mapping.target is not None
    assert mapping.target.asset == "SOL-USD"
    assert mapping.target.target_weight == 0.25


def test_no_action_does_not_flatten_portfolio() -> None:
    mapping = map_lyfe_instruction_to_target(
        _instruction(
            action="NO_ACTION",
            direction="FLAT",
            exposure=0.0,
        ),
        reference_price=150.0,
    )

    assert mapping.executable is False
    assert mapping.status == "NO_PORTFOLIO_CHANGE"
    assert mapping.target is None


def test_short_instruction_is_deferred() -> None:
    mapping = map_lyfe_instruction_to_target(
        _instruction(
            action="ENTER",
            direction="SHORT",
            exposure=0.20,
        ),
        reference_price=150.0,
    )

    assert mapping.executable is False
    assert mapping.status == "SHORT_DEFERRED"
    assert mapping.target is None


def test_exit_maps_to_zero_target() -> None:
    mapping = map_lyfe_instruction_to_target(
        _instruction(
            action="EXIT",
            direction="LONG",
            exposure=0.0,
        ),
        reference_price=150.0,
    )

    assert mapping.executable is True
    assert mapping.status == "EXIT_TARGET_READY"
    assert mapping.target is not None
    assert mapping.target.target_weight == 0.0


def test_long_instruction_uses_existing_portfolio_bridge() -> None:
    plan = build_lyfe_portfolio_intent_plan(
        _instruction(),
        reference_price=150.0,
        account=AccountSnapshot(
            cash=10_000.0
        ),
        policy=RebalancePolicy(
            minimum_order_notional=25.0,
            maximum_order_notional=5_000.0,
            maximum_total_turnover=1.0,
            minimum_cash_weight=0.50,
        ),
        write_output=False,
    )

    assert plan["execution_blocked"] is False
    assert plan["lyfe_mapping"]["status"] == (
        "LONG_TARGET_READY"
    )
    assert len(plan["intents"]) == 1
    assert plan["intents"][0]["asset"] == "SOL-USD"
    assert plan["intents"][0]["side"] == "BUY"


def test_short_instruction_produces_no_intents() -> None:
    plan = build_lyfe_portfolio_intent_plan(
        _instruction(
            action="ENTER",
            direction="SHORT",
            exposure=0.20,
        ),
        reference_price=150.0,
        account=AccountSnapshot(
            cash=10_000.0
        ),
        write_output=False,
    )

    assert plan["execution_blocked"] is True
    assert plan["mapping"]["status"] == "SHORT_DEFERRED"
    assert plan["intents"] == []


def test_invalid_reference_price_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="reference_price",
    ):
        map_lyfe_instruction_to_target(
            _instruction(),
            reference_price=0.0,
        )
