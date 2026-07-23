from atlas.autonomous.experiment_generator import (
    build_relationship_research_program,
)


def ready_pair():
    return {
        "pair_id": "a__b",
        "profile_a": "a",
        "profile_b": "b",
        "relationship_type": "documented_collaboration",
        "event_count": 8,
        "source_count": 6,
        "birth_time_status_a": "verified",
        "birth_time_status_b": "recorded",
        "evidence_status": "locked",
    }


def test_program_builds_competing_hypotheses_and_controls():
    report = build_relationship_research_program([ready_pair()], top_n=4)

    assert report["success"] is True
    assert report["selected_count"] == 4
    assert report["hypothesis_count"] == 12
    assert {row["model_role"] for row in report["hypotheses"]} == {
        "candidate_association",
        "null",
        "rival_confounder",
    }
    assert all(row["locked_before_run"] for row in report["hypotheses"])
    assert all(row["causal_claim"] is False for row in report["hypotheses"])


def test_incomplete_pair_routes_to_evidence_completion_before_outcome_testing():
    incomplete = {
        "profile_a": "edison",
        "profile_b": "ford",
        "birth_time_status_a": "estimated_historical",
        "birth_time_status_b": "estimated_historical",
    }
    report = build_relationship_research_program([incomplete], top_n=10)
    cohort = report["cohorts"][0]

    assert cohort["eligible_for_outcome_testing"] is False
    assert "EVENT_REGISTRY_NOT_LOCKED" in cohort["blockers"]
    assert any(
        row["stage"] == "data_acquisition"
        for row in report["selected_questions"]
    )
    assert all(
        row["stage"] in {"data_acquisition", "robustness"}
        for row in report["selected_questions"]
    )


def test_memory_lowers_repeated_question_novelty():
    memory = {
        "experiments": {
            "old": {
                "question_id": "relationship::a__b::birth_time_robustness"
            }
        }
    }
    report = build_relationship_research_program(
        [ready_pair()], memory=memory, top_n=10
    )
    repeated = next(
        row for row in report["questions"]
        if row["question_id"].endswith("birth_time_robustness")
    )
    assert repeated["novelty"] == 0.1
    assert repeated["already_in_memory"] is True
    assert repeated not in report["selected_questions"]


def test_completed_result_generates_the_correct_adaptive_branch():
    memory = {
        "experiments": {
            "old": {
                "question_id": "relationship::a__b::event_window_contrast",
                "status": "supported",
            }
        }
    }
    report = build_relationship_research_program(
        [ready_pair()], memory=memory, top_n=20
    )
    followup = next(
        row for row in report["questions"]
        if row.get("derived_from_status") == "supported"
    )
    assert followup["stage"] == "replication"
    assert followup["question_id"].endswith("independent_replication")
