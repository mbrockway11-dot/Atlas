"""Tests for Phase F.3 tamper-evident operator auditing."""

from __future__ import annotations

from pathlib import Path

from atlas.investment import (
    control_plane_operator_audit,
)


def test_event_hash_is_deterministic():
    event = (
        control_plane_operator_audit
        .build_operator_event(
            action="APPROVAL_ATTEMPTED",
            result="REQUESTED",
            operator_id="tester",
            session_id="UI-1",
            recorded_at=(
                "2026-07-12T00:00:00+00:00"
            ),
        )
    )

    assert (
        control_plane_operator_audit
        .operator_event_hash(event)
        == event["event_hash"]
    )


def test_sensitive_metadata_is_removed():
    event = (
        control_plane_operator_audit
        .build_operator_event(
            action="APPROVAL_REJECTED",
            result="REJECTED",
            operator_id="tester",
            session_id="UI-1",
            metadata={
                "secret": "never-store",
                "signature": "never-store",
                "nonce": "never-store",
                "safe": "yes",
                "nested": {
                    "env": "never-store",
                    "value": 1,
                },
            },
        )
    )

    metadata = event["metadata"]

    assert "secret" not in metadata
    assert "signature" not in metadata
    assert "nonce" not in metadata
    assert metadata["safe"] == "yes"
    assert "env" not in metadata[
        "nested"
    ]


def test_recorded_events_form_valid_chain(
    tmp_path: Path,
):
    ledger = tmp_path / "audit.jsonl"
    latest = tmp_path / "latest.json"

    first = (
        control_plane_operator_audit
        .record_operator_event(
            action=(
                "APPROVAL_ATTEMPTED"
            ),
            result="REQUESTED",
            operator_id="tester",
            session_id="UI-1",
            ledger_path=ledger,
            latest_path=latest,
        )
    )

    second = (
        control_plane_operator_audit
        .record_operator_event(
            action="APPROVAL_CREATED",
            result="SUCCEEDED",
            operator_id="tester",
            session_id="UI-1",
            approval_id="APPROVAL-1",
            ledger_path=ledger,
            latest_path=latest,
        )
    )

    events = (
        control_plane_operator_audit
        .read_operator_events(
            ledger
        )
    )

    assert len(events) == 2

    assert second[
        "previous_event_hash"
    ] == first["event_hash"]

    validation = (
        control_plane_operator_audit
        .validate_operator_audit_chain(
            events
        )
    )

    assert validation["valid"]


def test_tampered_event_breaks_chain():
    first = (
        control_plane_operator_audit
        .build_operator_event(
            action="DISPATCH_ATTEMPTED",
            result="REQUESTED",
            operator_id="tester",
            session_id="UI-1",
            recorded_at=(
                "2026-07-12T00:00:00+00:00"
            ),
        )
    )

    second = (
        control_plane_operator_audit
        .build_operator_event(
            action="DISPATCH_COMPLETED",
            result="SUCCEEDED",
            operator_id="tester",
            session_id="UI-1",
            previous_event_hash=(
                first["event_hash"]
            ),
            recorded_at=(
                "2026-07-12T00:01:00+00:00"
            ),
        )
    )

    second["reason"] = "tampered"

    validation = (
        control_plane_operator_audit
        .validate_operator_audit_chain([
            first,
            second,
        ])
    )

    assert not validation["valid"]

    assert any(
        value.startswith(
            "EVENT_HASH_MISMATCH"
        )
        for value in validation[
            "errors"
        ]
    )


def test_latest_index_tracks_activity(
    tmp_path: Path,
):
    ledger = tmp_path / "audit.jsonl"
    latest = tmp_path / "latest.json"

    (
        control_plane_operator_audit
        .record_operator_event(
            action=(
                "RECONCILIATION_ATTEMPTED"
            ),
            result="REQUESTED",
            operator_id="tester",
            session_id="UI-1",
            ledger_path=ledger,
            latest_path=latest,
        )
    )

    state = (
        control_plane_operator_audit
        .load_latest_operator_audit(
            latest
        )
    )

    assert state["event_count"] == 1
    assert state["operator_ids"] == [
        "tester",
    ]
    assert state["session_ids"] == [
        "UI-1",
    ]
