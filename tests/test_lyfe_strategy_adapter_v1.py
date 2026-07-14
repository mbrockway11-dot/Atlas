from __future__ import annotations

import hashlib
import json

import pytest

from atlas.investment.lyfe_bridge import (
    LyfeDecisionIntegrityError,
    LyfeDecisionSafetyError,
    import_lyfe_strategy_decision,
)


def _payload() -> dict:
    return {
        "schema_version":
            "lyfe.strategy-decision.v1",
        "decision_id":
            "engine-a-sol-123",
        "generated_at_utc":
            "2026-07-14T00:00:00+00:00",
        "signal_timestamp_utc":
            "2024-01-01T00:00:00+00:00",
        "strategy_id":
            "V32_AB",
        "strategy_version":
            "32.0.0",
        "asset":
            "SOL",
        "action":
            "ENTER",
        "direction":
            "LONG",
        "target_exposure":
            0.25,
        "confidence":
            0.82,
        "reason":
            "Engine A continuation confirmed.",
        "dataset_hash":
            "abc123",
        "source_commit":
            "7d37b9b",
        "research_session_id":
            None,
        "research_only":
            True,
        "requires_human_approval":
            True,
        "metadata": {
            "selected_engine":
                "ENGINE_A",
        },
    }


def _write_artifact(
    tmp_path,
    payload: dict,
):
    decision_path = (
        tmp_path / "decision.json"
    )

    text = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    ) + "\n"

    decision_path.write_text(
        text,
        encoding="utf-8",
    )

    digest = hashlib.sha256(
        decision_path.read_bytes()
    ).hexdigest()

    manifest_path = (
        tmp_path / "decision.manifest.json"
    )

    manifest_path.write_text(
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
                    "7d37b9b",
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    return decision_path, manifest_path


def test_import_valid_lyfe_decision(
    tmp_path,
) -> None:
    decision_path, manifest_path = (
        _write_artifact(
            tmp_path,
            _payload(),
        )
    )

    instruction = (
        import_lyfe_strategy_decision(
            decision_path,
            manifest_path,
        )
    )

    assert instruction.source_system == "LYFE"
    assert instruction.action == "ENTER"
    assert instruction.direction == "LONG"
    assert instruction.requested_exposure == 0.25
    assert instruction.requires_human_approval is True
    assert instruction.research_only is True
    assert len(
        instruction.source_decision_sha256
    ) == 64


def test_hash_mismatch_is_rejected(
    tmp_path,
) -> None:
    decision_path, manifest_path = (
        _write_artifact(
            tmp_path,
            _payload(),
        )
    )

    decision_path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        LyfeDecisionIntegrityError,
        match="mismatch",
    ):
        import_lyfe_strategy_decision(
            decision_path,
            manifest_path,
        )


def test_non_research_decision_is_rejected(
    tmp_path,
) -> None:
    payload = _payload()
    payload["research_only"] = False

    decision_path, manifest_path = (
        _write_artifact(
            tmp_path,
            payload,
        )
    )

    with pytest.raises(
        LyfeDecisionSafetyError,
        match="research-only",
    ):
        import_lyfe_strategy_decision(
            decision_path,
            manifest_path,
        )


def test_missing_human_approval_is_rejected(
    tmp_path,
) -> None:
    payload = _payload()
    payload[
        "requires_human_approval"
    ] = False

    decision_path, manifest_path = (
        _write_artifact(
            tmp_path,
            payload,
        )
    )

    with pytest.raises(
        LyfeDecisionSafetyError,
        match="human approval",
    ):
        import_lyfe_strategy_decision(
            decision_path,
            manifest_path,
        )


def test_unsupported_schema_is_rejected(
    tmp_path,
) -> None:
    payload = _payload()
    payload["schema_version"] = "unknown.v99"

    decision_path, manifest_path = (
        _write_artifact(
            tmp_path,
            payload,
        )
    )

    with pytest.raises(
        ValueError,
        match="Unsupported LYFE schema",
    ):
        import_lyfe_strategy_decision(
            decision_path,
            manifest_path,
        )


def test_invalid_enter_exposure_is_rejected(
    tmp_path,
) -> None:
    payload = _payload()
    payload["target_exposure"] = 0.0

    decision_path, manifest_path = (
        _write_artifact(
            tmp_path,
            payload,
        )
    )

    with pytest.raises(
        LyfeDecisionSafetyError,
        match="positive exposure",
    ):
        import_lyfe_strategy_decision(
            decision_path,
            manifest_path,
        )

