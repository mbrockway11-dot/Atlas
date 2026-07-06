
from atlas.autonomous.evidence import (
    aggregate_evidence_confidence,
    build_evidence_from_causality,
    build_evidence_from_discovery,
    validate_evidence_records,
)


def test_evidence_from_discovery():
    report = {
        "correlation_scans": [
            {
                "question_id": "q1",
                "question": "Does A relate to B?",
                "x_field": "a",
                "y_field": "b",
                "sample_size": 50,
                "correlation": 0.8,
                "strength": "strong",
                "direction": "positive",
            }
        ]
    }

    records = build_evidence_from_discovery(report)

    assert len(records) == 1
    assert records[0]["source_engine"] == "discovery"
    assert validate_evidence_records(records)["success"] is True


def test_evidence_from_causality():
    report = {
        "causal_hypotheses": [
            {
                "candidate_id": "c1",
                "claim": "A may drive B.",
                "mechanism": "A activates B.",
                "cause": "a",
                "effect": "b",
                "sample_size": 50,
                "causal_confidence": 0.7,
                "correlation": 0.6,
                "causal_label": "moderate_causal_candidate",
                "direction": "positive",
            }
        ]
    }

    records = build_evidence_from_causality(report)

    assert len(records) == 1
    assert records[0]["source_engine"] == "causality"
    assert aggregate_evidence_confidence(records)["record_count"] == 1
