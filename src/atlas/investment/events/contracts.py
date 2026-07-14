"""Canonical event contracts for Atlas G.22."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

SCHEMA_VERSION = "g22.event_bus.v1"


class EventType(str, Enum):
    MARKET_DATA = "MARKET_DATA"
    FEATURE = "FEATURE"
    SIGNAL = "SIGNAL"
    PORTFOLIO_INTENT = "PORTFOLIO_INTENT"
    RISK_DECISION = "RISK_DECISION"
    EXECUTION_INTENT = "EXECUTION_INTENT"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_DECIDED = "APPROVAL_DECIDED"
    PAPER_ORDER_SUBMITTED = "PAPER_ORDER_SUBMITTED"
    ORDER_STATUS = "ORDER_STATUS"
    FILL = "FILL"
    LEDGER_UPDATED = "LEDGER_UPDATED"
    RECONCILIATION = "RECONCILIATION"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class AtlasEvent:
    event_id: str
    event_type: EventType
    aggregate_type: str
    aggregate_id: str
    occurred_at: str
    source: str
    payload: Mapping[str, Any]
    correlation_id: str | None = None
    causation_id: str | None = None
    sequence: int = 0
    schema_version: str = SCHEMA_VERSION
    paper_only: bool = True
    live_execution: bool = False
    credentials_used: bool = False
    record_hash: str = ""
    previous_record_hash: str = ""


@dataclass(frozen=True)
class EventCursor:
    offset: int
    last_event_id: str | None
    last_record_hash: str


@dataclass(frozen=True)
class EventReplayResult:
    events_replayed: int
    first_event_id: str | None
    last_event_id: str | None
    final_offset: int
    paper_only: bool = True
    live_execution: bool = False


@dataclass(frozen=True)
class EventDispatchResult:
    event_id: str
    handlers_matched: int
    handlers_succeeded: int
    handlers_failed: int
    errors: tuple[str, ...] = field(default_factory=tuple)


__all__ = [
    "SCHEMA_VERSION",
    "AtlasEvent",
    "EventCursor",
    "EventDispatchResult",
    "EventReplayResult",
    "EventType",
]
