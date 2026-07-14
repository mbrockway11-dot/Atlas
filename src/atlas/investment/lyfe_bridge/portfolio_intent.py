"""
LYFE-to-Atlas portfolio intent adapter.

Maps validated LYFE strategy instructions into Atlas's existing
long-only PortfolioTarget and portfolio-intent infrastructure.

This module does not submit orders.

Mapping rules:
- NO_ACTION: no portfolio change
- ENTER/HOLD/REDUCE LONG: long target weight
- EXIT: zero target weight
- SHORT: retained as a deferred research observation
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from atlas.investment.execution.contracts import (
    AccountSnapshot,
)
from atlas.investment.execution.portfolio_bridge import (
    PortfolioTarget,
    RebalancePolicy,
    build_portfolio_intent_plan,
)

from .contracts import (
    AtlasStrategyInstruction,
)


@dataclass(frozen=True, slots=True)
class LyfePortfolioMapping:
    instruction_id: str
    status: str
    executable: bool
    reason: str
    target: PortfolioTarget | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instruction_id":
                self.instruction_id,
            "status":
                self.status,
            "executable":
                self.executable,
            "reason":
                self.reason,
            "target": (
                self.target.to_dict()
                if self.target is not None
                else None
            ),
        }


def _validate_reference_price(
    reference_price: float,
) -> float:
    price = float(
        reference_price
    )

    if (
        not math.isfinite(price)
        or price <= 0.0
    ):
        raise ValueError(
            "reference_price must be positive and finite."
        )

    return price


def map_lyfe_instruction_to_target(
    instruction: AtlasStrategyInstruction,
    *,
    reference_price: float,
) -> LyfePortfolioMapping:
    price = _validate_reference_price(
        reference_price
    )

    if instruction.action == "NO_ACTION":
        return LyfePortfolioMapping(
            instruction_id=(
                instruction.instruction_id
            ),
            status="NO_PORTFOLIO_CHANGE",
            executable=False,
            reason=(
                "LYFE emitted NO_ACTION; Atlas will not "
                "change the current portfolio."
            ),
        )

    if instruction.action == "EXIT":
        target = PortfolioTarget(
            asset=instruction.asset,
            target_weight=0.0,
            reference_price=price,
            source_label=(
                f"LYFE:{instruction.strategy_id}:EXIT"
            ),
        )

        return LyfePortfolioMapping(
            instruction_id=(
                instruction.instruction_id
            ),
            status="EXIT_TARGET_READY",
            executable=True,
            reason=(
                "LYFE exit mapped to zero Atlas target weight."
            ),
            target=target,
        )

    if instruction.direction == "SHORT":
        return LyfePortfolioMapping(
            instruction_id=(
                instruction.instruction_id
            ),
            status="SHORT_DEFERRED",
            executable=False,
            reason=(
                "Atlas portfolio execution is currently "
                "long-only; the LYFE short signal remains "
                "available for research and shadow evaluation."
            ),
        )

    if instruction.direction == "FLAT":
        return LyfePortfolioMapping(
            instruction_id=(
                instruction.instruction_id
            ),
            status="FLAT_DEFERRED",
            executable=False,
            reason=(
                "A flat non-exit instruction does not imply "
                "portfolio liquidation."
            ),
        )

    if (
        instruction.direction == "LONG"
        and instruction.action
        in {
            "ENTER",
            "HOLD",
            "REDUCE",
        }
    ):
        target = PortfolioTarget(
            asset=instruction.asset,
            target_weight=(
                instruction.requested_exposure
            ),
            reference_price=price,
            source_label=(
                f"LYFE:{instruction.strategy_id}:"
                f"{instruction.action}"
            ),
        )

        return LyfePortfolioMapping(
            instruction_id=(
                instruction.instruction_id
            ),
            status="LONG_TARGET_READY",
            executable=True,
            reason=(
                "LYFE long instruction mapped to an Atlas "
                "portfolio target."
            ),
            target=target,
        )

    return LyfePortfolioMapping(
        instruction_id=(
            instruction.instruction_id
        ),
        status="UNSUPPORTED_MAPPING",
        executable=False,
        reason=(
            "The LYFE instruction does not map to a supported "
            "Atlas portfolio target."
        ),
    )


def build_lyfe_portfolio_intent_plan(
    instruction: AtlasStrategyInstruction,
    *,
    reference_price: float,
    account: AccountSnapshot,
    policy: RebalancePolicy | None = None,
    write_output: bool = False,
) -> dict[str, Any]:
    mapping = map_lyfe_instruction_to_target(
        instruction,
        reference_price=reference_price,
    )

    if (
        not mapping.executable
        or mapping.target is None
    ):
        return {
            "version":
                "lyfe_portfolio_intent_adapter_v1",
            "instruction_id":
                instruction.instruction_id,
            "strategy_id":
                instruction.strategy_id,
            "mapping":
                mapping.to_dict(),
            "intents": [],
            "rebalance_lines": [],
            "execution_blocked": True,
        }

    plan = build_portfolio_intent_plan(
        targets=[
            mapping.target
        ],
        account=account,
        strategy_id=(
            instruction.strategy_id
        ),
        evidence_id=(
            instruction.source_decision_sha256
            or instruction.instruction_id
        ),
        policy=policy,
        write_output=write_output,
    )

    return {
        **plan,
        "lyfe_mapping":
            mapping.to_dict(),
        "execution_blocked":
            False,
    }
