
from atlas.autonomous.theory import build_theory_report


def test_theory_report_promotes_supported_theory():
    evidence = [
        {
            "evidence_id": "ev1",
            "variables": [
                "dynamics.dynamic_profile.recurrence",
                "dynamics.prediction.recovery_probability",
            ],
            "confidence": 0.9,
            "effect_size": 0.9,
            "status": "active",
        },
        {
            "evidence_id": "ev2",
            "variables": [
                "dynamics.dynamic_profile.attractor_density",
                "dynamics.prediction.recovery_probability",
            ],
            "confidence": 0.85,
            "effect_size": 0.8,
            "status": "active",
        },
    ]

    report = build_theory_report(evidence, promotion_threshold=0.35)

    assert report["success"] is True
    assert report["candidate_count"] >= 1
    assert report["promoted_count"] >= 1
