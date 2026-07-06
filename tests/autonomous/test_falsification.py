
from atlas.autonomous.falsification import build_falsification_report


def test_falsification_report_challenges_theory():
    theories = [
        {
            "theory_id": "theory::dynamic_recovery",
            "label": "Dynamic Recovery Theory",
            "variables": ["recovery", "recurrence"],
            "theory_score": 0.8,
        }
    ]

    evidence = [
        {
            "evidence_id": "ev1",
            "variables": ["recovery", "recurrence"],
            "confidence": 0.9,
            "effect_size": 0.8,
            "status": "active",
            "metadata": {"direction": "positive"},
        }
    ]

    report = build_falsification_report(theories, evidence)

    assert report["success"] is True
    assert report["challenge_count"] == 1
    assert report["challenges"][0]["theory_id"] == "theory::dynamic_recovery"
