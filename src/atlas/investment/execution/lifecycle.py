"""Persistent paper-order lifecycle state machine.

This module owns order lifecycle state, legal transition validation,
duplicate-intent protection, restart recovery, cancellation, expiry, and
immutable transition history.

It contains no live broker connectivity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from atlas.investment.execution.contracts import (
    FillRecord,
    OrderIntent,
    OrderRecord,
    RiskDecision,
)


LIFECYCLE_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

ORDER_STATE_JSON = (
    OUTPUT_DIR
    / "paper_order_state.json"
)

ORDER_TRANSITIONS_JSONL = (
    OUTPUT_DIR
    / "paper_order_transitions.jsonl"
)


ORDER_STATES = {
    "CREATED",
    "RISK_APPROVED",
    "RISK_REJECTED",
    "SUBMITTED",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "EXPIRED",
    "REJECTED",
}

TERMINAL_STATES = {
    "RISK_REJECTED",
    "FILLED",
    "CANCELLED",
    "EXPIRED",
    "REJECTED",
}

OPEN_STATES = {
    "CREATED",
    "RISK_APPROVED",
    "SUBMITTED",
    "PARTIALLY_FILLED",
}

LEGAL_TRANSITIONS = {
    "CREATED": {
        "RISK_APPROVED",
        "RISK_REJECTED",
        "CANCELLED",
        "EXPIRED",
    },
    "RISK_APPROVED": {
        "SUBMITTED",
        "REJECTED",
        "CANCELLED",
        "EXPIRED",
    },
    "RISK_REJECTED": set(),
    "SUBMITTED": {
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCELLED",
        "EXPIRED",
        "REJECTED",
    },
    "PARTIALLY_FILLED": {
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCELLED",
        "EXPIRED",
        "REJECTED",
    },
    "FILLED": set(),
    "CANCELLED": set(),
    "EXPIRED": set(),
    "REJECTED": set(),
}


@dataclass(frozen=True)
class LifecycleRecord:
    """Current persistent state for one paper order intent."""

    lifecycle_id: str
    intent_id: str
    order_id: str
    asset: str
    side: str
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    average_fill_price: float
    fee_paid: float
    state: str
    created_at: str
    updated_at: str
    expires_at: str
    strategy_id: str
    evidence_id: str
    rejection_reason: str = ""
    cancellation_reason: str = ""

    @property
    def terminal(self) -> bool:
        return (
            self.state
            in TERMINAL_STATES
        )

    @property
    def open(self) -> bool:
        return (
            self.state
            in OPEN_STATES
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["terminal"] = self.terminal
        result["open"] = self.open
        return result


@dataclass(frozen=True)
class LifecycleTransition:
    """One immutable lifecycle transition event."""

    transition_id: str
    lifecycle_id: str
    intent_id: str
    order_id: str
    from_state: str
    to_state: str
    recorded_at: str
    reason: str
    filled_quantity: float
    remaining_quantity: float
    event_hash: str
    previous_event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PaperOrderLifecycleStore:
    """Persistent state store and transition engine."""

    def __init__(
        self,
        *,
        state_path: Path = (
            ORDER_STATE_JSON
        ),
        transitions_path: Path = (
            ORDER_TRANSITIONS_JSONL
        ),
    ) -> None:
        self.state_path = state_path
        self.transitions_path = (
            transitions_path
        )

    def create(
        self,
        intent: OrderIntent,
    ) -> LifecycleRecord:
        """Create a lifecycle record, rejecting duplicate active intents."""
        records = self.load_records()

        existing = records.get(
            intent.intent_id
        )

        if (
            existing is not None
            and existing.open
        ):
            raise ValueError(
                "DUPLICATE_ACTIVE_INTENT:"
                + intent.intent_id
            )

        now = utc_now()

        record = LifecycleRecord(
            lifecycle_id=(
                build_lifecycle_id(
                    intent.intent_id
                )
            ),
            intent_id=intent.intent_id,
            order_id="",
            asset=intent.asset,
            side=intent.side,
            requested_quantity=(
                intent.quantity
            ),
            filled_quantity=0.0,
            remaining_quantity=(
                intent.quantity
            ),
            average_fill_price=0.0,
            fee_paid=0.0,
            state="CREATED",
            created_at=now,
            updated_at=now,
            expires_at=(
                intent.expires_at
            ),
            strategy_id=(
                intent.strategy_id
            ),
            evidence_id=(
                intent.evidence_id
            ),
        )

        records[
            intent.intent_id
        ] = record

        self.write_records(
            records
        )

        self.append_transition(
            record=record,
            from_state="",
            to_state="CREATED",
            reason=(
                "ORDER_INTENT_CREATED"
            ),
        )

        return record

    def apply_risk_decision(
        self,
        intent_id: str,
        decision: RiskDecision,
    ) -> LifecycleRecord:
        """Apply deterministic pre-trade risk outcome."""
        if decision.intent_id != intent_id:
            raise ValueError(
                "RISK_INTENT_MISMATCH"
            )

        target_state = (
            "RISK_APPROVED"
            if decision.approved
            else "RISK_REJECTED"
        )

        return self.transition(
            intent_id,
            target_state,
            reason=(
                "RISK_APPROVED"
                if decision.approved
                else "|".join(
                    decision.reason_codes
                )
            ),
        )

    def apply_order_record(
        self,
        intent_id: str,
        order: OrderRecord,
    ) -> LifecycleRecord:
        """Apply paper-broker order submission or terminal result."""
        if order.intent_id != intent_id:
            raise ValueError(
                "ORDER_INTENT_MISMATCH"
            )

        status_map = {
            "FILLED": "FILLED",
            "PARTIALLY_FILLED": (
                "PARTIALLY_FILLED"
            ),
            "CANCELLED": "CANCELLED",
            "REJECTED": "REJECTED",
            "SUBMITTED": "SUBMITTED",
        }

        target = status_map.get(
            order.status
        )

        if target is None:
            raise ValueError(
                "UNSUPPORTED_ORDER_STATUS:"
                + order.status
            )

        records = self.load_records()
        current = require_record(
            records,
            intent_id,
        )

        updated = self.transition(
            intent_id,
            target,
            reason=(
                order.rejection_reason
                or "PAPER_BROKER_"
                + order.status
            ),
            order_id=order.order_id,
            filled_quantity=(
                order.filled_quantity
            ),
            remaining_quantity=(
                order.remaining_quantity
            ),
            average_fill_price=(
                order.average_fill_price
            ),
            fee_paid=(
                order.fee_paid
            ),
        )

        if (
            current.state
            == "RISK_APPROVED"
            and target
            in {
                "PARTIALLY_FILLED",
                "FILLED",
            }
        ):
            # Paper brokers may immediately fill an approved order.
            # Preserve a submitted transition in the audit trail.
            pass

        return updated

    def apply_fill(
        self,
        intent_id: str,
        fill: FillRecord,
    ) -> LifecycleRecord:
        """Apply one additional fill to a submitted or partial order."""
        if fill.intent_id != intent_id:
            raise ValueError(
                "FILL_INTENT_MISMATCH"
            )

        records = self.load_records()
        current = require_record(
            records,
            intent_id,
        )

        if current.state not in {
            "SUBMITTED",
            "PARTIALLY_FILLED",
        }:
            raise ValueError(
                "FILL_NOT_ALLOWED_FROM_STATE:"
                + current.state
            )

        next_filled = (
            current.filled_quantity
            + fill.quantity
        )

        if (
            next_filled
            > current.requested_quantity
            + 1e-12
        ):
            raise ValueError(
                "OVERFILL_DETECTED"
            )

        next_remaining = max(
            0.0,
            current.requested_quantity
            - next_filled,
        )

        next_average = (
            (
                current.filled_quantity
                * current.average_fill_price
                + fill.quantity
                * fill.price
            )
            / next_filled
            if next_filled > 0
            else 0.0
        )

        next_state = (
            "FILLED"
            if next_remaining <= 1e-12
            else "PARTIALLY_FILLED"
        )

        return self.transition(
            intent_id,
            next_state,
            reason="PAPER_FILL_APPLIED",
            order_id=fill.order_id,
            filled_quantity=(
                next_filled
            ),
            remaining_quantity=(
                next_remaining
            ),
            average_fill_price=(
                next_average
            ),
            fee_paid=(
                current.fee_paid
                + fill.fee
            ),
        )

    def cancel(
        self,
        intent_id: str,
        *,
        reason: str = (
            "OPERATOR_CANCELLED"
        ),
    ) -> LifecycleRecord:
        return self.transition(
            intent_id,
            "CANCELLED",
            reason=reason,
            cancellation_reason=reason,
        )

    def expire_due_orders(
        self,
        *,
        now: datetime | None = None,
    ) -> list[LifecycleRecord]:
        """Expire open records whose ISO timestamp has passed."""
        reference = (
            now
            or datetime.now(UTC)
        )

        expired: list[
            LifecycleRecord
        ] = []

        for record in list(
            self.load_records().values()
        ):
            if (
                not record.open
                or not record.expires_at
            ):
                continue

            try:
                expires_at = (
                    datetime.fromisoformat(
                        record.expires_at
                        .replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )
            except ValueError:
                continue

            if reference >= expires_at:
                expired.append(
                    self.transition(
                        record.intent_id,
                        "EXPIRED",
                        reason=(
                            "ORDER_INTENT_EXPIRED"
                        ),
                    )
                )

        return expired

    def recover_open_orders(
        self,
    ) -> list[LifecycleRecord]:
        """Load active orders after process restart."""
        return sorted(
            (
                record
                for record
                in self.load_records().values()
                if record.open
            ),
            key=lambda item: (
                item.created_at,
                item.intent_id,
            ),
        )

    def transition(
        self,
        intent_id: str,
        to_state: str,
        *,
        reason: str,
        order_id: str | None = None,
        filled_quantity: (
            float | None
        ) = None,
        remaining_quantity: (
            float | None
        ) = None,
        average_fill_price: (
            float | None
        ) = None,
        fee_paid: float | None = None,
        rejection_reason: (
            str | None
        ) = None,
        cancellation_reason: (
            str | None
        ) = None,
    ) -> LifecycleRecord:
        """Validate and persist one legal state transition."""
        target = str(
            to_state
        ).upper()

        if target not in ORDER_STATES:
            raise ValueError(
                "UNKNOWN_ORDER_STATE:"
                + target
            )

        records = self.load_records()
        current = require_record(
            records,
            intent_id,
        )

        legal = LEGAL_TRANSITIONS.get(
            current.state,
            set(),
        )

        if target not in legal:
            raise ValueError(
                "ILLEGAL_ORDER_TRANSITION:"
                + current.state
                + "->"
                + target
            )

        updated = LifecycleRecord(
            lifecycle_id=(
                current.lifecycle_id
            ),
            intent_id=current.intent_id,
            order_id=(
                current.order_id
                if order_id is None
                else order_id
            ),
            asset=current.asset,
            side=current.side,
            requested_quantity=(
                current.requested_quantity
            ),
            filled_quantity=(
                current.filled_quantity
                if filled_quantity
                is None
                else float(
                    filled_quantity
                )
            ),
            remaining_quantity=(
                current.remaining_quantity
                if remaining_quantity
                is None
                else float(
                    remaining_quantity
                )
            ),
            average_fill_price=(
                current.average_fill_price
                if average_fill_price
                is None
                else float(
                    average_fill_price
                )
            ),
            fee_paid=(
                current.fee_paid
                if fee_paid is None
                else float(fee_paid)
            ),
            state=target,
            created_at=(
                current.created_at
            ),
            updated_at=utc_now(),
            expires_at=(
                current.expires_at
            ),
            strategy_id=(
                current.strategy_id
            ),
            evidence_id=(
                current.evidence_id
            ),
            rejection_reason=(
                current.rejection_reason
                if rejection_reason
                is None
                else rejection_reason
            ),
            cancellation_reason=(
                current.cancellation_reason
                if cancellation_reason
                is None
                else cancellation_reason
            ),
        )

        records[
            intent_id
        ] = updated

        self.write_records(
            records
        )

        self.append_transition(
            record=updated,
            from_state=current.state,
            to_state=target,
            reason=reason,
        )

        return updated

    def load_records(
        self,
    ) -> dict[str, LifecycleRecord]:
        if not self.state_path.exists():
            return {}

        try:
            payload = json.loads(
                self.state_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

        raw_records = payload.get(
            "records",
            {},
        )

        if not isinstance(
            raw_records,
            Mapping,
        ):
            return {}

        result: dict[
            str,
            LifecycleRecord,
        ] = {}

        for intent_id, value in (
            raw_records.items()
        ):
            if not isinstance(
                value,
                Mapping,
            ):
                continue

            record_data = {
                key: item
                for key, item
                in value.items()
                if key
                not in {
                    "terminal",
                    "open",
                }
            }

            try:
                result[
                    str(intent_id)
                ] = LifecycleRecord(
                    **record_data
                )
            except TypeError:
                continue

        return result

    def write_records(
        self,
        records: Mapping[
            str,
            LifecycleRecord,
        ],
    ) -> None:
        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "version": (
                LIFECYCLE_VERSION
            ),
            "updated_at": utc_now(),
            "records": {
                intent_id: (
                    record.to_dict()
                )
                for intent_id, record
                in sorted(
                    records.items()
                )
            },
        }

        temporary = (
            self.state_path
            .with_suffix(
                self.state_path.suffix
                + ".tmp"
            )
        )

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            self.state_path
        )

    def append_transition(
        self,
        *,
        record: LifecycleRecord,
        from_state: str,
        to_state: str,
        reason: str,
    ) -> LifecycleTransition:
        previous_hash = (
            self.latest_transition_hash()
        )

        recorded_at = utc_now()

        core = {
            "lifecycle_id": (
                record.lifecycle_id
            ),
            "intent_id": (
                record.intent_id
            ),
            "order_id": (
                record.order_id
            ),
            "from_state": (
                from_state
            ),
            "to_state": (
                to_state
            ),
            "recorded_at": (
                recorded_at
            ),
            "reason": reason,
            "filled_quantity": (
                record.filled_quantity
            ),
            "remaining_quantity": (
                record.remaining_quantity
            ),
            "previous_event_hash": (
                previous_hash
            ),
        }

        event_hash = stable_hash(
            core
        )

        transition = (
            LifecycleTransition(
                transition_id=(
                    "TRANSITION-"
                    + event_hash[:24]
                ),
                event_hash=event_hash,
                **core,
            )
        )

        self.transitions_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.transitions_path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                json.dumps(
                    transition.to_dict(),
                    sort_keys=True,
                    default=str,
                )
                + "\n"
            )

        return transition

    def read_transitions(
        self,
    ) -> list[LifecycleTransition]:
        if not (
            self.transitions_path.exists()
        ):
            return []

        result: list[
            LifecycleTransition
        ] = []

        with self.transitions_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line in handle:
                text = line.strip()

                if not text:
                    continue

                try:
                    payload = (
                        json.loads(text)
                    )
                except (
                    json.JSONDecodeError
                ):
                    continue

                try:
                    result.append(
                        LifecycleTransition(
                            **payload
                        )
                    )
                except TypeError:
                    continue

        return result

    def latest_transition_hash(
        self,
    ) -> str:
        transitions = (
            self.read_transitions()
        )

        return (
            transitions[-1].event_hash
            if transitions
            else ""
        )

    def validate_transition_chain(
        self,
    ) -> dict[str, Any]:
        transitions = (
            self.read_transitions()
        )

        errors: list[str] = []
        previous_hash = ""

        for index, transition in enumerate(
            transitions,
            start=1,
        ):
            if (
                transition
                .previous_event_hash
                != previous_hash
            ):
                errors.append(
                    "PREVIOUS_HASH_MISMATCH:"
                    + str(index)
                )

            core = {
                "lifecycle_id": (
                    transition
                    .lifecycle_id
                ),
                "intent_id": (
                    transition.intent_id
                ),
                "order_id": (
                    transition.order_id
                ),
                "from_state": (
                    transition.from_state
                ),
                "to_state": (
                    transition.to_state
                ),
                "recorded_at": (
                    transition.recorded_at
                ),
                "reason": (
                    transition.reason
                ),
                "filled_quantity": (
                    transition
                    .filled_quantity
                ),
                "remaining_quantity": (
                    transition
                    .remaining_quantity
                ),
                "previous_event_hash": (
                    transition
                    .previous_event_hash
                ),
            }

            expected = stable_hash(
                core
            )

            if (
                transition.event_hash
                != expected
            ):
                errors.append(
                    "EVENT_HASH_MISMATCH:"
                    + str(index)
                )

            previous_hash = (
                transition.event_hash
            )

        return {
            "valid": not errors,
            "transition_count": len(
                transitions
            ),
            "errors": errors,
            "latest_event_hash": (
                previous_hash
            ),
        }


def require_record(
    records: Mapping[
        str,
        LifecycleRecord,
    ],
    intent_id: str,
) -> LifecycleRecord:
    record = records.get(
        intent_id
    )

    if record is None:
        raise KeyError(
            "UNKNOWN_INTENT:"
            + intent_id
        )

    return record


def build_lifecycle_id(
    intent_id: str,
) -> str:
    return (
        "LIFECYCLE-"
        + hashlib.sha256(
            intent_id.encode(
                "utf-8"
            )
        ).hexdigest()[:24]
    )


def stable_hash(
    payload: Mapping[str, Any],
) -> str:
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


__all__ = [
    "LEGAL_TRANSITIONS",
    "LIFECYCLE_VERSION",
    "OPEN_STATES",
    "ORDER_STATES",
    "ORDER_STATE_JSON",
    "ORDER_TRANSITIONS_JSONL",
    "TERMINAL_STATES",
    "LifecycleRecord",
    "LifecycleTransition",
    "PaperOrderLifecycleStore",
    "build_lifecycle_id",
]
