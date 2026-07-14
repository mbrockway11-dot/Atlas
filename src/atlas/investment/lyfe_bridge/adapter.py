"""
Atlas LYFE Strategy Adapter.

Loads and verifies a LYFE StrategyDecision artifact and converts
it into an Atlas-owned strategy instruction.

This adapter does not execute trades.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import (
    SUPPORTED_MANIFEST_VERSION,
    AtlasStrategyInstruction,
    ExternalStrategyDecision,
)


class LyfeDecisionIntegrityError(ValueError):
    """Raised when an artifact hash or manifest is invalid."""


class LyfeDecisionSafetyError(ValueError):
    """Raised when an external decision violates Atlas safety rules."""


def file_sha256(
    path: str | Path,
) -> str:
    path = Path(path)
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _load_json(
    path: str | Path,
) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            path
        )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(payload, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return payload


def load_manifest(
    manifest_path: str | Path,
) -> dict[str, Any]:
    manifest = _load_json(
        manifest_path
    )

    if (
        manifest.get("schema_version")
        != SUPPORTED_MANIFEST_VERSION
    ):
        raise LyfeDecisionIntegrityError(
            "Unsupported LYFE decision manifest schema."
        )

    expected_hash = str(
        manifest.get(
            "decision_sha256",
            "",
        )
    ).strip()

    if len(expected_hash) != 64:
        raise LyfeDecisionIntegrityError(
            "Manifest decision_sha256 is invalid."
        )

    return manifest


def verify_decision_artifact(
    decision_path: str | Path,
    manifest_path: str | Path | None = None,
) -> str:
    decision_path = Path(
        decision_path
    )

    if manifest_path is None:
        manifest_path = decision_path.with_suffix(
            ".manifest.json"
        )

    manifest = load_manifest(
        manifest_path
    )

    actual_hash = file_sha256(
        decision_path
    )

    expected_hash = str(
        manifest["decision_sha256"]
    )

    if actual_hash != expected_hash:
        raise LyfeDecisionIntegrityError(
            "LYFE decision SHA-256 mismatch."
        )

    return actual_hash


def load_external_decision(
    decision_path: str | Path,
) -> ExternalStrategyDecision:
    payload = _load_json(
        decision_path
    )

    decision = ExternalStrategyDecision(
        **payload
    )

    decision.validate()

    return decision


def enforce_atlas_safety_boundary(
    decision: ExternalStrategyDecision,
) -> None:
    if not decision.research_only:
        raise LyfeDecisionSafetyError(
            "Atlas currently accepts only research-only LYFE decisions."
        )

    if not decision.requires_human_approval:
        raise LyfeDecisionSafetyError(
            "Atlas requires human approval for all LYFE decisions."
        )

    if (
        decision.action == "ENTER"
        and decision.target_exposure <= 0.0
    ):
        raise LyfeDecisionSafetyError(
            "ENTER decisions must request positive exposure."
        )

    if (
        decision.action == "NO_ACTION"
        and decision.target_exposure != 0.0
    ):
        raise LyfeDecisionSafetyError(
            "NO_ACTION decisions must request zero exposure."
        )


def adapt_lyfe_decision(
    decision: ExternalStrategyDecision,
    *,
    source_sha256: str,
) -> AtlasStrategyInstruction:
    enforce_atlas_safety_boundary(
        decision
    )

    return AtlasStrategyInstruction(
        instruction_id=(
            f"atlas:{decision.decision_id}"
        ),
        source_system="LYFE",
        strategy_id=decision.strategy_id,
        strategy_version=decision.strategy_version,
        signal_timestamp_utc=(
            decision.signal_timestamp_utc
        ),
        asset=decision.asset,
        action=decision.action,
        direction=decision.direction,
        requested_exposure=(
            decision.target_exposure
        ),
        confidence=decision.confidence,
        rationale=decision.reason,
        requires_human_approval=(
            decision.requires_human_approval
        ),
        research_only=decision.research_only,
        source_decision_sha256=source_sha256,
        source_commit=decision.source_commit,
        dataset_hash=decision.dataset_hash,
        metadata={
            **decision.metadata,
            "external_decision_id":
                decision.decision_id,
            "generated_at_utc":
                decision.generated_at_utc,
            "research_session_id":
                decision.research_session_id,
        },
    )


def import_lyfe_strategy_decision(
    decision_path: str | Path,
    manifest_path: str | Path | None = None,
) -> AtlasStrategyInstruction:
    source_hash = verify_decision_artifact(
        decision_path,
        manifest_path,
    )

    decision = load_external_decision(
        decision_path
    )

    return adapt_lyfe_decision(
        decision,
        source_sha256=source_hash,
    )
