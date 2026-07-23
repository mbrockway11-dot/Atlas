from atlas.temporal.constellations import (
    IAU_ZODIAC_CONSTELLATIONS,
    build_astronomical_constellation_chart,
)
from atlas.temporal.ephemeris import build_ephemeris
from atlas.temporal.models import BirthData


def _birth(date: str, time: str = "12:00") -> BirthData:
    return BirthData(
        name="Constellation Test",
        birth_date=date,
        birth_time=time,
        birth_place="Greenwich",
        time_known=True,
    )


def test_iau_zodiac_constellations_include_ophiuchus():
    assert len(IAU_ZODIAC_CONSTELLATIONS) == 13
    assert "Ophiuchus" in IAU_ZODIAC_CONSTELLATIONS


def test_sun_is_in_ophiuchus_in_early_december():
    chart = build_astronomical_constellation_chart(
        build_ephemeris(_birth("2000-12-01"))
    )
    sun = chart["planets"]["Sun"]

    assert sun["actual_constellation"] == "Ophiuchus"
    assert sun["ecliptic_path_constellation"] == "Ophiuchus"
    assert sun["is_ophiuchus"] is True


def test_constellation_chart_preserves_unequal_boundary_definition():
    chart = build_astronomical_constellation_chart(
        build_ephemeris(_birth("1879-03-14", "11:30"))
    )

    assert chart["boundary_epoch"] == "B1875"
    assert chart["zodiac_constellation_count"] == 13
    assert chart["claim_type"] == "astronomical_coordinate_classification"
    assert chart["causal_claim"] is False
    assert len(chart["planets"]) == 12
    assert {"Uranus", "Neptune", "Pluto"}.issubset(chart["planets"])
