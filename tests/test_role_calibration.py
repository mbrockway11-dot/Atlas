from atlas.classification.role_calibration import (
    CALIBRATION_METRICS,
    build_metric_separation,
    calibrate_functional_roles_v2,
    detect_role_drift,
)
from atlas.classification.functional_role_v2 import classify_functional_role_v2
from atlas.research import build_research_matrix


def test_role_calibration_builds_report():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
            "Alan Turing",
        ]
    )

    report = calibrate_functional_roles_v2(rows)

    assert report["valid"] is True
    assert report["row_count"] == len(rows)
    assert report["metric_count"] > 0
    assert report["role_distribution"]
    assert report["metric_separation"]
    assert report["learned_weights"]
    assert report["drift"]


def test_metric_separation_has_expected_fields():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    classified_rows = [
        {
            "row": row,
            "classification": classify_functional_role_v2(row),
        }
        for row in rows
    ]

    separation = build_metric_separation(classified_rows)

    assert separation

    first = separation[0]

    assert "metric" in first
    assert "between_role_variance" in first
    assert "within_role_variance" in first
    assert "separation_score" in first
    assert "role_means" in first


def test_learned_weights_are_normalized_per_role():
    rows = build_research_matrix(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
            "Alan Turing",
        ]
    )

    report = calibrate_functional_roles_v2(rows)

    for weights in report["learned_weights"].values():
        if not weights:
            continue

        total = sum(record["weight"] for record in weights)

        assert abs(total - 1.0) < 0.000001


def test_role_drift_detection_statuses():
    balanced = detect_role_drift(
        [
            {"role": "Driver", "ratio": 0.2},
            {"role": "Amplifier", "ratio": 0.2},
            {"role": "Regulator", "ratio": 0.2},
            {"role": "Integrator", "ratio": 0.2},
            {"role": "Explorer", "ratio": 0.2},
        ]
    )

    severe = detect_role_drift(
        [
            {"role": "Driver", "ratio": 0.8},
            {"role": "Amplifier", "ratio": 0.05},
            {"role": "Regulator", "ratio": 0.05},
            {"role": "Integrator", "ratio": 0.05},
            {"role": "Explorer", "ratio": 0.05},
        ]
    )

    assert balanced["status"] == "balanced"
    assert severe["status"] == "severe_drift"


def test_calibration_metrics_list_is_not_empty():
    assert CALIBRATION_METRICS