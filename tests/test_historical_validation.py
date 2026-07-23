import json
from pathlib import Path

from atlas.historical_validation.controls import (
    build_event_control_windows,
    holdout_split,
    placebo_dates,
    shuffled_relationship_edges,
)
from atlas.historical_validation.paths import OUTPUT_DIR, PILOT_REGISTRY_PATH
from atlas.historical_validation.interpretation import (
    build_interpretation_registry,
    compose_interpretation,
    contains_prohibited_claim,
    load_ontology,
    validate_ontology,
)
from atlas.historical_validation.registry import (
    load_registry,
    relationship_active,
    validate_registry,
)
from atlas.historical_validation.statistics import (
    apply_bh_fdr,
    fisher_exact_two_sided,
    permutation_distribution,
)
from atlas.historical_validation.transit import (
    applying_state,
    aspect_orb,
    build_pairwise_natal_contacts,
    build_window_exposures,
)
from atlas.services import historical_validation_service


def registry():
    return load_registry(PILOT_REGISTRY_PATH)


def test_registry_citations_and_evidence_references_resolve():
    payload = registry()
    assert validate_registry(payload) == []
    source_ids = {row["source_id"] for row in payload["sources"]}
    for collection in ("historical_events", "profile_participation", "dynamic_relationships"):
        for row in payload[collection]:
            assert row["source_citations"]
            assert set(row["source_citations"]) <= source_ids


def test_edison_tesla_registry_is_valid_and_honest_about_retrospection():
    path = PILOT_REGISTRY_PATH.with_name("edison_tesla_relationship_registry.json")
    payload = load_registry(path)
    assert payload["pilot_id"] == "edison_tesla_relationship_pilot_v1"
    assert all(row["source_citations"] for row in payload["profiles"])
    inspected = [row for row in payload["hypotheses"] if row["rationale_type"] == "symbolic_hypothesis"]
    assert inspected
    assert all(row["locked_before_run"] is False for row in inspected)
    assert all("retrospectively" in row["status"] for row in inspected)
    edison = next(row for row in payload["profiles"] if row["profile_key"] == "thomas_edison")
    assert edison["birth_time"] == "03:00"
    assert edison["birth_time_status"] == "estimated_historical"
    assert edison["birth_time_provenance"]["confidence"] == "low"


def test_edison_tesla_pairwise_contacts_are_geometric_and_time_bounded():
    path = PILOT_REGISTRY_PATH.with_name("edison_tesla_relationship_registry.json")
    payload = load_registry(path)
    contacts = build_pairwise_natal_contacts(payload["profiles"], payload["dynamic_relationships"][:1])
    saturn_venus = [
        row for row in contacts
        if row["profile_a_planet"] == "Saturn"
        and row["profile_b_planet"] == "Venus"
        and row["aspect"] == "trine"
    ]
    assert saturn_venus
    # Historical estimates are used centrally, while endpoint stability remains
    # mandatory so the estimate is not misrepresented as verified precision.
    assert saturn_venus[0]["orb_degrees"] < 0.2
    assert saturn_venus[0]["contact_stable_across_birth_time_range"] is True
    assert saturn_venus[0]["causal_claim"] is False
    assert saturn_venus[0]["houses_angles_included"] is False


def test_invalid_profile_source_reference_is_rejected():
    payload = registry()
    payload["profiles"][0]["source_citations"] = ["MISSING_SOURCE"]
    assert any("profile references unknown source" in error for error in validate_registry(payload))


def test_invalid_evidence_reference_is_rejected():
    payload = registry()
    payload["historical_events"][0]["source_citations"] = ["MISSING_SOURCE"]
    assert any("unknown source" in error for error in validate_registry(payload))


def test_relationship_interval_activation_is_inclusive_and_bounded():
    relationship = registry()["dynamic_relationships"][0]
    assert relationship_active(relationship, "1969-01-09") is True
    assert relationship_active(relationship, "1969-07-24") is True
    assert relationship_active(relationship, "1969-07-25") is False


def test_event_control_windows_do_not_overlap_registered_event_boundaries():
    payload = registry()
    windows = build_event_control_windows(payload)
    assert sum(row["window_kind"] == "event" for row in windows) == 12
    assert all(row["anchor_date"] for row in windows)
    event_dates = {row["start_date"] for row in payload["historical_events"]}
    assert all(row["anchor_date"] not in event_dates for row in windows if row["window_kind"] != "event")


def test_aspect_orb_and_applying_separating_boundaries():
    assert aspect_orb(10.0, 100.0, 90.0) == 0.0
    assert aspect_orb(359.0, 1.0, 0.0) == 2.0
    assert applying_state([4.0, 3.0, 2.0], 1) == "applying"
    assert applying_state([2.0, 3.0, 4.0], 1) == "separating"


def test_unknown_birth_time_produces_bounds_and_disables_houses():
    profile = registry()["profiles"][0]
    window = {
        "window_id": "test-window",
        "window_kind": "event",
        "anchor_date": "1969-07-20",
        "event_id": "apollo11_lunar_landing",
        "event_family": "apollo11_mission",
        "outcome_present": 1,
    }
    rows = build_window_exposures(profile, window, scan_days=2, max_orb=5.0)
    assert rows
    assert all(row["birth_time_known"] is False for row in rows)
    assert all(row["houses_angles_included"] is False for row in rows)
    assert all("noon is not treated as certain" in row["birth_time_policy"] for row in rows)
    assert any(row["fast_moon_uncertainty"] for row in rows)


def test_estimated_historical_time_is_used_centrally_but_not_marked_known():
    payload = load_registry(PILOT_REGISTRY_PATH.with_name("edison_tesla_relationship_registry.json"))
    profile = next(row for row in payload["profiles"] if row["profile_key"] == "thomas_edison")
    window = {"window_id": "estimate", "window_kind": "event", "anchor_date": "1884-06-06", "event_id": "tesla_arrives_new_york", "event_family": "edison_tesla_relationship", "outcome_present": 1}
    rows = build_window_exposures(profile, window, scan_days=1, max_orb=3.0)
    assert rows
    assert all(row["central_birth_time_used"] == "03:00" for row in rows)
    assert all(row["central_birth_time_status"] == "estimated_historical" for row in rows)
    assert all(row["birth_time_known"] is False for row in rows)
    assert all(row["houses_angles_included"] is False for row in rows)


def test_transit_calculation_is_deterministic():
    profile = registry()["profiles"][1]
    window = {"window_id": "det", "window_kind": "event", "anchor_date": "1969-07-16", "event_id": "apollo11_launch", "event_family": "apollo11_mission", "outcome_present": 1}
    first = build_window_exposures(profile, window, scan_days=1, max_orb=3.0)
    second = build_window_exposures(profile, window, scan_days=1, max_orb=3.0)
    assert first == second


def test_permutations_and_placebos_are_reproducible():
    observations = [
        {"outcome_present": 1, "exposed": 1},
        {"outcome_present": 1, "exposed": 0},
        {"outcome_present": 0, "exposed": 1},
        {"outcome_present": 0, "exposed": 0},
    ]
    assert permutation_distribution(observations, iterations=20, seed=7) == permutation_distribution(observations, iterations=20, seed=7)
    assert placebo_dates(["1969-07-20"], iterations=5, seed=9) == placebo_dates(["1969-07-20"], iterations=5, seed=9)


def test_multiple_testing_correction_and_exact_test():
    rows = [{"raw_p_value": 0.01}, {"raw_p_value": 0.04}, {"raw_p_value": 0.2}]
    apply_bh_fdr(rows, alpha=0.05)
    assert rows[0]["corrected_p_value"] <= rows[1]["corrected_p_value"]
    assert fisher_exact_two_sided(1, 9, 11, 3) < 0.01


def test_holdout_and_relationship_shuffle_are_separate_and_reproducible():
    split = holdout_split(["c", "a", "b"])
    assert set(split["discovery"]).isdisjoint(split["holdout"])
    assert set(split["discovery"] + split["holdout"]) == {"a", "b", "c"}
    assert shuffled_relationship_edges(["a", "b", "c"], 2, seed=4) == shuffled_relationship_edges(["a", "b", "c"], 2, seed=4)


def test_paths_are_absolute_and_independent_of_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert OUTPUT_DIR.is_absolute()
    assert PILOT_REGISTRY_PATH.is_absolute()
    assert load_registry(PILOT_REGISTRY_PATH)["pilot_id"] == "apollo11_crew_pilot_v1"


def test_dashboard_service_payload_filters_event_and_active_relationships(monkeypatch, tmp_path):
    output = tmp_path / "historical_validation"
    output.mkdir()
    write(output / "historical_validation_summary.json", {"version": "v", "counts": {"profiles": 2}})
    write(output / "historical_event_registry.json", [{"event_id": "e1", "name": "Event", "start_date": "2000-01-01"}])
    write(output / "dynamic_relationship_registry.json", [{"relationship_id": "r1", "source_profile": "a", "target_profile": "b", "start_date": "1999-01-01", "end_date": "2001-01-01"}])
    write(output / "cohort_quality_report.json", {"limitations": []})
    for name in ["profile_event_participation", "transit_exposure_matrix", "relationship_exposure_matrix", "event_control_windows", "transit_validation_results", "permutation_results", "missing_data_report"]:
        write(output / f"{name}.json", [])
    monkeypatch.setattr(historical_validation_service, "OUTPUT_DIR", output)
    payload = historical_validation_service.build_historical_validation_dashboard_payload(event_id="e1", selected_date="2000-01-01")
    assert payload["success"] is True
    assert payload["selected_event"]["event_id"] == "e1"
    assert len(payload["data"]["active_relationships"]) == 1


def test_interpretation_ontology_resolves_every_symbolic_source_reference():
    ontology = load_ontology()
    assert validate_ontology(ontology) == []
    assert ontology["causal_claims_allowed"] is False
    assert ontology["empirical_validation"] is False


def test_interpretation_composition_is_deterministic_and_noncausal():
    first = compose_interpretation(transit_planet="Saturn", natal_target="Sun", aspect="conjunction", phase="applying", retrograde=True, repeated_hit_count=2, birth_time_known=False)
    second = compose_interpretation(transit_planet="Saturn", natal_target="Sun", aspect="conjunction", phase="applying", retrograde=True, repeated_hit_count=2, birth_time_known=False)
    assert first == second
    assert first["claim_type"] == "symbolic_hypothesis"
    assert first["empirical_evidence"] is False
    assert first["causal_claim"] is False
    assert "planet.saturn" in first["ontology_refs"]
    assert contains_prohibited_claim(first["symbolic_statement"]) is False


def test_interpretation_registry_links_exposure_ids_without_hidden_meaning():
    exposure = {
        "exposure_id": "x1", "transit_planet": "Venus", "natal_target": "Jupiter",
        "aspect": "square", "applying_separating": "separating",
        "retrograde_at_anchor": False, "repeated_hit_count": 1, "birth_time_known": False,
    }
    records, mapping = build_interpretation_registry([exposure])
    assert len(records) == 1
    assert mapping["x1"] == records[0]["interpretation_id"]
    assert records[0]["directional_valence"] == "unspecified"


def test_prohibited_predictive_or_causal_language_is_detected():
    assert contains_prohibited_claim("This transit guarantees a certain outcome.") is True
    assert contains_prohibited_claim("This is a hypothesis for testing.") is False


def write(path: Path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
