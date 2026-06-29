import json
from pathlib import Path

from atlas.identity_bridge import (
    IDENTITY_BRIDGE_VERSION,
    atlas_identity_to_dict,
    build_atlas_identity,
    export_atlas_identity,
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


def test_build_atlas_identity(tmp_path: Path):
    identity = build_atlas_identity(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    assert identity.version == IDENTITY_BRIDGE_VERSION
    assert identity.name == "Albert Einstein"
    assert identity.summary["has_acf"] is True
    assert identity.summary["has_intake"] is True
    assert "natal" in identity.temporal
    assert "dasha" in identity.temporal
    assert "transits" in identity.temporal


def test_atlas_identity_to_dict(tmp_path: Path):
    identity = build_atlas_identity(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    data = atlas_identity_to_dict(identity)

    assert data["version"] == IDENTITY_BRIDGE_VERSION
    assert data["name"] == "Albert Einstein"
    assert "temporal" in data
    assert "summary" in data


def test_export_atlas_identity(tmp_path: Path):
    identity = build_atlas_identity(
        _profile_dir(tmp_path),
        transit_date="2026-06-29",
    )

    output = tmp_path / "identity.json"

    export_atlas_identity(
        identity,
        output,
    )

    assert output.exists()
    assert "Albert Einstein" in output.read_text(encoding="utf-8")