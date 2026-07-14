"""
Atlas-owned contracts for consuming LYFE strategy decisions.

Atlas does not import LYFE source code. It owns and validates
its copy of the external contract boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


SUPPORTED_SCHEMA_VERSION = "lyfe.strategy-decision.v1"
SUPPORTED_MANIFEST_VERSION = "lyfe.strategy-decision-manifest.v1"

Action = Literal[
    "NO_ACTION",
    "ENTER",
    "EXIT",
    "HOLD",
    "REDUCE",
]

Direction = Literal[
    "FLAT",
    "LONG",
    "SHORT",
]


@dataclass(frozen=True, slots=True)
class ExternalStrategyDecision:
    schema_version: str

    decision_id: str
    generated_at_utc: str
    signal_timestamp_utc: str

    strategy_id: str
    strategy_version: str

    asset: str
    action: Action
    direction: Direction

    target_exposure: float
    confidence: float | None

    reason: str

    dataset_hash: str | None = None
    source_commit: str | None = None
    research_session_id: str | None = None

    research_only: bool = True
    requires_human_approval: bool = True

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        if self.schema_version != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported LYFE schema: {self.schema_version}"
            )

        for field_name, value in (
            ("decision_id", self.decision_id),
            ("strategy_id", self.strategy_id),
            ("strategy_version", self.strategy_version),
            ("asset", self.asset),
            ("reason", self.reason),
        ):
            if not str(value).strip():
                raise ValueError(
                    f"{field_name} must not be empty."
                )

        for timestamp_name, timestamp_value in (
            ("generated_at_utc", self.generated_at_utc),
            (
                "signal_timestamp_utc",
                self.signal_timestamp_utc,
            ),
        ):
            try:
                parsed = datetime.fromisoformat(
                    timestamp_value.replace(
                        "Z",
                        "+00:00",
                    )
                )
            except ValueError as exc:
                raise ValueError(
                    f"{timestamp_name} must be ISO-8601."
                ) from exc

            if parsed.tzinfo is None:
                raise ValueError(
                    f"{timestamp_name} must include timezone."
                )

        if self.action not in {
            "NO_ACTION",
            "ENTER",
            "EXIT",
            "HOLD",
            "REDUCE",
        }:
            raise ValueError(
                f"Unsupported action: {self.action}"
            )

        if self.direction not in {
            "FLAT",
            "LONG",
            "SHORT",
        }:
            raise ValueError(
                f"Unsupported direction: {self.direction}"
            )

        if not 0.0 <= self.target_exposure <= 1.0:
            raise ValueError(
                "target_exposure must be between 0.0 and 1.0."
            )

        if (
            self.confidence is not None
            and not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError(
                "confidence must be between 0.0 and 1.0."
            )

        if (
            self.action == "NO_ACTION"
            and self.direction != "FLAT"
        ):
            raise ValueError(
                "NO_ACTION must use FLAT direction."
            )

        if (
            self.direction == "FLAT"
            and self.target_exposure != 0.0
        ):
            raise ValueError(
                "FLAT decisions must use zero exposure."
            )


@dataclass(frozen=True, slots=True)
class AtlasStrategyInstruction:
    instruction_id: str
    source_system: str

    strategy_id: str
    strategy_version: str

    signal_timestamp_utc: str

    asset: str
    action: Action
    direction: Direction
    requested_exposure: float

    confidence: float | None
    rationale: str

    requires_human_approval: bool
    research_only: bool

    source_decision_sha256: str
    source_commit: str | None = None
    dataset_hash: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )
