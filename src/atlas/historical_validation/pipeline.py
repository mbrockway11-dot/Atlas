"""End-to-end Historical Event–Relationship Transit Validation pilot."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from atlas.historical_validation.controls import (
    build_event_control_windows,
    placebo_dates,
    shuffled_birth_assignments,
    shuffled_relationship_edges,
)
from atlas.historical_validation.paths import OUTPUT_DIR, PILOT_REGISTRY_PATH
from atlas.historical_validation.interpretation import (
    build_interpretation_registry,
    compose_interpretation,
    load_ontology,
)
from atlas.historical_validation.registry import load_registry, relationship_active
from atlas.historical_validation.statistics import validate_hypotheses
from atlas.historical_validation.transit import (
    build_pairwise_natal_contacts,
    build_transit_exposures,
)
from atlas.library.profile_library import list_saved_profiles


SYSTEM_VERSION = "atlas.historical-transit-validation.v1"


def run_historical_validation(
    *,
    registry_path: str | Path = PILOT_REGISTRY_PATH,
    output_dir: str | Path = OUTPUT_DIR,
    permutation_iterations: int = 1_000,
    seed: int = 19690720,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    ontology = load_ontology()
    run_output_dir = Path(output_dir).resolve()
    checkpoint_path = run_output_dir / "run_checkpoint.json"
    run_output_dir.mkdir(parents=True, exist_ok=True)
    write_json(checkpoint_path, {"version": SYSTEM_VERSION, "status": "running", "stage": "registry_loaded", "updated_at": now_utc()})

    events = registry["historical_events"]
    participation = registry["profile_participation"]
    relationships = registry["dynamic_relationships"]
    outcomes = build_lifecycle_outcomes(participation, events)
    windows = build_event_control_windows(registry)
    write_json(checkpoint_path, {"version": SYSTEM_VERSION, "status": "running", "stage": "controls_built", "window_count": len(windows), "updated_at": now_utc()})

    exposures = build_transit_exposures(registry["profiles"], windows, scan_days=15, max_orb=5.0)
    interpretations, exposure_interpretation_map = build_interpretation_registry(exposures, ontology)
    for row in exposures:
        row["interpretation_id"] = exposure_interpretation_map.get(row["exposure_id"])
    for hypothesis in registry["hypotheses"]:
        hypothesis["symbolic_interpretation"] = compose_interpretation(
            transit_planet=hypothesis["transit_planet"],
            natal_target=hypothesis["natal_target"],
            aspect=hypothesis["aspect"],
            phase="unspecified",
            ontology=ontology,
        )
    relationship_exposures = build_relationship_exposures(relationships, events, exposures)
    pairwise_contacts = build_pairwise_natal_contacts(registry["profiles"], relationships)
    write_json(checkpoint_path, {"version": SYSTEM_VERSION, "status": "running", "stage": "exposures_built", "exposure_count": len(exposures), "pairwise_contact_count": len(pairwise_contacts), "updated_at": now_utc()})

    validation, permutations = validate_hypotheses(
        registry["hypotheses"], windows, exposures, relationships,
        permutation_iterations=permutation_iterations, seed=seed,
        known_confounders=registry.get("known_confounders"),
    )
    hypothesis_map = {row["hypothesis_id"]: row for row in registry["hypotheses"]}
    for result in validation:
        result["symbolic_interpretation"] = hypothesis_map[result["hypothesis_id"]]["symbolic_interpretation"]
        result["symbolic_interpretation"]["empirical_status"] = {
            "decision": result["decision"],
            "raw_p_value": result["raw_p_value"],
            "corrected_p_value": result["corrected_p_value"],
            "replication_status": result["replication_status"],
        }
    missing = build_missing_data_report(registry, exposures)
    quality = build_quality_report(registry, windows, exposures, validation, missing)
    falsification = build_falsification_manifest(registry, seed=seed)
    audit = build_system_audit()

    write_registry_artifacts(registry, outcomes, output_dir=run_output_dir)
    write_pair("transit_exposure_matrix", exposures, output_dir=run_output_dir)
    write_json(run_output_dir / "transit_interpretation_ontology.json", ontology)
    write_pair("transit_interpretation_registry", interpretations, output_dir=run_output_dir)
    write_pair("relationship_exposure_matrix", relationship_exposures, output_dir=run_output_dir)
    write_pair("pairwise_natal_contact_matrix", pairwise_contacts, output_dir=run_output_dir)
    write_pair("event_control_windows", windows, output_dir=run_output_dir)
    write_pair("transit_hypothesis_registry", registry["hypotheses"], output_dir=run_output_dir)
    write_pair("transit_validation_results", validation, output_dir=run_output_dir)
    write_pair("permutation_results", permutations, output_dir=run_output_dir)
    write_pair("missing_data_report", missing, output_dir=run_output_dir)
    write_json(run_output_dir / "falsification_manifest.json", falsification)
    write_json(run_output_dir / "cohort_quality_report.json", quality)
    (run_output_dir / "cohort_quality_report.md").write_text(render_quality_markdown(quality), encoding="utf-8")
    (run_output_dir / "methodology_report.md").write_text(render_methodology(audit, quality), encoding="utf-8")
    write_json(run_output_dir / "system_audit.json", audit)

    summary = {
        "success": True,
        "version": SYSTEM_VERSION,
        "generated_at": now_utc(),
        "pilot_id": registry["pilot_id"],
        "research_only": True,
        "causal_claims_allowed": False,
        "counts": {
            "profiles": len(registry["profiles"]),
            "events": len(events),
            "participations": len(participation),
            "relationships": len(relationships),
            "lifecycle_outcomes": len(outcomes),
            "event_windows": sum(row["window_kind"] == "event" for row in windows),
            "control_windows": sum(row["window_kind"] != "event" for row in windows),
            "transit_exposures": len(exposures),
            "pairwise_natal_contacts": len(pairwise_contacts),
            "symbolic_interpretations": len(interpretations),
            "hypotheses": len(validation),
            "retained_findings": sum(row["decision"] == "retained_for_independent_replication" for row in validation),
            "not_retained_findings": sum(row["decision"] != "retained_for_independent_replication" for row in validation),
        },
        "findings": validation,
        "quality": quality,
        "output_dir": str(run_output_dir),
    }
    summary_path = run_output_dir / "historical_validation_summary.json"
    write_json(summary_path, summary)
    write_json(checkpoint_path, {"version": SYSTEM_VERSION, "status": "complete", "stage": "complete", "summary_path": str(summary_path), "updated_at": now_utc()})
    return summary


def build_lifecycle_outcomes(participation: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_map = {row["event_id"]: row for row in events}
    return [{
        "outcome_id": f"outcome:{row['profile_key']}:{row['event_id']}",
        "profile_key": row["profile_key"],
        "event_id": row["event_id"],
        "date": event_map[row["event_id"]]["start_date"],
        "date_precision": event_map[row["event_id"]]["date_precision"],
        "outcome_category": row["outcome_category"],
        "outcome_direction": row.get("outcome_direction"),
        "outcome_severity": row.get("outcome_severity"),
        "description": row.get("documented_outcome"),
        "source_citations": row.get("source_citations", []),
        "evidence_confidence": row.get("involvement_confidence", "unknown"),
        "evidence_type": "documented_historical_fact",
    } for row in participation]


def build_relationship_exposures(
    relationships: list[dict[str, Any]],
    events: list[dict[str, Any]],
    exposures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in exposures:
        if row["window_kind"] == "event":
            index.setdefault((row["profile_key"], row["event_id"]), []).append(row)
    output = []
    for relationship in relationships:
        for event in events:
            if event["event_id"] not in relationship.get("shared_event_ids", []):
                continue
            active = relationship_active(relationship, event["start_date"])
            source_rows = index.get((relationship["source_profile"], event["event_id"]), [])
            target_rows = index.get((relationship["target_profile"], event["event_id"]), [])
            source_defs = {contact_definition(row) for row in source_rows}
            target_defs = {contact_definition(row) for row in target_rows}
            output.append({
                "relationship_id": relationship["relationship_id"],
                "event_id": event["event_id"],
                "event_date": event["start_date"],
                "relationship_active": active,
                "profile_a": relationship["source_profile"],
                "profile_b": relationship["target_profile"],
                "profile_a_exposure_count": len(source_rows),
                "profile_b_exposure_count": len(target_rows),
                "simultaneous_shared_exposures": sorted(source_defs & target_defs),
                "simultaneous_shared_exposure_count": len(source_defs & target_defs),
                "a_to_b_directional_effect": None,
                "b_to_a_directional_effect": None,
                "directional_effect_status": "not_estimable_without_a_preregistered_relational_transit_method",
                "composite_contacts_included": False,
                "composite_disabled_reason": "no composite-chart method preregistered for pilot",
                "source_citations": relationship.get("source_citations", []),
                "evidence_type": "astronomical_calculation_plus_documented_relationship",
            })
    return output


def build_missing_data_report(registry: dict[str, Any], exposures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    library_keys = set(list_saved_profiles())
    output = []
    for profile in registry["profiles"]:
        missing = []
        if not profile.get("birth_date"):
            missing.append(note("birth.date", "required", "Planet-to-planet transit analysis disabled."))
        if profile.get("birth_time_status") != "known":
            missing.append(note("birth.time", "uncertain", "Houses and angles disabled; natal positions evaluated across 00:00/12:00/23:59; Moon contacts flagged."))
        if not profile.get("birth_place"):
            missing.append(note("birth.place", "recommended", "Location-dependent calculations disabled."))
        if not profile.get("source_citations"):
            missing.append(note("profile.source_citations", "required", "Historical identity facts are unverified."))
        if profile["profile_key"] not in library_keys:
            missing.append(note("atlas_profile_library", "identity_resolution", "Pilot identity is citation-backed but absent from the main library; similarly named unrelated profiles are not substituted."))
        unstable = sum(
            not row.get("contact_stable_across_birth_time_range", True)
            for row in exposures if row["profile_key"] == profile["profile_key"]
        )
        output.append({
            "record_type": "profile",
            "record_id": profile["profile_key"],
            "missing_or_uncertain": missing,
            "unstable_transit_contact_count": unstable,
            "preserved": True,
        })
    for relationship in registry["dynamic_relationships"]:
        gaps = []
        if not relationship.get("start_date"):
            gaps.append(note("relationship.start_date", "required", "Interval activation disabled."))
        if not relationship.get("end_date"):
            gaps.append(note("relationship.end_date", "uncertain", "Relationship treated as open-ended."))
        if not relationship.get("source_citations"):
            gaps.append(note("relationship.source_citations", "required", "Relationship cannot be treated as documented."))
        output.append({"record_type": "relationship", "record_id": relationship["relationship_id"], "missing_or_uncertain": gaps, "preserved": True})
    for event in registry["historical_events"]:
        gaps = []
        if not event.get("source_citations"):
            gaps.append(note("event.source_citations", "required", "Event excluded from factual analysis."))
        if event.get("date_precision") != "day":
            gaps.append(note("event.date_precision", "uncertain", "Transit window widened to match date precision."))
        output.append({"record_type": "event", "record_id": event["event_id"], "missing_or_uncertain": gaps, "preserved": True})
    return output


def build_quality_report(registry: dict[str, Any], windows: list[dict[str, Any]], exposures: list[dict[str, Any]], validation: list[dict[str, Any]], missing: list[dict[str, Any]]) -> dict[str, Any]:
    profile_notes = [row for row in missing if row["record_type"] == "profile"]
    default_limitations = [
        "Pilot sample size is not powered for general inference.",
        "Event windows are historically selected and may be correlated.",
        "Unknown or unverified birth times disable houses and angles and uncertainty-flag Moon contacts.",
    ]
    return {
        "pilot_id": registry["pilot_id"],
        "cohort_selection_basis": registry.get("cohort_selection_basis", "authoritative-source completeness and bounded documented collaboration, not attractive transit results"),
        "profile_count": len(registry["profiles"]),
        "event_count": len(registry["historical_events"]),
        "relationship_count": len(registry["dynamic_relationships"]),
        "event_window_count": sum(row["window_kind"] == "event" for row in windows),
        "control_window_count": sum(row["window_kind"] != "event" for row in windows),
        "exposure_count": len(exposures),
        "profiles_missing_birth_time": sum(profile.get("birth_time_status") != "known" for profile in registry["profiles"]),
        "profiles_missing_birth_date": sum(not profile.get("birth_date") for profile in registry["profiles"]),
        "profiles_absent_from_main_library": sum(any(gap["field"] == "atlas_profile_library" for gap in row["missing_or_uncertain"]) for row in profile_notes),
        "events_missing_citations": sum(not row.get("source_citations") for row in registry["historical_events"]),
        "relationships_missing_citations": sum(not row.get("source_citations") for row in registry["dynamic_relationships"]),
        "retained_findings": sum(row["decision"] == "retained_for_independent_replication" for row in validation),
        "rejected_or_not_retained_findings": sum(row["decision"] != "retained_for_independent_replication" for row in validation),
        "limitations": registry.get("known_confounders", default_limitations) + [
            "No finding may be called validated from this pilot."
        ],
    }


def build_falsification_manifest(registry: dict[str, Any], *, seed: int) -> dict[str, Any]:
    profiles = registry["profiles"]
    event_dates = [row["start_date"] for row in registry["historical_events"]]
    keys = [row["profile_key"] for row in profiles]
    births = [row["birth_date"] for row in profiles]
    return {
        "seed": seed,
        "placebo_event_dates": placebo_dates(event_dates, iterations=100, seed=seed),
        "shuffled_birth_dates": shuffled_birth_assignments(keys, births, iterations=100, seed=seed + 1),
        "shuffled_relationship_edges": shuffled_relationship_edges(keys, len(registry["dynamic_relationships"]), seed=seed + 2),
        "negative_control_hypotheses": [row["hypothesis_id"] for row in registry["hypotheses"] if row.get("rationale_type") == "negative_control"],
        "relationship_control_status": "not_estimable_complete_three-person_network_has_no_unconnected_pairs",
        "shared_event_control_status": "not_estimable_all_pilot_participants_share_positive_outcomes",
        "matched_contemporary_status": "not_run_no_citation-complete_matched_control_cohort_in_pilot",
    }


def build_system_audit() -> dict[str, Any]:
    return {
        "usable": [
            "profile library and canonical payload path services",
            "Swiss Ephemeris tropical geocentric planetary calculations",
            "population and graph service conventions",
            "evidence/confidence payload conventions",
            "Streamlit dashboard service boundary",
            "profile readiness reports",
        ],
        "partially_integrated": [
            "existing transit engine is sign-contact oriented and lacks orb/exactness/duration controls",
            "relationship intelligence compares static structure but does not store sourced time-bounded relationships",
            "lifecycle service accepts events but corpus event coverage is sparse",
            "unknown birth time is normalized but lower-level ephemeris defaults to noon; this pilot adds explicit uncertainty bounds",
        ],
        "duplicated": [
            "temporal/aspects.py and temporal/atlas_overlay.py expose overlapping aspect-chart implementations",
            "temporal/ephemeris.py and temporal/geocoder.py contain overlapping ephemeris wrappers",
        ],
        "missing_before_pilot": [
            "normalized sourced event/participation/dynamic-relationship registries",
            "event/control windows and falsification randomizations",
            "orb-based applying/separating transit exposure matrix",
            "Fisher exact tests, permutation tests, BH-FDR, and holdout reporting",
            "historical transit validation dashboard",
        ],
        "separation": "No atlas.investment or trading execution module is imported or modified.",
    }


def write_registry_artifacts(registry: dict[str, Any], outcomes: list[dict[str, Any]], *, output_dir: Path = OUTPUT_DIR) -> None:
    write_pair("historical_event_registry", registry["historical_events"], output_dir=output_dir)
    write_pair("profile_event_participation", registry["profile_participation"], output_dir=output_dir)
    write_pair("dynamic_relationship_registry", registry["dynamic_relationships"], output_dir=output_dir)
    write_pair("lifecycle_outcome_registry", outcomes, output_dir=output_dir)


def write_pair(stem: str, rows: list[dict[str, Any]], *, output_dir: Path = OUTPUT_DIR) -> None:
    write_json(output_dir / f"{stem}.json", rows)
    write_csv(output_dir / f"{stem}.csv", rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row.get(key)) for key in keys})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def contact_definition(row: dict[str, Any]) -> str:
    return f"{row['transit_planet']} {row['aspect']} {row['natal_target']}"


def note(field: str, severity: str, impact: str) -> dict[str, str]:
    return {"field": field, "severity": severity, "impact": impact}


def render_quality_markdown(quality: dict[str, Any]) -> str:
    lines = ["# Cohort Quality Report", "", f"Pilot: `{quality['pilot_id']}`", "", f"Profiles: **{quality['profile_count']}**", f"Events: **{quality['event_count']}**", f"Relationships: **{quality['relationship_count']}**", f"Event/control windows: **{quality['event_window_count']} / {quality['control_window_count']}**", f"Missing birth times: **{quality['profiles_missing_birth_time']}**", f"Retained findings: **{quality['retained_findings']}**", "", "## Limitations", ""]
    lines.extend(f"- {item}" for item in quality["limitations"])
    return "\n".join(lines) + "\n"


def render_methodology(audit: dict[str, Any], quality: dict[str, Any]) -> str:
    return """# Historical Event–Relationship Transit Validation Methodology

## Claim separation

- Astronomical calculations: Swiss Ephemeris longitudes and explicitly defined aspects.
- Historical facts: accepted only from citation-linked registry records.
- Statistical associations: matched rate differences, odds ratios, Fisher tests, permutations, BH-FDR, and locked holdout summaries.
- Symbolic interpretations: hypothesis rationale only; never evidence of causality.
- Unsupported hypotheses: reported as not retained or not estimable.

## Transit interpretation ontology

Symbolic meanings are composed from the versioned `atlas.transit-interpretation-ontology.v1`. Every component resolves to ontology and source references. The ontology uses Ptolemy's *Tetrabiblos* only as historical provenance and an explicit Atlas operational convention for machine-testable definitions. Symbolic content never contributes to p-values, effect sizes, evidence confidence, or causal status.

## Pilot design

The selected pilot and its selection basis are recorded in the registry and quality report. Event windows are compared with same-person shifted non-event windows. Correlated events and retrospective hypotheses are reported as limitations, so this is a pipeline and exploratory-association test—not substantive validation of transit claims.

## Astronomical uncertainty

Unknown birth times are evaluated at 00:00, 12:00, and 23:59 UT. Noon is a computational center, not asserted as the birth time. Houses and angles are excluded. Moon contacts and contacts that change classification across the daily range are flagged.

## Falsification

The run includes deterministic placebo dates, shuffled birth assignments, shuffled relationship edges, a preregistered negative-control hypothesis, permutation tests, BH false-discovery-rate correction, and a profile-level discovery/holdout split. Shared-event differential-outcome and unconnected-pair relationship controls are not estimable in this three-person all-positive pilot.

## Decision rule

No result is retained without adequate sample size, corrected significance, and same-direction holdout performance. No causal claims are permitted.

## Known limitations

""" + "\n".join(f"- {item}" for item in quality["limitations"]) + "\n\n## Existing-system audit\n\n" + "\n".join(f"- **{key}:** " + "; ".join(values) for key, values in audit.items() if isinstance(values, list)) + f"\n- **Separation:** {audit['separation']}\n"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
