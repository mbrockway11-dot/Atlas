import pytest

from atlas.temporal.houses import (
    HOUSES_ENGINE_VERSION,
    assign_planets_to_whole_sign_houses,
    build_house_chart,
    build_house_cusp,
    build_whole_sign_cusps,
    house_chart_to_dict,
    whole_sign_house_for_sign,
)
from atlas.temporal.models import BirthData, PlanetPosition
from atlas.temporal.natal_chart import build_natal_chart


def _birth() -> BirthData:
    return BirthData(
        name="Albert Einstein",
        birth_date="1879-03-14",
        birth_time="11:30",
        birth_place="Ulm",
        latitude=48.3984,
        longitude=9.9916,
        timezone="Europe/Berlin",
        time_known=True,
    )


def _planet(
    planet: str,
    sign_index: int,
) -> PlanetPosition:
    return PlanetPosition(
        planet=planet,
        longitude=sign_index * 30.0,
        latitude=0.0,
        speed=1.0,
        sign=[
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ][sign_index],
        sign_index=sign_index,
        degree_in_sign=0.0,
        retrograde=False,
    )


def test_build_house_cusp():
    cusp = build_house_cusp(
        house=1,
        longitude=45.0,
    )

    assert cusp.house == 1
    assert cusp.sign == "Taurus"
    assert cusp.sign_index == 1
    assert cusp.degree_in_sign == 15.0


def test_whole_sign_house_for_sign():
    assert whole_sign_house_for_sign(
        sign_index=0,
        ascendant_sign_index=0,
    ) == 1

    assert whole_sign_house_for_sign(
        sign_index=1,
        ascendant_sign_index=0,
    ) == 2

    assert whole_sign_house_for_sign(
        sign_index=11,
        ascendant_sign_index=0,
    ) == 12


def test_build_whole_sign_cusps():
    cusps = build_whole_sign_cusps(
        ascendant_sign_index=2,
    )

    assert len(cusps) == 12
    assert cusps[1].sign == "Gemini"
    assert cusps[2].sign == "Cancer"
    assert cusps[12].sign == "Taurus"


def test_assign_planets_to_whole_sign_houses():
    planets = {
        "Sun": _planet("Sun", 0),
        "Moon": _planet("Moon", 3),
    }

    placements = assign_planets_to_whole_sign_houses(
        planets=planets,
        ascendant_sign_index=0,
    )

    assert placements["Sun"].house == 1
    assert placements["Moon"].house == 4


def test_build_house_chart():
    natal = build_natal_chart(_birth())
    chart = build_house_chart(natal)

    assert chart.version == HOUSES_ENGINE_VERSION
    assert chart.name == "Albert Einstein"
    assert chart.house_system == "Whole Sign"
    assert len(chart.cusps) == 12
    assert "Sun" in chart.placements
    assert "Moon" in chart.placements


def test_build_house_chart_rejects_unsupported_house_system():
    natal = build_natal_chart(_birth())

    with pytest.raises(ValueError):
        build_house_chart(
            natal,
            house_system="Placidus",
        )


def test_house_chart_to_dict():
    natal = build_natal_chart(_birth())
    chart = build_house_chart(natal)
    data = house_chart_to_dict(chart)

    assert data["version"] == HOUSES_ENGINE_VERSION
    assert "ascendant" in data
    assert "cusps" in data
    assert "placements" in data