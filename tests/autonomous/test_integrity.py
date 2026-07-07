from pathlib import Path

from atlas.autonomous.confidence import build_scientific_confidence_report
from atlas.autonomous.director import build_director_report
from atlas.autonomous.export import build_autonomous_export_report
from atlas.autonomous.provenance import build_provenance_report
from atlas.autonomous.timeline import build_research_timeline_report


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


def test_director_integrity_stack():
    records = [make_record(i) for i in range(30)]

    report = build_director_report(
        records,
        max_schedule_items=1,
        export=False,
    )

    assert report["success"] is True
    assert report["health"]["success"] is True
    assert "scientific_confidence" in report
    assert "provenance" in report
    assert "timeline" in report
    assert report["checkpoints"]["checkpoint_count"] >= 1


def test_scientific_confidence_report_from_director_cycle():
    records = [make_record(i) for i in range(30)]
    director = build_director_report(records, max_schedule_items=1, export=False)

    cycle = director["lifecycle"]["cycle"]
    confidence = build_scientific_confidence_report(cycle)

    assert confidence["success"] is True
    assert 0.0 <= confidence["scientific_confidence"] <= 1.0
    assert confidence["confidence_label"]
    assert "components" in confidence


def test_provenance_report_from_director_cycle():
    records = [make_record(i) for i in range(30)]
    director = build_director_report(records, max_schedule_items=1, export=False)

    provenance = build_provenance_report(director["lifecycle"]["cycle"])

    assert provenance["success"] is True
    assert provenance["graph"]["summary"]["node_count"] >= 1
    assert provenance["graph"]["summary"]["edge_count"] >= 1
    assert provenance["registry"]["objects"]


def test_timeline_report_from_director():
    records = [make_record(i) for i in range(30)]
    director = build_director_report(records, max_schedule_items=1, export=False)

    timeline = build_research_timeline_report(director)

    assert timeline["success"] is True
    assert timeline["summary"]["event_count"] >= 1
    assert timeline["events"]
    assert timeline["text_summary"]


def test_export_package_contains_integrity_files(tmp_path):
    records = [make_record(i) for i in range(30)]
    director = build_director_report(records, max_schedule_items=1, export=False)
    cycle = director["lifecycle"]["cycle"]

    export = build_autonomous_export_report(
        cycle,
        output_dir=tmp_path / "autonomous",
    )

    files = export["export"]["files"]

    assert export["success"] is True
    assert "confidence" in files
    assert "confidence_json" in files
    assert "provenance" in files
    assert "provenance_json" in files
    assert "timeline" in files
    assert "timeline_json" in files

    for file_path in files.values():
        assert Path(file_path).exists()
