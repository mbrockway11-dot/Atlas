from atlas.temporal.models import BirthData
from atlas.temporal.natal_chart import build_natal_chart
from atlas.temporal.navamsa import (
    NAVAMSA_ENGINE_VERSION,
    build_navamsa_chart,
    longitude_to_navamsa,
    navamsa_chart_to_dict,
)


def _birth():

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


def test_single_conversion():

    nav = longitude_to_navamsa(
        "Sun",
        15.0,
    )

    assert nav.planet == "Sun"

    assert 1 <= nav.division_number <= 9

    assert nav.sign


def test_chart():

    natal = build_natal_chart(
        _birth(),
    )

    chart = build_navamsa_chart(
        natal,
    )

    assert chart.version == NAVAMSA_ENGINE_VERSION

    assert chart.name == "Albert Einstein"

    assert "Sun" in chart.positions

    assert "Moon" in chart.positions

    assert len(chart.positions) >= 9


def test_serializer():

    natal = build_natal_chart(
        _birth(),
    )

    chart = build_navamsa_chart(
        natal,
    )

    data = navamsa_chart_to_dict(
        chart,
    )

    assert data["version"] == NAVAMSA_ENGINE_VERSION

    assert "positions" in data

    assert "summary" in data