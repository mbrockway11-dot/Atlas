import json

from atlas.services import bulk_profile_codex_service as service


def write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_readiness_notes_explain_missing_profile_data(monkeypatch, tmp_path):
    profile_dir = tmp_path / "incomplete_person"
    profile_dir.mkdir()
    write_json(profile_dir / "profile.intake.json", {
        "identity": {"full_name": "Incomplete Person"},
        "birth": {"date": "", "time": "", "place": ""},
    })
    write_json(profile_dir / "profile.payload.json", {
        "identity": {"full_name": "Incomplete Person"},
        "birth": {"date": "", "time": "", "place": ""},
    })
    monkeypatch.setattr(service, "resolve_profile_dir", lambda key: profile_dir)

    record = service.build_profile_readiness(
        "incomplete_person",
        codex={
            "success": True,
            "symbolic_profile": {
                "numerology": {"available": True},
                "gematria": {"available": True},
            },
            "errors": [],
            "warnings": [],
        },
        population_members=set(),
    )

    gaps = {row["field"]: row for row in record["missing_data"]}
    assert record["status"] == "incomplete"
    assert record["core_complete"] is False
    assert gaps["birth.date"]["severity"] == "required"
    assert gaps["birth.time"]["severity"] == "recommended"
    assert gaps["population_v2"]["severity"] == "derived"
    assert any("Life Path" in note for note in record["notes"])


def test_readiness_marks_complete_profile_without_false_gaps(monkeypatch, tmp_path):
    profile_dir = tmp_path / "complete_person"
    profile_dir.mkdir()
    intake = {
        "identity": {"full_name": "Complete Person"},
        "birth": {"date": "1990-01-02", "time": "12:00", "place": "Miami, Florida"},
        "major_events": [{"date": "2020-01-01", "label": "Event"}],
        "source": {"url": "https://example.test"},
    }
    write_json(profile_dir / "profile.intake.json", intake)
    write_json(profile_dir / "profile.payload.json", {"identity": intake["identity"], "birth": intake["birth"]})
    write_json(profile_dir / "profile.acf.json", {})
    monkeypatch.setattr(service, "resolve_profile_dir", lambda key: profile_dir)

    record = service.build_profile_readiness(
        "complete_person",
        codex={
            "success": True,
            "symbolic_profile": {
                "numerology": {"available": True},
                "gematria": {"available": True},
            },
            "errors": [],
            "warnings": [],
        },
        population_members={"complete_person"},
    )

    assert record["status"] == "complete"
    assert record["core_complete"] is True
    assert record["enrichment_complete"] is True
    assert record["missing_data"] == []
