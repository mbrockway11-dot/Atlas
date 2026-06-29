import json
from pathlib import Path

from atlas.temporal.birth import (
    build_birth_data_from_intake,
    is_birth_time_known,
    load_birth_data_from_profile,
    normalize_birth_time,
    normalize_optional_float,
)


def test_normalize_birth_time_unknown_values():
    assert normalize_birth_time("") == "Unknown"
    assert normalize_birth_time("unknown") == "Unknown"
    assert normalize_birth_time("N/A") == "Unknown"


def test_normalize_birth_time_known_value():
    assert normalize_birth_time("11:30") == "11:30"


def test_is_birth_time_known():
    assert is_birth_time_known("11:30") is True
    assert is_birth_time_known("Unknown") is False


def test_normalize_optional_float():
    assert normalize_optional_float("27.5") == 27.5
    assert normalize_optional_float("") is None
    assert normalize_optional_float("bad") is None


def test_build_birth_data_from_intake():
    birth = build_birth_data_from_intake(
        {
            "name": "Albert Einstein",
            "birth_date": "1879-03-14",
            "birth_time": "11:30",
            "birth_place": "Ulm",
            "latitude": "48.3984",
            "longitude": "9.9916",
            "timezone": "Europe/Berlin",
            "source_file": "historical_batch.csv",
            "row_number": 18,
        }
    )

    assert birth.name == "Albert Einstein"
    assert birth.birth_date == "1879-03-14"
    assert birth.birth_time == "11:30"
    assert birth.birth_place == "Ulm"
    assert birth.latitude == 48.3984
    assert birth.longitude == 9.9916
    assert birth.timezone == "Europe/Berlin"
    assert birth.time_known is True


def test_load_birth_data_from_profile(tmp_path: Path):
    profile_dir = tmp_path / "albert_einstein"
    profile_dir.mkdir()

    intake_path = profile_dir / "profile.intake.json"
    intake_path.write_text(
        json.dumps(
            {
                "name": "Albert Einstein",
                "birth_date": "1879-03-14",
                "birth_time": "11:30",
                "birth_place": "Ulm",
            }
        ),
        encoding="utf-8",
    )

    birth = load_birth_data_from_profile(profile_dir)

    assert birth.name == "Albert Einstein"
    assert birth.birth_date == "1879-03-14"
    assert birth.birth_time == "11:30"


def test_load_birth_data_missing_intake(tmp_path: Path):
    profile_dir = tmp_path / "missing"
    profile_dir.mkdir()

    birth = load_birth_data_from_profile(profile_dir)

    assert birth.name == "missing"
    assert birth.birth_time == "Unknown"
    assert birth.time_known is False