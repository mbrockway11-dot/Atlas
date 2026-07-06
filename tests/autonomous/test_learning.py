
from atlas.autonomous.learning import build_autonomous_learning_report


def make_record(index):
    return {
        "profile_key": f"profile_{index:03d}",
        "dynamics": {
            "dynamic_profile": {
                "recurrence": 0.2 + index * 0.001,
                "mean_energy": 3.0 + index * 0.01,
                "attractor_density": 1.0 + index * 0.01,
                "field_edge_count": 100 + index,
            },
            "prediction": {
                "recovery_probability": 0.5 + index * 0.001,
                "perturbation_sensitivity": 0.4 + index * 0.001,
            },
        },
    }


def test_autonomous_learning_report():
    records = [make_record(i) for i in range(30)]

    report = build_autonomous_learning_report(records, max_schedule_items=1)

    assert report["success"] is True
    assert report["learning_update"]["signal_count"] >= 1
    assert "Learning" in report["summary"] or "learning" in report["summary"]
