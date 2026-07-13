"""Tests for tamper-evident paper execution provenance."""

from __future__ import annotations

from pathlib import Path

from atlas.investment.execution.provenance import (
    read_execution_events,
    record_execution_events,
    validate_execution_provenance,
)


def test_execution_events_form_valid_chain(
    tmp_path: Path,
):
    ledger = (
        tmp_path / "events.jsonl"
    )
    latest = (
        tmp_path / "latest.json"
    )

    recorded = record_execution_events(
        execution_id="EXEC-1",
        events=[
            {
                "event_type": (
                    "INTENT_RECORDED"
                ),
                "intent_id": "INTENT-1",
                "status": "RECORDED",
                "payload": {
                    "asset": "BTC-USD",
                },
            },
            {
                "event_type": (
                    "RISK_EVALUATED"
                ),
                "intent_id": "INTENT-1",
                "status": "APPROVED",
                "payload": {
                    "approved": True,
                },
            },
        ],
        ledger_path=ledger,
        latest_path=latest,
    )

    assert len(recorded) == 2

    events = read_execution_events(
        ledger
    )

    validation = (
        validate_execution_provenance(
            events
        )
    )

    assert validation["valid"]

    assert (
        events[1][
            "previous_event_hash"
        ]
        == events[0][
            "event_hash"
        ]
    )


def test_sensitive_fields_are_removed(
    tmp_path: Path,
):
    ledger = (
        tmp_path / "events.jsonl"
    )
    latest = (
        tmp_path / "latest.json"
    )

    record_execution_events(
        execution_id="EXEC-1",
        events=[
            {
                "event_type": (
                    "INTENT_RECORDED"
                ),
                "payload": {
                    "asset": "BTC-USD",
                    "api_key": (
                        "never-store"
                    ),
                    "nested": {
                        "nonce": (
                            "never-store"
                        ),
                        "safe": True,
                    },
                },
            }
        ],
        ledger_path=ledger,
        latest_path=latest,
    )

    event = read_execution_events(
        ledger
    )[0]

    assert (
        "api_key"
        not in event["payload"]
    )

    assert (
        "nonce"
        not in event[
            "payload"
        ][
            "nested"
        ]
    )


def test_tampering_breaks_chain(
    tmp_path: Path,
):
    ledger = (
        tmp_path / "events.jsonl"
    )
    latest = (
        tmp_path / "latest.json"
    )

    record_execution_events(
        execution_id="EXEC-1",
        events=[
            {
                "event_type": (
                    "ORDER_RECORDED"
                ),
                "order_id": "ORDER-1",
                "status": "FILLED",
            }
        ],
        ledger_path=ledger,
        latest_path=latest,
    )

    events = read_execution_events(
        ledger
    )

    events[0]["status"] = (
        "TAMPERED"
    )

    validation = (
        validate_execution_provenance(
            events
        )
    )

    assert not validation["valid"]
