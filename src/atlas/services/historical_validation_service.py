"""Dashboard service for historical event–relationship transit validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.historical_validation.paths import OUTPUT_DIR
from atlas.historical_validation.registry import relationship_active


def build_historical_validation_dashboard_payload(
    *,
    event_id: str | None = None,
    selected_date: str | None = None,
) -> dict[str, Any]:
    summary = read_json(OUTPUT_DIR / "historical_validation_summary.json")
    if not summary:
        return {"success": False, "errors": [f"Historical validation outputs not found: {OUTPUT_DIR}"], "warnings": [], "data": {}}
    events = read_json(OUTPUT_DIR / "historical_event_registry.json", default=[])
    relationships = read_json(OUTPUT_DIR / "dynamic_relationship_registry.json", default=[])
    participations = read_json(OUTPUT_DIR / "profile_event_participation.json", default=[])
    exposures = read_json(OUTPUT_DIR / "transit_exposure_matrix.json", default=[])
    relationship_exposures = read_json(OUTPUT_DIR / "relationship_exposure_matrix.json", default=[])
    windows = read_json(OUTPUT_DIR / "event_control_windows.json", default=[])
    validation = read_json(OUTPUT_DIR / "transit_validation_results.json", default=[])
    interpretations = read_json(OUTPUT_DIR / "transit_interpretation_registry.json", default=[])
    ontology = read_json(OUTPUT_DIR / "transit_interpretation_ontology.json")
    hypotheses = read_json(OUTPUT_DIR / "transit_hypothesis_registry.json", default=[])
    permutations = read_json(OUTPUT_DIR / "permutation_results.json", default=[])
    missing = read_json(OUTPUT_DIR / "missing_data_report.json", default=[])
    quality = read_json(OUTPUT_DIR / "cohort_quality_report.json")
    source_registry = read_source_registry()

    selected_event = next((row for row in events if row.get("event_id") == event_id), events[0] if events else {})
    resolved_date = selected_date or selected_event.get("start_date")
    active_relationships = [row for row in relationships if resolved_date and relationship_active(row, resolved_date)]
    selected_event_id = selected_event.get("event_id")
    return {
        "success": True,
        "version": summary.get("version"),
        "metrics": summary.get("counts", {}),
        "selected_event": selected_event,
        "selected_date": resolved_date,
        "event_options": [{"event_id": row.get("event_id"), "name": row.get("name"), "start_date": row.get("start_date")} for row in events],
        "data": {
            "events": events,
            "participations": [row for row in participations if not selected_event_id or row.get("event_id") == selected_event_id],
            "active_relationships": active_relationships,
            "exposures": [row for row in exposures if not selected_event_id or row.get("event_id") == selected_event_id],
            "relationship_exposures": [row for row in relationship_exposures if not selected_event_id or row.get("event_id") == selected_event_id],
            "windows": [row for row in windows if not selected_event_id or row.get("event_id") == selected_event_id],
            "validation": validation,
            "interpretations": interpretations,
            "ontology": ontology,
            "hypotheses": hypotheses,
            "permutations": permutations,
            "missing_data": missing,
            "quality": quality,
            "sources": source_registry,
        },
        "labels": {
            "astronomical": "Calculated astronomical geometry; not a causal claim",
            "historical": "Citation-linked documented facts",
            "statistical": "Pilot associations and falsification results",
            "symbolic": "Hypothesis rationale only; not empirical evidence",
        },
        "downloads": available_downloads(),
        "warnings": quality.get("limitations", []),
        "errors": [],
    }


def available_downloads() -> list[dict[str, str]]:
    return [
        {"name": path.name, "path": str(path)}
        for path in sorted(OUTPUT_DIR.iterdir())
        if path.is_file() and path.suffix in {".json", ".csv", ".md"}
    ] if OUTPUT_DIR.exists() else []


def read_source_registry() -> list[dict[str, Any]]:
    from atlas.historical_validation.paths import PILOT_REGISTRY_PATH
    payload = read_json(PILOT_REGISTRY_PATH)
    return payload.get("sources", []) if isinstance(payload, dict) else []


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {} if default is None else default
