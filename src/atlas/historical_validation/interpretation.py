"""Deterministic composition of evidence-linked symbolic transit hypotheses."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from atlas.historical_validation.paths import RESEARCH_DIR


ONTOLOGY_PATH = RESEARCH_DIR / "transit_interpretation_ontology.v1.json"


def load_ontology(path: str | Path = ONTOLOGY_PATH) -> dict[str, Any]:
    ontology = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_ontology(ontology)
    if errors:
        raise ValueError("Invalid transit interpretation ontology: " + "; ".join(errors))
    return ontology


def validate_ontology(ontology: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_ids = {row.get("source_id") for row in ontology.get("sources", [])}
    if ontology.get("causal_claims_allowed") is not False:
        errors.append("causal_claims_allowed must be false")
    for collection in ("planets", "natal_targets", "aspects", "phase_modifiers", "modifiers"):
        for key, record in ontology.get(collection, {}).items():
            refs = record.get("source_refs", [])
            if not refs:
                errors.append(f"{collection}.{key} missing source_refs")
            if not set(refs) <= source_ids:
                errors.append(f"{collection}.{key} has unresolved source_refs")
    return errors


def compose_interpretation(
    *,
    transit_planet: str,
    natal_target: str,
    aspect: str,
    phase: str = "unspecified",
    retrograde: bool = False,
    repeated_hit_count: int = 0,
    birth_time_known: bool = True,
    ontology: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ontology = ontology or load_ontology()
    planet_key = transit_planet.casefold()
    target_key = natal_target.casefold()
    aspect_key = aspect.casefold()
    phase_key = phase if phase in ontology["phase_modifiers"] else "unspecified"
    planet = ontology["planets"].get(planet_key)
    target = ontology["natal_targets"].get(target_key)
    aspect_record = ontology["aspects"].get(aspect_key)
    if not planet or not target or not aspect_record:
        return {"success": False, "errors": ["Ontology does not define the requested planet, target, or aspect."]}
    refs = [f"planet.{planet_key}", f"natal_target.{target_key}", f"aspect.{aspect_key}", f"phase.{phase_key}"]
    modifiers = []
    if retrograde:
        refs.append("modifier.retrograde")
        modifiers.append(ontology["modifiers"]["retrograde"]["meaning"])
    if repeated_hit_count > 1:
        refs.append("modifier.repeated_hit")
        modifiers.append(ontology["modifiers"]["repeated_hit"]["meaning"])
    if not birth_time_known:
        refs.append("modifier.unknown_birth_time")
        modifiers.append(ontology["modifiers"]["unknown_birth_time"]["meaning"])
    eligible = sorted(set(planet["eligible_outcomes"]) & set(target["eligible_outcomes"]))
    signature = f"{planet_key}|{target_key}|{aspect_key}|{phase_key}|{int(retrograde)}|{int(repeated_hit_count > 1)}|{int(birth_time_known)}"
    statement = (
        f"Within {ontology['ontology_id']}, transit {planet['label']} themes "
        f"({', '.join(planet['themes'])}) are combined with {target['label']} functions "
        f"({', '.join(target['chart_functions'])}) through {aspect_record['symbolic_operation']}. "
        f"The measured phase is treated as {ontology['phase_modifiers'][phase_key]['meaning']}."
    )
    if modifiers:
        statement += " Modifiers: " + "; ".join(modifiers) + "."
    return {
        "success": True,
        "interpretation_id": "TI-" + sha256(signature.encode("utf-8")).hexdigest()[:16],
        "ontology_id": ontology["ontology_id"],
        "signature": signature,
        "transit_planet": transit_planet,
        "natal_target": natal_target,
        "aspect": aspect,
        "phase": phase_key,
        "symbolic_statement": statement,
        "symbolic_themes": {"planet": planet["themes"], "natal_target": target["chart_functions"], "aspect_operation": aspect_record["symbolic_operation"], "modifiers": modifiers},
        "eligible_outcome_categories": eligible,
        "ontology_refs": refs,
        "source_refs": sorted(set(planet["source_refs"] + target["source_refs"] + aspect_record["source_refs"] + ontology["phase_modifiers"][phase_key]["source_refs"])),
        "claim_type": "symbolic_hypothesis",
        "empirical_evidence": False,
        "causal_claim": False,
        "directional_valence": "unspecified",
        "limitations": ["This composition proposes a falsifiable association; it does not establish prediction or causation."],
        "errors": [],
    }


def build_interpretation_registry(exposures: list[dict[str, Any]], ontology: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, str]]:
    ontology = ontology or load_ontology()
    records: dict[str, dict[str, Any]] = {}
    exposure_map: dict[str, str] = {}
    for row in exposures:
        interpretation = compose_interpretation(
            transit_planet=row["transit_planet"], natal_target=row["natal_target"],
            aspect=row["aspect"], phase=row.get("applying_separating", "unspecified"),
            retrograde=bool(row.get("retrograde_at_anchor")),
            repeated_hit_count=int(row.get("repeated_hit_count") or 0),
            birth_time_known=bool(row.get("birth_time_known")), ontology=ontology,
        )
        if interpretation.get("success"):
            records[interpretation["interpretation_id"]] = interpretation
            exposure_map[row["exposure_id"]] = interpretation["interpretation_id"]
    return sorted(records.values(), key=lambda row: row["interpretation_id"]), exposure_map


def contains_prohibited_claim(text: str, ontology: dict[str, Any] | None = None) -> bool:
    ontology = ontology or load_ontology()
    lowered = text.casefold()
    return any(phrase.casefold() in lowered for phrase in ontology.get("prohibited_claims", []))
