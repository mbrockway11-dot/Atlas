from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from atlas.investment.lyfe_bridge.registry import (
    build_strategy_registry,
    registry_instruction_map,
    summarize_strategy_registry,
)


def _payload(
    *,
    decision_id: str,
    strategy_id: str,
    strategy_version: str = "1.0.0",
    action: str = "ENTER",
    direction: str = "LONG",
    target_exposure: float = 0.25,
) -> dict:
    return {
        "schema_version":
            "lyfe.strategy-decision.v1",
        "decision_id":
            decision_id,
        "generated_at_utc":
            "2026-07-14T00:00:00+00:00",
        "signal_timestamp_utc":
            "2026-07-14T00:00:00+00:00",
        "strategy_id":
            strategy_id,
        "strategy_version":
            strategy_version,
        "asset":
            "SOL",
        "action":
            action,
        "direction":
            direction,
        "target_exposure":
            target_exposure,
        "confidence":
            0.82,
        "reason":
            "Validated research decision.",
        "dataset_hash":
            "dataset-123",
        "source_commit":
            "abc1234",
        "research_session_id":
            None,
        "research_only":
            True,
        "requires_human_approval":
            True,
        "metadata": {},
    }


def _write_strategy(
    root: Path,
    directory_name: str,
    payload: dict,
) -> Path:
    directory = (
        root / directory_name
    )

    directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    decision_path = (
        directory
        / "latest_strategy_decision.json"
    )

    text = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    ) + "\n"

    decision_path.write_bytes(
        text.encode("utf-8")
    )

    digest = hashlib.sha256(
        decision_path.read_bytes()
    ).hexdigest()

    manifest_path = (
        directory
        / "latest_strategy_decision.manifest.json"
    )

    manifest_path.write_bytes(
        (
            json.dumps(
                {
                    "schema_version":
                        "lyfe.strategy-decision-manifest.v1",
                    "decision_path":
                        str(decision_path),
                    "decision_sha256":
                        digest,
                    "source_path":
                        "combined.csv",
                    "source_commit":
                        "abc1234",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    )

    return decision_path


def test_registry_discovers_multiple_strategies(
    tmp_path,
) -> None:
    _write_strategy(
        tmp_path,
        "V32_AB",
        _payload(
            decision_id="v32-decision",
            strategy_id="V32_AB",
            strategy_version="32.0.0",
        ),
    )

    _write_strategy(
        tmp_path,
        "V33_TOPOLOGY",
        _payload(
            decision_id="v33-decision",
            strategy_id="V33_TOPOLOGY",
            strategy_version="33.0.0",
        ),
    )

    snapshot = build_strategy_registry(
        tmp_path
    )

    assert snapshot.registered_count == 2
    assert snapshot.failure_count == 0
    assert snapshot.is_clean is True

    keys = [
        item.registry_key
        for item in snapshot.registered
    ]

    assert keys == [
        "LYFE:V32_AB:32.0.0",
        "LYFE:V33_TOPOLOGY:33.0.0",
    ]


def test_invalid_strategy_is_recorded_as_failure(
    tmp_path,
) -> None:
    _write_strategy(
        tmp_path,
        "VALID",
        _payload(
            decision_id="valid",
            strategy_id="VALID",
        ),
    )

    invalid = (
        tmp_path / "INVALID"
    )

    invalid.mkdir()

    (
        invalid
        / "latest_strategy_decision.json"
    ).write_text(
        "{}",
        encoding="utf-8",
    )

    snapshot = build_strategy_registry(
        tmp_path
    )

    assert snapshot.registered_count == 1
    assert snapshot.failure_count == 1
    assert snapshot.is_clean is False


def test_strict_registry_raises_on_failure(
    tmp_path,
) -> None:
    empty = (
        tmp_path / "EMPTY"
    )

    empty.mkdir()

    with pytest.raises(
        RuntimeError,
        match="registry discovery failed",
    ):
        build_strategy_registry(
            tmp_path,
            strict=True,
        )


def test_duplicate_registry_key_is_rejected(
    tmp_path,
) -> None:
    payload_one = _payload(
        decision_id="decision-one",
        strategy_id="DUPLICATE",
        strategy_version="1.0.0",
    )

    payload_two = _payload(
        decision_id="decision-two",
        strategy_id="DUPLICATE",
        strategy_version="1.0.0",
    )

    _write_strategy(
        tmp_path,
        "FIRST",
        payload_one,
    )

    _write_strategy(
        tmp_path,
        "SECOND",
        payload_two,
    )

    snapshot = build_strategy_registry(
        tmp_path
    )

    assert snapshot.registered_count == 1
    assert snapshot.failure_count == 1
    assert (
        "Duplicate strategy registry key"
        in snapshot.failures[0].error_message
    )


def test_registry_instruction_map(
    tmp_path,
) -> None:
    _write_strategy(
        tmp_path,
        "V32_AB",
        _payload(
            decision_id="v32-decision",
            strategy_id="V32_AB",
            strategy_version="32.0.0",
        ),
    )

    snapshot = build_strategy_registry(
        tmp_path
    )

    instruction_map = (
        registry_instruction_map(
            snapshot
        )
    )

    instruction = instruction_map[
        "LYFE:V32_AB:32.0.0"
    ]

    assert instruction.action == "ENTER"
    assert instruction.direction == "LONG"
    assert instruction.requested_exposure == 0.25


def test_registry_summary_is_deterministic(
    tmp_path,
) -> None:
    _write_strategy(
        tmp_path,
        "V33_TOPOLOGY",
        _payload(
            decision_id="v33-decision",
            strategy_id="V33_TOPOLOGY",
            strategy_version="33.0.0",
        ),
    )

    snapshot = build_strategy_registry(
        tmp_path
    )

    first = summarize_strategy_registry(
        snapshot
    )

    second = summarize_strategy_registry(
        snapshot
    )

    assert first == second
    assert first["registered_count"] == 1
    assert first["failure_count"] == 0
