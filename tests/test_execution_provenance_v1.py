"""Tests for Phase D.4 immutable execution provenance."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment.research_orchestrator import (
    provenance,
)


def fake_event() -> dict:
    return {
        "schema_version": "1.0.0",
        "recorded_at": (
            "2026-07-12T12:00:00+00:00"
        ),
        "run_id": "ORCH-1",
        "job_id": "alpha_engines",
        "status": "SUCCEEDED",
        "attempt": 1,
        "returncode": 0,
        "started_at": (
            "2026-07-12T11:59:00+00:00"
        ),
        "completed_at": (
            "2026-07-12T12:00:00+00:00"
        ),
        "duration_seconds": 60.0,
        "command_signature": {
            "job_id": "alpha_engines",
        },
        "build_identity_hash": "identity",
        "required_input_manifest": {},
        "required_output_manifest": {
            "output.json": "abc",
        },
        "cache": {
            "hit": False,
        },
        "verification": {
            "verified": True,
            "healed": True,
        },
        "recovery": {
            "attempt": 1,
        },
    }


def test_event_id_is_deterministic():
    event = fake_event()

    first = provenance.provenance_event_id(
        event
    )
    second = provenance.provenance_event_id(
        event
    )

    assert first == second
    assert first.startswith("PROV-")


def test_append_and_read_provenance(
    tmp_path: Path,
):
    ledger = tmp_path / "ledger.jsonl"
    latest = tmp_path / "latest.json"

    event = fake_event()
    event["event_id"] = (
        provenance.provenance_event_id(
            event
        )
    )

    provenance.append_provenance_event(
        event,
        ledger_path=ledger,
        latest_path=latest,
    )

    events = (
        provenance.read_provenance_events(
            ledger
        )
    )

    state = (
        provenance.load_latest_provenance(
            latest
        )
    )

    assert events == [event]
    assert state["event_count"] == 1
    assert (
        state["jobs"]["alpha_engines"]
        == event
    )
    assert (
        state["status_counts"][
            "SUCCEEDED"
        ]
        == 1
    )


def test_append_is_immutable_history(
    tmp_path: Path,
):
    ledger = tmp_path / "ledger.jsonl"
    latest = tmp_path / "latest.json"

    first = fake_event()
    first["event_id"] = (
        provenance.provenance_event_id(
            first
        )
    )

    second = fake_event()
    second["status"] = "CACHED"
    second["recorded_at"] = (
        "2026-07-12T13:00:00+00:00"
    )
    second["event_id"] = (
        provenance.provenance_event_id(
            second
        )
    )

    provenance.append_provenance_event(
        first,
        ledger_path=ledger,
        latest_path=latest,
    )

    provenance.append_provenance_event(
        second,
        ledger_path=ledger,
        latest_path=latest,
    )

    events = (
        provenance.read_provenance_events(
            ledger
        )
    )

    state = (
        provenance.load_latest_provenance(
            latest
        )
    )

    assert events == [
        first,
        second,
    ]
    assert state["event_count"] == 2
    assert (
        state["jobs"]["alpha_engines"][
            "status"
        ]
        == "CACHED"
    )


def test_malformed_ledger_line_is_ignored(
    tmp_path: Path,
):
    ledger = tmp_path / "ledger.jsonl"

    ledger.write_text(
        '{"job_id":"alpha"}\n'
        '{broken\n',
        encoding="utf-8",
    )

    events = (
        provenance.read_provenance_events(
            ledger
        )
    )

    assert events == [
        {
            "job_id": "alpha",
        }
    ]


def test_latest_state_round_trip(
    tmp_path: Path,
):
    path = tmp_path / "latest.json"

    state = {
        "schema_version": "1.0.0",
        "event_count": 3,
        "status_counts": {
            "SUCCEEDED": 2,
            "CACHED": 1,
        },
        "jobs": {},
    }

    provenance.write_latest_provenance(
        state,
        path,
    )

    assert (
        provenance.load_latest_provenance(
            path
        )
        == state
    )
