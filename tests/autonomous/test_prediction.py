
from atlas.autonomous.prediction import build_prediction_challenge_report


def make_record(index):
    return {
        "profile_key": f"profile_{index:03d}",
        "dynamics": {
            "prediction": {
                "recovery_probability": 0.5 + index * 0.001,
                "perturbation_sensitivity": 0.4 + index * 0.001,
            },
            "dynamic_profile": {
                "recurrence": 0.2 + index * 0.001,
            },
        },
    }


def test_prediction_challenge_report():
    records = [make_record(i) for i in range(30)]

    report = build_prediction_challenge_report(records)

    assert report["success"] is True
    assert "Prediction benchmark trained" in report["summary"]
    assert report["benchmark"]["scores"]["valid_prediction_count"] > 0
