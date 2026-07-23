from atlas.core.compiler_passes.temporal import build_birth_seed


def test_build_birth_seed_supports_canonical_nested_intake():
    payload = {
        "profile.intake": {
            "identity": {
                "display_name": "Example Person",
            },
            "birth": {
                "date": "1993-08-16",
                "time": "17:30",
                "place": "Janesville, Wisconsin",
                "latitude": 42.6828,
                "longitude": -89.0187,
                "timezone": "America/Chicago",
            },
        }
    }

    assert build_birth_seed(payload) == {
        "name": "Example Person",
        "birth_date": "1993-08-16",
        "birth_time": "17:30",
        "birth_place": "Janesville, Wisconsin",
        "birth_location": "Janesville, Wisconsin",
        "latitude": 42.6828,
        "longitude": -89.0187,
        "timezone": "America/Chicago",
    }
