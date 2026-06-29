import json
from pathlib import Path

from atlas.identity_bridge import build_atlas_identity
from atlas.intelligence.interpreter import interpret_identity
from atlas.intelligence.report import (
    REPORT_ENGINE_VERSION,
    atlas_report_to_dict,
    build_atlas_report,
    export_atlas_report_json,
    export_atlas_report_markdown,
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


def _report(tmp_path: Path):
    identity = build_atlas_identity(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )
    interpretation = interpret_identity(identity)
    report = build_atlas_report(interpretation)

    return report, interpretation


def test_build_atlas_report(tmp_path: Path):
    report, _interpretation = _report(tmp_path)

    assert report.version == REPORT_ENGINE_VERSION
    assert report.name == "Albert Einstein"
    assert "Atlas Intelligence Report" in report.markdown
    assert "Executive Summary" in report.markdown


def test_atlas_report_to_dict(tmp_path: Path):
    report, _interpretation = _report(tmp_path)

    data = atlas_report_to_dict(report)

    assert data["version"] == REPORT_ENGINE_VERSION
    assert data["name"] == "Albert Einstein"
    assert "markdown" in data
    assert "summary" in data


def test_export_markdown(tmp_path: Path):
    report, _interpretation = _report(tmp_path)

    output = tmp_path / "report.md"

    export_atlas_report_markdown(
        report,
        output,
    )

    assert output.exists()
    assert "Atlas Intelligence Report" in output.read_text(encoding="utf-8")


def test_export_json(tmp_path: Path):
    report, interpretation = _report(tmp_path)

    output = tmp_path / "report.json"

    export_atlas_report_json(
        report,
        interpretation,
        output,
    )

    assert output.exists()
    assert "Albert Einstein" in output.read_text(encoding="utf-8")