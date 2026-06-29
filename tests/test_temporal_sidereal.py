import pytest

from atlas.temporal.ephemeris import build_ephemeris
from atlas.temporal.models import BirthData
from atlas.temporal.sidereal import (
    DEFAULT_AYANAMSA,
    SIDEREAL_ENGINE_VERSION,
    convert_ephemeris_to_sidereal,
    convert_position_to_sidereal,
    get_ayanamsa_degrees,
    resolve_ayanamsa_mode,
    sidereal_chart_to_dict,
)


def _birth() -> BirthData:
    return BirthData(
        name="Albert Einstein",
        birth_date="1879-03-14",
        birth_time="11:30",
        birth_place="Ulm",
        time_known=True,
    )


def test_resolve_ayanamsa_mode_supported():
    assert isinstance(resolve_ayanamsa_mode(DEFAULT_AYANAMSA), int)


def test_resolve_ayanamsa_mode_unsupported():
    with pytest.raises(ValueError):
        resolve_ayanamsa_mode("Unsupported")


def test_get_ayanamsa_degrees():
    ephemeris = build_ephemeris(_birth())
    value = get_ayanamsa_degrees(ephemeris.julian_day)

    assert value > 0.0
    assert value < 30.0


def test_convert_position_to_sidereal():
    ephemeris = build_ephemeris(_birth())
    tropical_sun = ephemeris.planets["Sun"]

    sidereal_sun = convert_position_to_sidereal(
        tropical_sun,
        ayanamsa_degrees=20.0,
    )

    assert sidereal_sun.planet == "Sun"
    assert sidereal_sun.longitude != tropical_sun.longitude
    assert sidereal_sun.latitude == tropical_sun.latitude
    assert sidereal_sun.speed == tropical_sun.speed


def test_convert_ephemeris_to_sidereal():
    ephemeris = build_ephemeris(_birth())
    sidereal = convert_ephemeris_to_sidereal(ephemeris)

    assert sidereal.version == SIDEREAL_ENGINE_VERSION
    assert sidereal.name == "Albert Einstein"
    assert sidereal.ayanamsa == DEFAULT_AYANAMSA
    assert sidereal.zodiac == "sidereal"
    assert "Sun" in sidereal.planets
    assert "Moon" in sidereal.planets
    assert sidereal.ayanamsa_degrees > 0.0


def test_sidereal_chart_to_dict():
    ephemeris = build_ephemeris(_birth())
    sidereal = convert_ephemeris_to_sidereal(ephemeris)

    data = sidereal_chart_to_dict(sidereal)

    assert data["version"] == SIDEREAL_ENGINE_VERSION
    assert data["zodiac"] == "sidereal"
    assert "planets" in data
    assert "Sun" in data["planets"]