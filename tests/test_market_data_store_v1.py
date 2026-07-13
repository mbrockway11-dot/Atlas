"""Tests for market snapshot persistence and audit integrity."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.market_data.store import (
    load_market_snapshot,
    validate_market_data_audit,
    write_market_snapshot,
)


def test_snapshot_round_trip_and_audit(
    tmp_path: Path,
):
    snapshot_path = (
        tmp_path / "snapshot.json"
    )

    audit_path = (
        tmp_path / "audit.jsonl"
    )

    snapshot = {
        "success": True,
        "snapshot_id": (
            "MARKET-SNAPSHOT-1"
        ),
        "counts": {
            "requested": 1,
            "resolved": 1,
            "failed": 0,
        },
        "contract": {
            "provider_neutral": True,
            "broker_independent": True,
            "live_execution": False,
            "credentials_used": False,
        },
    }

    write_market_snapshot(
        snapshot,
        path=snapshot_path,
        audit_path=audit_path,
    )

    loaded = load_market_snapshot(
        snapshot_path
    )

    assert (
        loaded["snapshot_id"]
        == "MARKET-SNAPSHOT-1"
    )

    validation = (
        validate_market_data_audit(
            path=audit_path
        )
    )

    assert validation["valid"]


def test_audit_tampering_is_detected(
    tmp_path: Path,
):
    snapshot_path = (
        tmp_path / "snapshot.json"
    )

    audit_path = (
        tmp_path / "audit.jsonl"
    )

    write_market_snapshot(
        {
            "success": True,
            "snapshot_id": "ONE",
            "counts": {},
        },
        path=snapshot_path,
        audit_path=audit_path,
    )

    event = json.loads(
        audit_path.read_text(
            encoding="utf-8"
        ).strip()
    )

    event["snapshot_id"] = (
        "TAMPERED"
    )

    audit_path.write_text(
        json.dumps(event)
        + "\n",
        encoding="utf-8",
    )

    validation = (
        validate_market_data_audit(
            path=audit_path
        )
    )

    assert not validation["valid"]
