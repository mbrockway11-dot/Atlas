from atlas.temporal.models import BirthData
from atlas.temporal.nakshatra import (
    NAKSHATRA_ENGINE_VERSION,
    build_nakshatra_chart,
    get_nakshatra_metadata,
    get_nakshatra_metadata_by_index,
    longitude_to_nakshatra,
    nakshatra_chart_to_dict,
)
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


def test_longitude_lookup():
    position = longitude_to_nakshatra(0.5)

    assert position.nakshatra == "Ashwini"
    assert position.nakshatra_index == 1
    assert position.pada == 1


def test_metadata_lookup():
    metadata = get_nakshatra_metadata("Rohini")

    assert metadata.index == 4
    assert metadata.ruler == "Moon"


def test_metadata_lookup_by_index():
    metadata = get_nakshatra_metadata_by_index(27)

    assert metadata.name == "Revati"


def test_build_chart():
    natal = build_natal_chart(_birth())
    chart = build_nakshatra_chart(natal)

    assert chart.version == NAKSHATRA_ENGINE_VERSION
    assert chart.name == "Albert Einstein"
    assert "Sun" in chart.positions
    assert "Moon" in chart.positions
    assert "Rahu" in chart.positions
    assert "Ketu" in chart.positions


def test_chart_to_dict():
    natal = build_natal_chart(_birth())
    chart = build_nakshatra_chart(natal)

    data = nakshatra_chart_to_dict(chart)

    assert data["version"] == NAKSHATRA_ENGINE_VERSION
    assert data["name"] == "Albert Einstein"
    assert "positions" in data
    assert "summary" in data
    assert "Moon" in data["positions"]