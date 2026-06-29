import json
from pathlib import Path

from atlas.identity_bridge import build_atlas_identity
from atlas.intelligence.interpreter import (
    INTERPRETER_VERSION,
    atlas_interpretation_to_dict,
    interpret_identity,
)


def _profile_dir(tmp_path: Path) -> Path:
    profile = tmp_path / "albert_einstein"
    profile.mkdir()

    (profile / "profile.acf.json").write_text(
        json.dumps(
            {
                "identity": {
                    "name": "Albert Einstein",
                }
            }
        ),
        encoding="utf-8",
    )

    (profile / "profile.intake.json").write_text(
        json.dumps(
            {
                "name": "Albert Einstein",
                "birth_date": "1879-03-14",
                "birth_time": "11:30",
                "birth_place": "Ulm",
                "latitude": 48.3984,
                "longitude": 9.9916,
                "timezone": "Europe/Berlin",
            }
        ),
        encoding="utf-8",
    )

    return profile


def test_interpret_identity(tmp_path: Path):
    identity = build_atlas_identity(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    interpretation = interpret_identity(identity)

    assert interpretation.version == INTERPRETER_VERSION
    assert interpretation.name == "Albert Einstein"
    assert interpretation.summary["section_count"] > 0

    titles = [
        section.title
        for section in interpretation.sections
    ]

    assert "Identity Overview" in titles
    assert "Temporal Overview" in titles
    assert "Natal Signature" in titles


def test_atlas_interpretation_to_dict(tmp_path: Path):
    identity = build_atlas_identity(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    interpretation = interpret_identity(identity)
    data = atlas_interpretation_to_dict(interpretation)

    assert data["version"] == INTERPRETER_VERSION
    assert data["name"] == "Albert Einstein"
    assert "sections" in data
    assert "summary" in data