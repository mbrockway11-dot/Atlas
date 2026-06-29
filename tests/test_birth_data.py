from atlas.birth import BirthData, birth_data_to_dict
from atlas.acf.builder import build_acf_profile


def test_birth_data_to_dict_empty():
    data = birth_data_to_dict(None)

    assert data["date"] is None
    assert data["time"] is None
    assert data["location"] is None
    assert data["confidence"] == "unknown"


def test_birth_data_to_dict_populated():
    birth_data = BirthData(
        date="1993-08-16",
        time="17:30",
        location="Janesville, Wisconsin, USA",
        confidence="high",
        notes="User-provided birth data.",
    )

    data = birth_data_to_dict(birth_data)

    assert data["date"] == "1993-08-16"
    assert data["time"] == "17:30"
    assert data["location"] == "Janesville, Wisconsin, USA"
    assert data["confidence"] == "high"


def test_acf_profile_accepts_birth_data():
    birth_data = BirthData(
        date="1993-08-16",
        time="17:30",
        location="Janesville, Wisconsin, USA",
        confidence="high",
    )

    acf = build_acf_profile(
        "Michael Elvis Brockway",
        birth_data=birth_data,
    )

    assert acf["identity"]["birth_data"]["date"] == "1993-08-16"
    assert acf["identity"]["birth_data"]["time"] == "17:30"
    assert acf["identity"]["birth_data"]["location"] == "Janesville, Wisconsin, USA"