"""Normalized historical-event, participation, relationship, and outcome registries."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Any


DATE_PRECISIONS = {"day", "month", "year", "range", "unknown"}
CONFIDENCE_LEVELS = {"high", "moderate", "low", "unknown"}
BIRTH_TIME_STATUSES = {"known", "unknown", "reported_unverified", "estimated_historical"}
OUTCOME_CATEGORIES = {
    "career_transition", "appointment_removal", "collaboration", "conflict",
    "marriage_separation", "relocation", "publication_discovery",
    "financial_change", "illness_injury", "imprisonment", "death",
    "institutional_formation", "other",
}


def load_registry(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_registry(payload)
    if errors:
        raise ValueError("Invalid historical registry: " + "; ".join(errors))
    return payload


def validate_registry(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sources = {row.get("source_id") for row in payload.get("sources", []) if isinstance(row, dict)}
    events = {row.get("event_id") for row in payload.get("historical_events", []) if isinstance(row, dict)}
    profiles = {row.get("profile_key") for row in payload.get("profiles", []) if isinstance(row, dict)}
    for row in payload.get("profiles", []):
        require(row, ["profile_key", "name", "birth_date", "birth_time_status", "source_citations"], "profile", errors)
        validate_date(row.get("birth_date"), f"profile {row.get('profile_key')} birth_date", errors)
        if row.get("birth_time_status") not in BIRTH_TIME_STATUSES:
            errors.append(f"profile has invalid birth_time_status: {row.get('birth_time_status')}")
        validate_citations(row, sources, "profile", errors)
        provenance = row.get("birth_time_provenance")
        if provenance:
            validate_citations(provenance, sources, "profile birth_time_provenance", errors)
    for row in payload.get("historical_events", []):
        require(row, ["event_id", "name", "event_type", "start_date", "date_precision", "source_citations", "evidence_confidence"], "event", errors)
        validate_date(row.get("start_date"), f"event {row.get('event_id')} start_date", errors)
        validate_optional_date(row.get("end_date"), f"event {row.get('event_id')} end_date", errors)
        validate_common(row, sources, "event", errors)
    for row in payload.get("profile_participation", []):
        require(row, ["profile_key", "event_id", "participation_role", "active_interval", "involvement_confidence", "outcome_category", "source_citations"], "participation", errors)
        if row.get("profile_key") not in profiles:
            errors.append(f"participation references unknown profile: {row.get('profile_key')}")
        if row.get("event_id") not in events:
            errors.append(f"participation references unknown event: {row.get('event_id')}")
        if row.get("outcome_category") not in OUTCOME_CATEGORIES:
            errors.append(f"invalid outcome category: {row.get('outcome_category')}")
        validate_interval(row.get("active_interval", {}), "participation active_interval", errors)
        validate_citations(row, sources, "participation", errors)
    for row in payload.get("dynamic_relationships", []):
        require(row, ["relationship_id", "source_profile", "target_profile", "relationship_type", "direction", "start_date", "date_precision", "source_citations", "evidence_confidence"], "relationship", errors)
        if row.get("source_profile") not in profiles or row.get("target_profile") not in profiles:
            errors.append(f"relationship {row.get('relationship_id')} references unknown profile")
        if row.get("source_profile") == row.get("target_profile"):
            errors.append(f"relationship {row.get('relationship_id')} cannot be self-referential")
        validate_date(row.get("start_date"), f"relationship {row.get('relationship_id')} start_date", errors)
        validate_optional_date(row.get("end_date"), f"relationship {row.get('relationship_id')} end_date", errors)
        validate_common(row, sources, "relationship", errors)
        for event_id in row.get("shared_event_ids", []):
            if event_id not in events:
                errors.append(f"relationship {row.get('relationship_id')} references unknown event {event_id}")
    for row in payload.get("lifecycle_outcomes", []):
        require(row, ["outcome_id", "profile_key", "event_id", "date", "date_precision", "outcome_category", "source_citations", "evidence_confidence"], "outcome", errors)
        if row.get("profile_key") not in profiles or row.get("event_id") not in events:
            errors.append(f"outcome {row.get('outcome_id')} references unknown profile/event")
        if row.get("outcome_category") not in OUTCOME_CATEGORIES:
            errors.append(f"invalid outcome category: {row.get('outcome_category')}")
        validate_date(row.get("date"), f"outcome {row.get('outcome_id')} date", errors)
        validate_common(row, sources, "outcome", errors)
    return errors


def relationship_active(row: dict[str, Any], on_date: str) -> bool:
    """Return whether a sourced relationship interval contains a date."""
    point = date.fromisoformat(on_date)
    start = date.fromisoformat(str(row["start_date"]))
    end_value = str(row.get("end_date") or "")
    end = date.fromisoformat(end_value) if end_value else date.max
    return start <= point <= end


def event_active(row: dict[str, Any], on_date: str) -> bool:
    point = date.fromisoformat(on_date)
    start = date.fromisoformat(str(row["start_date"]))
    end = date.fromisoformat(str(row.get("end_date") or row["start_date"]))
    return start <= point <= end


def validate_common(row: dict[str, Any], sources: set[Any], label: str, errors: list[str]) -> None:
    if row.get("date_precision") not in DATE_PRECISIONS:
        errors.append(f"{label} has invalid date_precision: {row.get('date_precision')}")
    if row.get("evidence_confidence") not in CONFIDENCE_LEVELS:
        errors.append(f"{label} has invalid evidence_confidence: {row.get('evidence_confidence')}")
    validate_citations(row, sources, label, errors)


def validate_citations(row: dict[str, Any], sources: set[Any], label: str, errors: list[str]) -> None:
    citations = row.get("source_citations", [])
    if not citations:
        errors.append(f"{label} missing source citations")
    for source_id in citations:
        if source_id not in sources:
            errors.append(f"{label} references unknown source: {source_id}")


def validate_interval(value: dict[str, Any], label: str, errors: list[str]) -> None:
    if not isinstance(value, dict) or not value.get("start_date"):
        errors.append(f"{label} missing start_date")
        return
    validate_date(value.get("start_date"), f"{label} start_date", errors)
    validate_optional_date(value.get("end_date"), f"{label} end_date", errors)


def validate_date(value: Any, label: str, errors: list[str]) -> None:
    try:
        date.fromisoformat(str(value))
    except (TypeError, ValueError):
        errors.append(f"{label} must be YYYY-MM-DD")


def validate_optional_date(value: Any, label: str, errors: list[str]) -> None:
    if value not in (None, ""):
        validate_date(value, label, errors)


def require(row: dict[str, Any], fields: list[str], label: str, errors: list[str]) -> None:
    for field in fields:
        if field not in row or row.get(field) in (None, "", []):
            errors.append(f"{label} missing {field}")
