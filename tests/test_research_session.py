import json
from pathlib import Path

from atlas.research.session import (
    RESEARCH_SESSION_VERSION,
    build_research_session,
    export_research_session_json,
    export_research_session_markdown,
    research_session_to_dict,
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


def test_build_research_session(tmp_path: Path):
    session = build_research_session(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    assert session.version == RESEARCH_SESSION_VERSION
    assert session.name == "Albert Einstein"
    assert session.summary["has_identity"] is True
    assert session.summary["has_interpretation"] is True
    assert session.summary["has_report"] is True


def test_research_session_to_dict(tmp_path: Path):
    session = build_research_session(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    data = research_session_to_dict(session)

    assert data["version"] == RESEARCH_SESSION_VERSION
    assert data["name"] == "Albert Einstein"
    assert "identity" in data
    assert "interpretation" in data
    assert "report" in data


def test_export_research_session_json(tmp_path: Path):
    session = build_research_session(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    output = tmp_path / "session.json"

    export_research_session_json(
        session,
        output,
    )

    assert output.exists()
    assert "Albert Einstein" in output.read_text(encoding="utf-8")


def test_export_research_session_markdown(tmp_path: Path):
    session = build_research_session(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    output = tmp_path / "session.md"

    export_research_session_markdown(
        session,
        output,
    )

    assert output.exists()
    assert "Atlas Intelligence Report" in output.read_text(encoding="utf-8")