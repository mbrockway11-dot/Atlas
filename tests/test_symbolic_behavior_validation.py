"""Tests for dependency-aware symbolic/behavior association research."""

from __future__ import annotations

import json

from atlas.services import symbolic_behavior_service
from atlas.symbolic_behavior import features as feature_module
from atlas.symbolic_behavior.features import extract_profile_features
from atlas.symbolic_behavior.registry import behavior_profile_index, validate_behavior_registry
from atlas.symbolic_behavior.statistics import build_independence_audit, evaluate_symbolic_behavior_associations
from atlas.symbolic_behavior.pipeline import build_annotation_readiness, build_population_coverage


def test_registry_requires_noncausal_blinded_annotation():
    payload = minimal_registry()
    assert validate_behavior_registry(payload, check_profiles=False) == []
    payload["causal_claims_allowed"] = True
    payload["symbolic_features_blinded_during_annotation"] = "unknown"
    errors = validate_behavior_registry(payload, check_profiles=False)
    assert "causal_claims_allowed must be false" in errors
    assert "symbolic_features_blinded_during_annotation must be boolean" in errors


def test_registry_rejects_unresolved_sources_and_unknown_behavior():
    payload = minimal_registry()
    payload["observations"][0]["source_refs"] = ["missing"]
    payload["observations"][0]["behavior_id"] = "unknown"
    errors = validate_behavior_registry(payload, check_profiles=False)
    assert any("unknown behavior_id" in error for error in errors)
    assert any("unresolved source refs" in error for error in errors)


def test_behavior_index_deduplicates_profiles():
    rows = [
        {"profile_key": "a", "behavior_id": "persistence"},
        {"profile_key": "a", "behavior_id": "persistence"},
        {"profile_key": "b", "behavior_id": "leadership"},
    ]
    assert behavior_profile_index(rows)["persistence"] == {"a"}


def test_feature_extraction_preserves_shared_input_dependencies(monkeypatch, tmp_path):
    codex = {
        "symbolic_profile": {
            "numerology": {"core_numbers": {"life_path": {"number": 8}, "expression": {"number": 3}, "maturity": {"number": 11}}},
            "gematria": {"systems": {"ordinal": {"digital_root": 3}}, "cross_system": {"distinct_root_count": 2, "exact_root_convergence": False}},
            "kamea": {"ranked_planets": [{"planet": "saturn", "composite_score": 0.8}]},
        }
    }
    payload = {"temporal": {"summary": {"time_known": False}, "natal": {"sidereal": {"planets": {"Sun": {"sign": "Cancer", "retrograde": False}}}}}}
    write(tmp_path / "structural_codex.json", codex)
    write(tmp_path / "profile.payload.json", payload)
    monkeypatch.setattr(feature_module, "resolve_profile_dir", lambda _: tmp_path)
    rows, quality = extract_profile_features("person")
    groups = {row["feature_id"]: row["independence_group"] for row in rows}
    assert groups["vedic.sun.sign"] == "birth_input"
    assert groups["numerology.life_path.number"] == "birth_input"
    assert groups["numerology.expression.number"] == "name_input"
    assert groups["numerology.maturity.number"] == "birth_and_name_input"
    assert groups["gematria.ordinal.digital_root"] == "name_input"
    assert groups["kamea.saturn.composite_score"] == "name_input"
    assert quality["houses_included"] is False


def test_small_cohort_never_retains_nominal_association():
    observations = [{"profile_key": key, "behavior_id": "behavior"} for key in ("a", "b")]
    observations += [{"profile_key": key, "behavior_id": "comparison"} for key in ("c", "d")]
    features = [feature(key, "x", "categorical", key in {"a", "b"}) for key in ("a", "b", "c", "d")]
    results = evaluate_symbolic_behavior_associations(observations, features, permutation_iterations=20)
    behavior_rows = [row for row in results if row["behavior_id"] == "behavior"]
    assert behavior_rows
    assert all(row["decision"] != "retained_for_independent_replication" for row in behavior_rows)
    assert all(row["causal_claim"] is False for row in behavior_rows)


def test_numeric_association_uses_deterministic_permutation():
    observations = [{"profile_key": f"p{i}", "behavior_id": "case" if i < 3 else "other"} for i in range(6)]
    features = [feature(f"p{i}", "score", "numeric", float(i < 3)) for i in range(6)]
    first = evaluate_symbolic_behavior_associations(observations, features, permutation_iterations=50, seed=7)
    second = evaluate_symbolic_behavior_associations(observations, features, permutation_iterations=50, seed=7)
    assert first == second
    assert any(row["test_type"] == "permutation_mean_difference" for row in first)


def test_independence_audit_counts_name_transforms_once():
    rows = [
        {"behavior_id": "b", "raw_p_value": 0.01, "corrected_significance": True, "independence_group": "name_input"},
        {"behavior_id": "b", "raw_p_value": 0.01, "corrected_significance": True, "independence_group": "name_input"},
        {"behavior_id": "b", "raw_p_value": 0.01, "corrected_significance": True, "independence_group": "birth_input"},
    ]
    audit = build_independence_audit(rows)[0]
    assert audit["corrected_associations"] == 3
    assert audit["independent_group_count"] == 2
    assert audit["cross_family_signal"] is True


def test_dashboard_service_filters_outputs(monkeypatch, tmp_path):
    write(tmp_path / "symbolic_behavior_summary.json", {"version": "v1", "counts": {"profiles": 2}})
    write(tmp_path / "behavior_observation_registry.json", [{"profile_key": "a", "behavior_id": "b1"}, {"profile_key": "b", "behavior_id": "b2"}])
    write(tmp_path / "symbolic_feature_matrix.json", [{"profile_key": "a", "feature_family": "vedic"}, {"profile_key": "b", "feature_family": "kamea"}])
    write(tmp_path / "symbolic_behavior_associations.json", [{"behavior_id": "b1", "feature_family": "vedic"}, {"behavior_id": "b2", "feature_family": "kamea"}])
    write(tmp_path / "behavior_taxonomy.json", [{"behavior_id": "b1"}, {"behavior_id": "b2"}])
    for name, value in [("independence_audit.json", []), ("profile_feature_quality.json", []), ("quality_report.json", {"limitations": []}), ("source_registry.json", [])]:
        write(tmp_path / name, value)
    monkeypatch.setattr(symbolic_behavior_service, "OUTPUT_DIR", tmp_path)
    payload = symbolic_behavior_service.build_symbolic_behavior_dashboard_payload(behavior_id="b1", feature_family="vedic")
    assert payload["success"] is True
    assert len(payload["data"]["observations"]) == 1
    assert len(payload["data"]["features"]) == 1
    assert len(payload["data"]["associations"]) == 1


def test_population_readiness_never_treats_missing_annotation_as_negative():
    quality = [
        {"profile_key": "a", "success": True, "feature_count": 4, "families": ["vedic"], "independence_groups": ["birth_input"], "birth_time_known": True},
        {"profile_key": "b", "success": True, "feature_count": 4, "families": ["vedic"], "independence_groups": ["birth_input"], "birth_time_known": False},
    ]
    observations = {"a": [{"behavior_id": "persistence"}]}
    rows = build_annotation_readiness(["a", "b"], quality, observations)
    missing = next(row for row in rows if row["profile_key"] == "b")
    assert missing["needs_behavior_annotation"] is True
    assert missing["eligible_as_behavior_negative"] is False
    assert missing["association_role"] == "predictor_only_not_an_outcome_control"


def test_population_coverage_counts_profiles_not_duplicate_feature_rows():
    features = [
        {"profile_key": "a", "feature_family": "vedic", "independence_group": "birth_input"},
        {"profile_key": "a", "feature_family": "vedic", "independence_group": "birth_input"},
        {"profile_key": "b", "feature_family": "vedic", "independence_group": "birth_input"},
    ]
    coverage = build_population_coverage(features, [{"profile_key": "a"}, {"profile_key": "b"}])[0]
    assert coverage["profile_count"] == 2
    assert coverage["feature_rows"] == 3
    assert coverage["profile_coverage"] == 1.0


def minimal_registry():
    return {
        "causal_claims_allowed": False,
        "symbolic_features_blinded_during_annotation": True,
        "sources": [{"source_id": "s1"}],
        "behavior_taxonomy": [{"behavior_id": "b1"}],
        "observations": [{
            "observation_id": "o1", "profile_key": "p1", "behavior_id": "b1",
            "observed_at": "2000-01-01", "date_precision": "day", "description": "Observed action",
            "confidence": 0.8, "source_refs": ["s1"],
        }],
    }


def feature(profile_key, feature_id, value_type, value):
    return {
        "profile_key": profile_key, "feature_id": feature_id,
        "feature_family": "gematria", "independence_group": "name_input",
        "input_dependencies": ["recorded_name"], "value_type": value_type,
        "value": value,
    }


def write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
