"""Canonical Research Corpus service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from atlas.acf.builder import build_acf_profile
from atlas.database import list_entities
from atlas.library.profile_library import LIBRARY_DIR, load_profile_interpretation


RESEARCH_CORPUS_SERVICE_VERSION = "3.0"


@dataclass(slots=True)
class ResearchCorpusPayload:
    """Canonical Research Corpus payload."""

    success: bool
    version: str
    entities: list[dict[str, Any]]
    rows: list[dict[str, Any]]
    metrics: dict[str, Any]
    warnings: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary payload."""
        return {
            "success": self.success,
            "version": self.version,
            "entities": self.entities,
            "rows": self.rows,
            "metrics": self.metrics,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def build_research_corpus_payload() -> ResearchCorpusPayload:
    """Build index-derived Research Corpus payload."""
    warnings: list[str] = []

    try:
        entities = list_entities()
    except Exception as exc:
        return ResearchCorpusPayload(
            success=False,
            version=RESEARCH_CORPUS_SERVICE_VERSION,
            entities=[],
            rows=[],
            metrics={
                "indexed_entities": 0,
                "row_count": 0,
                "load_errors": 1,
            },
            warnings=[],
            errors=[f"Could not list indexed entities: {exc}"],
        )

    rows = []

    for entity in entities:
        rows.append(build_entity_row(entity, warnings))

    load_errors = sum(
        1
        for row in rows
        if row.get("function") == "missing profile"
    )

    return ResearchCorpusPayload(
        success=True,
        version=RESEARCH_CORPUS_SERVICE_VERSION,
        entities=entities,
        rows=rows,
        metrics={
            "indexed_entities": len(entities),
            "row_count": len(rows),
            "load_errors": load_errors,
        },
        warnings=warnings,
        errors=[],
    )


def build_entity_row(entity: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    """Build a canonical corpus row for one indexed entity."""
    entity_id = entity["id"]
    name = entity["name"]

    base = {
        "entity_id": entity_id,
        "name": name,
        "entity_type": entity.get("entity_type", "unknown"),
        "tags": ", ".join(entity.get("tags", [])),
        "birth_confidence": entity.get("birth_confidence", "unknown"),
        "notes": entity.get("notes") or "",
    }

    try:
        interpretation = load_profile_interpretation(entity_id)
        classification = load_or_build_acf_classification(entity_id, name)

        return {
            **base,
            "function": classification["function"]["role"],
            "expression": classification["expression"]["type"],
            "state": classification["state"]["type"],
            "scale": classification["scale"],
            "analysis_count": interpretation["analysis_count"],
            "strongest_driver_planet": interpretation["strongest_driver"]["planet"],
            "strongest_driver_score": interpretation["strongest_driver"]["score"],
            "strongest_amplifier_planet": interpretation["strongest_amplifier"]["planet"],
            "strongest_amplifier_score": interpretation["strongest_amplifier"]["score"],
            "strongest_regulator_planet": interpretation["strongest_regulator"]["planet"],
            "strongest_regulator_score": interpretation["strongest_regulator"]["score"],
        }

    except Exception as exc:
        warnings.append(f"{entity_id}: {exc}")
        return {
            **base,
            "function": "missing profile",
            "expression": "missing profile",
            "state": "missing profile",
            "scale": "unknown",
            "analysis_count": None,
            "strongest_driver_planet": "",
            "strongest_driver_score": None,
            "strongest_amplifier_planet": "",
            "strongest_amplifier_score": None,
            "strongest_regulator_planet": "",
            "strongest_regulator_score": None,
            "notes": f"{base['notes']} | Load error: {exc}",
        }


def load_or_build_acf_classification(profile_key: str, name: str) -> dict[str, Any]:
    """Load classification from ACF if available, otherwise build it."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if acf_path.exists():
        data = json.loads(acf_path.read_text(encoding="utf-8"))
        classification = data.get("essence", {}).get("classification")

        if classification and "meanings" in classification:
            return classification

    acf = build_acf_profile(name=name)
    classification = acf["essence"]["classification"]

    acf_path.parent.mkdir(parents=True, exist_ok=True)
    acf_path.write_text(
        json.dumps(acf, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return classification