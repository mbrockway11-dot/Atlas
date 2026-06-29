import pytest

from atlas.temporal.ephemeris import (
    EPHEMERIS_ENGINE_VERSION,
    build_ephemeris,
    build_planet_position,
    ephemeris_result_to_dict,
    normalize_degrees,
    parse_birth_date,
    parse_birth_time_to_decimal_hours,
)
from atlas.temporal.models import BirthData


def _birth() -> BirthData:
    return BirthData(
        name="Albert Einstein",
        birth_date="1879-03-14",
        birth_time="11:30",
        birth_place="Ulm",
        time_known=True,
    )


def test_parse_birth_date():
    assert parse_birth_date("1879-03-14") == (1879, 3, 14)


def test_parse_negative_birth_date():
    assert parse_birth_date("-0100-07-13") == (-100, 7, 13)


def test_parse_birth_time_to_decimal_hours():
    assert parse_birth_time_to_decimal_hours("11:30") == 11.5


def test_parse_birth_time_unknown_defaults_to_noon():
    assert parse_birth_time_to_decimal_hours("Unknown") == 12.0


def test_normalize_degrees():
    assert normalize_degrees(370.0) == 10.0
    assert normalize_degrees(-10.0) == 350.0


def test_build_planet_position():
    position = build_planet_position(
        planet="Sun",
        longitude=45.5,
        latitude=0.0,
        speed=1.0,
    )

    assert position.planet == "Sun"
    assert position.sign == "Taurus"
    assert position.sign_index == 1
    assert position.degree_in_sign == 15.5
    assert position.retrograde is False


def test_build_ephemeris():
    result = build_ephemeris(_birth())

    assert result.version == EPHEMERIS_ENGINE_VERSION
    assert result.name == "Albert Einstein"
    assert result.zodiac == "tropical"
    assert result.julian_day > 0
    assert "Sun" in result.planets
    assert "Moon" in result.planets
    assert "Rahu" in result.planets
    assert "Ketu" in result.planets


def test_ephemeris_result_to_dict():
    result = build_ephemeris(_birth())
    data = ephemeris_result_to_dict(result)

    assert data["version"] == EPHEMERIS_ENGINE_VERSION
    assert data["name"] == "Albert Einstein"
    assert "planets" in data
    assert "Sun" in data["planets"]


def test_birth_date_required():
    birth = BirthData(
        name="Missing",
        birth_date="",
        birth_time="Unknown",
        birth_place="",
    )

    with pytest.raises(ValueError):
        build_ephemeris(birth)