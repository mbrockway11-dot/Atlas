from atlas.temporal.models import BirthData
from atlas.temporal.natal_chart import build_natal_chart
from atlas.temporal.transits import (
    TRANSIT_ENGINE_VERSION,
    build_transit_chart,
    count_opposition_contacts,
    count_same_sign_contacts,
    opposition_contacts,
    same_sign_contacts,
    sign_distance,
    transit_chart_to_dict,
)


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


def test_sign_distance():
    assert sign_distance(0, 0) == 1
    assert sign_distance(0, 6) == 7
    assert sign_distance(11, 0) == 2


def test_build_transit_chart():
    natal = build_natal_chart(_birth())

    chart = build_transit_chart(
        natal,
        transit_date="2026-06-29",
    )

    assert chart.version == TRANSIT_ENGINE_VERSION
    assert chart.name == "Albert Einstein"
    assert chart.transit_date == "2026-06-29"
    assert len(chart.contacts) > 0
    assert chart.summary["transit_planet_count"] > 0
    assert chart.summary["natal_planet_count"] > 0


def test_contact_filters():
    natal = build_natal_chart(_birth())

    chart = build_transit_chart(
        natal,
        transit_date="2026-06-29",
    )

    same = same_sign_contacts(chart.contacts)
    oppositions = opposition_contacts(chart.contacts)

    assert count_same_sign_contacts(chart.contacts) == len(same)
    assert count_opposition_contacts(chart.contacts) == len(oppositions)

    for contact in same:
        assert contact.same_sign is True

    for contact in oppositions:
        assert contact.opposition is True


def test_transit_chart_to_dict():
    natal = build_natal_chart(_birth())

    chart = build_transit_chart(
        natal,
        transit_date="2026-06-29",
    )

    data = transit_chart_to_dict(chart)

    assert data["version"] == TRANSIT_ENGINE_VERSION
    assert data["name"] == "Albert Einstein"
    assert "contacts" in data
    assert "summary" in data