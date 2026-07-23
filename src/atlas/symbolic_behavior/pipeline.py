"""End-to-end research pipeline for symbolic-feature/behavior associations."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.symbolic_behavior.features import extract_profile_features
from atlas.symbolic_behavior.features import extract_symbolic_feature_matrix
from atlas.symbolic_behavior.paths import CHECKPOINT_PATH, OUTPUT_DIR, PILOT_REGISTRY_PATH, output_path
from atlas.symbolic_behavior.registry import load_behavior_registry
from atlas.symbolic_behavior.statistics import build_independence_audit, evaluate_symbolic_behavior_associations


SYSTEM_VERSION = "atlas.symbolic-behavior-validation.v1"


def run_symbolic_behavior_validation(
    *,
    registry_path: str | Path = PILOT_REGISTRY_PATH,
    permutation_iterations: int = 1_000,
    seed: int = 8675309,
) -> dict[str, Any]:
    registry = load_behavior_registry(registry_path)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint("registry_loaded")
    observations = registry["observations"]
    profile_keys = sorted({row["profile_key"] for row in observations})
    features, feature_quality = extract_symbolic_feature_matrix(profile_keys)
    checkpoint("features_extracted", feature_count=len(features))
    associations = evaluate_symbolic_behavior_associations(
        observations, features,
        permutation_iterations=permutation_iterations,
        seed=seed,
        annotation_blinded=registry["symbolic_features_blinded_during_annotation"],
    )
    independence = build_independence_audit(associations)
    quality = build_quality_report(registry, features, feature_quality, associations)

    write_pair("behavior_observation_registry", observations)
    write_pair("symbolic_feature_matrix", features)
    write_pair("symbolic_behavior_associations", associations)
    write_pair("independence_audit", independence)
    write_pair("profile_feature_quality", feature_quality)
    write_json(output_path("behavior_taxonomy.json"), registry["behavior_taxonomy"])
    write_json(output_path("source_registry.json"), registry["sources"])
    write_json(output_path("quality_report.json"), quality)
    output_path("methodology_report.md").write_text(render_methodology(quality), encoding="utf-8")

    summary = {
        "success": True,
        "version": SYSTEM_VERSION,
        "pilot_id": registry["pilot_id"],
        "generated_at": now_utc(),
        "research_only": True,
        "causal_claims_allowed": False,
        "counts": {
            "profiles": len(profile_keys),
            "behavior_observations": len(observations),
            "behavior_categories": len({row["behavior_id"] for row in observations}),
            "symbolic_features": len(features),
            "tested_associations": len(associations),
            "nominal_associations": sum(row["raw_p_value"] <= 0.05 for row in associations),
            "corrected_associations": sum(row["corrected_significance"] for row in associations),
            "retained_findings": sum(row["decision"] == "retained_for_independent_replication" for row in associations),
            "cross_family_signals": sum(row["cross_family_signal"] for row in independence),
        },
        "quality": quality,
        "output_dir": str(OUTPUT_DIR),
    }
    write_json(output_path("symbolic_behavior_summary.json"), summary)
    checkpoint("complete", summary_path=str(output_path("symbolic_behavior_summary.json")))
    return summary


def run_population_symbolic_feature_index(
    *,
    registry_path: str | Path = PILOT_REGISTRY_PATH,
    profile_keys: list[str] | None = None,
    force: bool = False,
    output_dir: str | Path = OUTPUT_DIR,
) -> dict[str, Any]:
    """Index all local profiles without treating unannotated profiles as controls."""
    registry = load_behavior_registry(registry_path)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    cache_dir = root / "population_feature_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    keys = sorted(set(profile_keys if profile_keys is not None else list_saved_profiles()))
    observation_index: dict[str, list[dict[str, Any]]] = {}
    for observation in registry["observations"]:
        observation_index.setdefault(observation["profile_key"], []).append(observation)
    all_features: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    cache_hits = 0
    for index, profile_key in enumerate(keys, start=1):
        cache_path = cache_dir / f"{profile_key}.json"
        cached = read_json(cache_path) if cache_path.exists() and not force else {}
        if cached.get("profile_key") == profile_key and isinstance(cached.get("features"), list):
            rows = cached["features"]
            quality = cached.get("quality", {})
            cache_hits += 1
        else:
            rows, quality = extract_profile_features(profile_key)
            write_json(cache_path, {"profile_key": profile_key, "features": rows, "quality": quality})
        all_features.extend(rows)
        quality_rows.append(quality)
        if index == 1 or index % 50 == 0 or index == len(keys):
            write_json(root / "population_run_checkpoint.json", {
                "version": SYSTEM_VERSION, "status": "running", "stage": "feature_index",
                "completed_profiles": index, "total_profiles": len(keys),
                "feature_rows": len(all_features), "cache_hits": cache_hits,
                "current_profile": profile_key, "updated_at": now_utc(),
            })
    readiness = build_annotation_readiness(keys, quality_rows, observation_index)
    coverage = build_population_coverage(all_features, readiness)
    write_pair_to(root, "population_symbolic_feature_matrix", all_features)
    write_pair_to(root, "population_annotation_readiness", readiness)
    write_pair_to(root, "population_profile_feature_quality", quality_rows)
    write_pair_to(root, "population_feature_coverage", coverage)
    summary = {
        "success": True,
        "version": SYSTEM_VERSION,
        "generated_at": now_utc(),
        "research_only": True,
        "unannotated_profiles_used_as_behavior_negative": False,
        "counts": {
            "profiles": len(keys),
            "feature_ready_profiles": sum(row["symbolic_feature_ready"] for row in readiness),
            "feature_rows": len(all_features),
            "behavior_annotated_profiles": sum(row["behavior_observation_count"] > 0 for row in readiness),
            "profiles_needing_behavior_annotation": sum(row["needs_behavior_annotation"] for row in readiness),
            "cache_hits": cache_hits,
        },
        "limitations": [
            "Population indexing supplies predictors, not behavioral outcomes.",
            "Profiles without cited observations are never treated as behavior-negative controls.",
            "The existing five-profile behavior pilot is unblinded and cannot retain findings.",
            "A blinded annotation protocol and independent replication remain required.",
        ],
        "output_dir": str(root),
    }
    write_json(root / "population_symbolic_feature_summary.json", summary)
    write_json(root / "population_run_checkpoint.json", {
        "version": SYSTEM_VERSION, "status": "complete", "stage": "complete",
        "completed_profiles": len(keys), "total_profiles": len(keys),
        "feature_rows": len(all_features), "cache_hits": cache_hits,
        "summary_path": str(root / "population_symbolic_feature_summary.json"),
        "updated_at": now_utc(),
    })
    return summary


def build_annotation_readiness(profile_keys: list[str], quality_rows: list[dict[str, Any]], observation_index: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    quality_index = {row.get("profile_key"): row for row in quality_rows}
    output: list[dict[str, Any]] = []
    for profile_key in profile_keys:
        quality = quality_index.get(profile_key, {})
        observations = observation_index.get(profile_key, [])
        output.append({
            "profile_key": profile_key,
            "symbolic_feature_ready": bool(quality.get("success")),
            "symbolic_feature_count": int(quality.get("feature_count") or 0),
            "feature_families": quality.get("families", []),
            "independence_groups": quality.get("independence_groups", []),
            "birth_time_known": bool(quality.get("birth_time_known")),
            "behavior_observation_count": len(observations),
            "documented_behaviors": sorted({row["behavior_id"] for row in observations}),
            "behavior_annotation_status": "source_cited_unblinded_pilot" if observations else "missing_behavior_observations",
            "needs_behavior_annotation": not bool(observations),
            "eligible_as_behavior_negative": False,
            "association_role": "documented_pilot_profile" if observations else "predictor_only_not_an_outcome_control",
        })
    return output


def build_population_coverage(features: list[dict[str, Any]], readiness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, set[str] | int]] = {}
    for row in features:
        key = (row["feature_family"], row["independence_group"])
        record = groups.setdefault(key, {"profiles": set(), "feature_rows": 0})
        record["profiles"].add(row["profile_key"])
        record["feature_rows"] += 1
    total = len(readiness)
    return [{
        "feature_family": family,
        "independence_group": independence,
        "profile_count": len(record["profiles"]),
        "profile_coverage": round(len(record["profiles"]) / max(total, 1), 6),
        "feature_rows": record["feature_rows"],
    } for (family, independence), record in sorted(groups.items())]


def build_quality_report(registry: dict[str, Any], features: list[dict[str, Any]], feature_quality: list[dict[str, Any]], associations: list[dict[str, Any]]) -> dict[str, Any]:
    profile_count = len({row["profile_key"] for row in registry["observations"]})
    return {
        "pilot_status": "pipeline_validation_only",
        "profile_count": profile_count,
        "symbolic_features_blinded_during_annotation": registry["symbolic_features_blinded_during_annotation"],
        "source_coverage": round(sum(bool(row.get("source_refs")) for row in registry["observations"]) / max(len(registry["observations"]), 1), 6),
        "feature_families": sorted({row["feature_family"] for row in features}),
        "independence_groups": sorted({row["independence_group"] for row in features}),
        "unknown_birth_time_profiles": sorted(row["profile_key"] for row in feature_quality if not row.get("birth_time_known")),
        "retained_findings": sum(row.get("decision") == "retained_for_independent_replication" for row in associations),
        "limitations": [
            f"Only {profile_count} profiles are included; the pilot cannot validate behavioral associations.",
            "Registry non-membership means not documented here, not behavioral absence.",
            "Public figures are a selected and historically heterogeneous cohort.",
            "Behavior coding can contain interpretation bias despite source citations.",
            "This development pilot was not blinded and cannot retain a finding.",
            "Unknown birth times disable houses and angles.",
            "Name spelling, transliteration, aliases, and recorded-name selection affect all name-derived transforms.",
            "Kamea, Gematria, and name numerology share recorded-name input and are not independent confirmations.",
            "Birth-date numerology and Vedic placements share birth-date input and require dependency-aware interpretation.",
            "No causal, diagnostic, predictive, or compatibility claim is permitted.",
        ],
        "promotion_requirements": {
            "minimum_profiles": 30,
            "minimum_profiles_per_behavior": 10,
            "fdr_alpha": 0.05,
            "blinded_behavior_annotation_required": True,
            "independent_replication_required": True,
            "prospective_validation_required_for_prediction": True,
        },
    }


def render_methodology(quality: dict[str, Any]) -> str:
    limitations = "\n".join(f"- {item}" for item in quality["limitations"])
    return f"""# Symbolic–Behavior Correlation Methodology

## Scope

Atlas compares deterministic symbolic features with independently cited behavioral observations. It tests association only. It does not infer personality, fate, compatibility, prediction, or causation.

## Evidence families

- `birth_input`: sidereal planetary features and birth-date numerology share birth input and count once.
- `name_input`: name numerology, Gematria, and Kamea share the recorded name and count once.
- `birth_and_name_input`: jointly derived features never count as an additional independent confirmation.

Houses and angles are excluded even when present in order to keep the pilot comparable across unknown birth times. Time-varying numerology cycles are also excluded because the stored Structural Codex compilation date is not the observation date.

## Statistics

Categorical features use two-sided Fisher exact tests. Numeric features use deterministic label-permutation mean-difference tests. Benjamini–Hochberg correction is applied across the complete pilot family. Findings require blinded behavior annotation, at least 30 profiles, at least 10 behavior-positive profiles, corrected significance, and later independent replication before retention.

## Limitations

{limitations}
"""


def write_pair(stem: str, rows: list[dict[str, Any]]) -> None:
    write_json(output_path(f"{stem}.json"), rows)
    write_csv(output_path(f"{stem}.csv"), rows)


def write_pair_to(root: Path, stem: str, rows: list[dict[str, Any]]) -> None:
    write_json(root / f"{stem}.json", rows)
    write_csv(root / f"{stem}.csv", rows)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row.get(key)) for key in fieldnames})


def csv_value(value: Any) -> Any:
    return json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value


def checkpoint(stage: str, **details: Any) -> None:
    write_json(CHECKPOINT_PATH, {"version": SYSTEM_VERSION, "status": "complete" if stage == "complete" else "running", "stage": stage, "updated_at": now_utc(), **details})


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
