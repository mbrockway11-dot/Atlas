"""Read-only dashboard service for symbolic-behavior validation outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.symbolic_behavior.paths import OUTPUT_DIR


def build_symbolic_behavior_dashboard_payload(*, behavior_id: str | None = None, feature_family: str | None = None) -> dict[str, Any]:
    summary = read_json(OUTPUT_DIR / "symbolic_behavior_summary.json")
    if not summary:
        return {"success": False, "errors": [f"Symbolic-behavior outputs not found: {OUTPUT_DIR}"], "warnings": [], "data": {}}
    observations = read_json(OUTPUT_DIR / "behavior_observation_registry.json", [])
    features = read_json(OUTPUT_DIR / "symbolic_feature_matrix.json", [])
    associations = read_json(OUTPUT_DIR / "symbolic_behavior_associations.json", [])
    taxonomy = read_json(OUTPUT_DIR / "behavior_taxonomy.json", [])
    if behavior_id:
        associations = [row for row in associations if row.get("behavior_id") == behavior_id]
        observations = [row for row in observations if row.get("behavior_id") == behavior_id]
    if feature_family:
        associations = [row for row in associations if row.get("feature_family") == feature_family]
        features = [row for row in features if row.get("feature_family") == feature_family]
    return {
        "success": True,
        "version": summary.get("version"),
        "metrics": summary.get("counts", {}),
        "filters": {
            "behavior_options": sorted({row.get("behavior_id") for row in taxonomy if row.get("behavior_id")}),
            "feature_family_options": sorted({row.get("feature_family") for row in read_json(OUTPUT_DIR / "symbolic_feature_matrix.json", [])}),
            "behavior_id": behavior_id,
            "feature_family": feature_family,
        },
        "data": {
            "summary": summary, "taxonomy": taxonomy,
            "observations": observations, "features": features,
            "associations": associations,
            "independence_audit": read_json(OUTPUT_DIR / "independence_audit.json", []),
            "profile_quality": read_json(OUTPUT_DIR / "profile_feature_quality.json", []),
            "quality": read_json(OUTPUT_DIR / "quality_report.json"),
            "sources": read_json(OUTPUT_DIR / "source_registry.json", []),
            "population_summary": read_json(OUTPUT_DIR / "population_symbolic_feature_summary.json"),
            "population_readiness": read_json(OUTPUT_DIR / "population_annotation_readiness.json", []),
            "population_coverage": read_json(OUTPUT_DIR / "population_feature_coverage.json", []),
        },
        "downloads": [{"name": path.name, "path": str(path)} for path in sorted(OUTPUT_DIR.iterdir()) if path.is_file() and path.suffix in {".json", ".csv", ".md"}],
        "warnings": read_json(OUTPUT_DIR / "quality_report.json").get("limitations", []),
        "errors": [],
    }


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {} if default is None else default
