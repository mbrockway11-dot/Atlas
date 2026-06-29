"""Tests for Graha Drishti aspect engine."""

from atlas.temporal.aspects import (
    ASPECT_ENGINE_VERSION,
    GRAHA_DRISHTI,
    aspect_chart_to_dict,
    build_aspect_chart,
    house_distance,
    incoming_aspects,
    outgoing_aspects,
)
from atlas.temporal.houses import build_house_chart
from atlas.temporal.models import BirthData
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


def _chart():
    natal = build_natal_chart(_birth())
    houses = build_house_chart(natal)
    return build_aspect_chart(houses)


# ------------------------------------------------------------
# House Distance
# ------------------------------------------------------------

def test_house_distance_same():
    assert house_distance(1, 1) == 1


def test_house_distance_forward():
    assert house_distance(1, 7) == 7


def test_house_distance_wrap():
    assert house_distance(12, 1) == 2
    assert house_distance(11, 2) == 4


# ------------------------------------------------------------
# Classical Graha Drishti Rules
# ------------------------------------------------------------

def test_default_planets_only_aspect_seventh():
    for planet in [
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Rahu",
        "Ketu",
    ]:
        assert GRAHA_DRISHTI[planet] == {7}


def test_mars_rules():
    assert GRAHA_DRISHTI["Mars"] == {4, 7, 8}


def test_jupiter_rules():
    assert GRAHA_DRISHTI["Jupiter"] == {5, 7, 9}


def test_saturn_rules():
    assert GRAHA_DRISHTI["Saturn"] == {3, 7, 10}


# ------------------------------------------------------------
# Aspect Chart
# ------------------------------------------------------------

def test_build_chart():
    chart = _chart()

    assert chart.version == ASPECT_ENGINE_VERSION
    assert chart.name == "Albert Einstein"

    assert isinstance(chart.aspects, list)

    assert chart.summary["planet_count"] > 0
    assert chart.summary["aspect_count"] == len(chart.aspects)


def test_every_aspect_is_valid():
    chart = _chart()

    for aspect in chart.aspects:

        assert aspect.source != aspect.target

        assert 1 <= aspect.source_house <= 12
        assert 1 <= aspect.target_house <= 12

        assert aspect.aspect_type.endswith("th")

        assert aspect.strength == 1.0


# ------------------------------------------------------------
# Query Helpers
# ------------------------------------------------------------

def test_outgoing_helper():
    chart = _chart()

    mars = outgoing_aspects(
        chart,
        "Mars",
    )

    for aspect in mars:
        assert aspect.source == "Mars"


def test_incoming_helper():
    chart = _chart()

    moon = incoming_aspects(
        chart,
        "Moon",
    )

    for aspect in moon:
        assert aspect.target == "Moon"


# ------------------------------------------------------------
# Serialization
# ------------------------------------------------------------

def test_chart_to_dict():
    chart = _chart()

    data = aspect_chart_to_dict(chart)

    assert data["version"] == ASPECT_ENGINE_VERSION
    assert data["name"] == "Albert Einstein"

    assert "summary" in data
    assert "aspects" in data

    assert len(data["aspects"]) == len(chart.aspects)