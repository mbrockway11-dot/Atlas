"""Behavioral observation registry loading and provenance validation."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Any

from atlas.services.profile_path_service import profile_exists
from atlas.symbolic_behavior.paths import PILOT_REGISTRY_PATH


REQUIRED_OBSERVATION_FIELDS = {
    "observation_id", "profile_key", "behavior_id", "observed_at",
    "date_precision", "description", "confidence", "source_refs",
}


def load_behavior_registry(path: str | Path = PILOT_REGISTRY_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_behavior_registry(payload)
    if errors:
        raise ValueError("Invalid behavior observation registry: " + "; ".join(errors))
    return payload


def validate_behavior_registry(payload: dict[str, Any], *, check_profiles: bool = True) -> list[str]:
    errors: list[str] = []
    source_ids = {row.get("source_id") for row in payload.get("sources", [])}
    behavior_ids = {row.get("behavior_id") for row in payload.get("behavior_taxonomy", [])}
    observation_ids: set[str] = set()
    if payload.get("causal_claims_allowed") is not False:
        errors.append("causal_claims_allowed must be false")
    if not isinstance(payload.get("symbolic_features_blinded_during_annotation"), bool):
        errors.append("symbolic_features_blinded_during_annotation must be boolean")
    for index, row in enumerate(payload.get("observations", [])):
        prefix = f"observations[{index}]"
        missing = REQUIRED_OBSERVATION_FIELDS - set(row)
        if missing:
            errors.append(f"{prefix} missing {sorted(missing)}")
            continue
        observation_id = str(row["observation_id"])
        if observation_id in observation_ids:
            errors.append(f"duplicate observation_id {observation_id}")
        observation_ids.add(observation_id)
        if row["behavior_id"] not in behavior_ids:
            errors.append(f"{prefix} has unknown behavior_id {row['behavior_id']}")
        unresolved = set(row.get("source_refs", [])) - source_ids
        if unresolved:
            errors.append(f"{prefix} has unresolved source refs {sorted(unresolved)}")
        try:
            date.fromisoformat(str(row["observed_at"]))
        except ValueError:
            errors.append(f"{prefix} observed_at is not an ISO date")
        try:
            confidence = float(row["confidence"])
            if not 0 <= confidence <= 1:
                raise ValueError
        except (TypeError, ValueError):
            errors.append(f"{prefix} confidence must be between 0 and 1")
        if check_profiles and not profile_exists(str(row["profile_key"])):
            errors.append(f"{prefix} profile not found: {row['profile_key']}")
    return errors


def behavior_profile_index(observations: list[dict[str, Any]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for row in observations:
        index.setdefault(str(row["behavior_id"]), set()).add(str(row["profile_key"]))
    return index
