from atlas.acf.builder import build_acf_profile
from atlas.corpus.validation import (
    validate_profile_acfs,
    validate_profile_library,
)


def test_validate_profile_acfs_valid():
    acf = build_acf_profile("Michael Elvis Brockway")

    result = validate_profile_acfs([acf])

    assert result.valid
    assert result.profile_count == 1
    assert result.errors == []


def test_validate_profile_library_missing(tmp_path):
    result = validate_profile_library(tmp_path / "missing")

    assert not result.valid
    assert result.errors


def test_validate_profile_library_detects_missing_acf(tmp_path):
    profile_dir = tmp_path / "profiles" / "missing_acf"
    profile_dir.mkdir(parents=True)

    result = validate_profile_library(tmp_path / "profiles")

    assert not result.valid
    assert "Missing profile.acf.json" in result.errors[0]