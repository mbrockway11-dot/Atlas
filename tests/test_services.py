from atlas.services.intelligence_service import cache_path
from atlas.services.profile_service import profile_dir


def test_profile_dir_returns_path():
    path = profile_dir("example")
    assert str(path).endswith("example")


def test_cache_path_returns_json_path():
    path = cache_path("example/profile")
    assert path.name == "example_profile.json"
    assert "output" in str(path)