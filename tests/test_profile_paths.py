from pathlib import Path

from atlas.library import profile_library
from atlas.services import profile_path_service


def test_profile_library_paths_are_project_root_anchored(monkeypatch, tmp_path):
    """Profile discovery must not depend on the dashboard launch directory."""
    monkeypatch.chdir(tmp_path)

    expected_root = Path(profile_library.__file__).resolve().parents[3]

    assert profile_library.PROJECT_ROOT == expected_root
    assert profile_library.ROOT_LIBRARY_DIR == expected_root / "output" / "library"
    assert profile_library.LIBRARY_DIR == expected_root / "output" / "library" / "profiles"
    assert profile_library.ROOT_LIBRARY_DIR.is_absolute()


def test_resolve_profile_dir_prefers_canonical_profiles_layout(monkeypatch, tmp_path):
    legacy_root = tmp_path / "library"
    canonical_root = legacy_root / "profiles"
    profile_key = "example_profile"
    legacy_profile = legacy_root / profile_key
    canonical_profile = canonical_root / profile_key
    legacy_profile.mkdir(parents=True)
    canonical_profile.mkdir(parents=True)

    monkeypatch.setattr(profile_path_service, "LIBRARY_DIR", legacy_root)
    monkeypatch.setattr(profile_path_service, "PROFILES_DIR", canonical_root)

    assert profile_path_service.resolve_profile_dir(profile_key) == canonical_profile


def test_resolve_profile_dir_falls_back_to_legacy_layout(monkeypatch, tmp_path):
    legacy_root = tmp_path / "library"
    canonical_root = legacy_root / "profiles"
    profile_key = "legacy_profile"
    legacy_profile = legacy_root / profile_key
    legacy_profile.mkdir(parents=True)

    monkeypatch.setattr(profile_path_service, "LIBRARY_DIR", legacy_root)
    monkeypatch.setattr(profile_path_service, "PROFILES_DIR", canonical_root)

    assert profile_path_service.resolve_profile_dir(profile_key) == legacy_profile
