import pytest

from atlas.temporal.config import (
    DEFAULT_AYANAMSA,
    DEFAULT_ZODIAC,
    SUPPORTED_AYANAMSAS,
)
from atlas.temporal.models import BirthData
from atlas.temporal.natal_chart import (
    NATAL_CHART_ENGINE_VERSION,
    build_natal_chart,
    build_natal_chart_payload,
)


def _birth() -> BirthData:
    return BirthData(
        name="Albert Einstein",
        birth_date="1879-03-14",
        birth_time="11:30",
        birth_place="Ulm",
        time_known=True,
    )


def test_temporal_config_defaults():
    assert DEFAULT_ZODIAC == "sidereal"
    assert DEFAULT_AYANAMSA == "Lahiri"
    assert "Lahiri" in SUPPORTED_AYANAMSAS


def test_build_sidereal_natal_chart():
    chart = build_natal_chart(_birth())

    assert chart.version == NATAL_CHART_ENGINE_VERSION
    assert chart.name == "Albert Einstein"
    assert chart.zodiac == "sidereal"
    assert chart.ayanamsa == DEFAULT_AYANAMSA
    assert "Sun" in chart.planets
    assert "Moon" in chart.planets
    assert "Rahu" in chart.planets
    assert "Ketu" in chart.planets


def test_build_tropical_natal_chart():
    chart = build_natal_chart(
        _birth(),
        zodiac="tropical",
    )

    assert chart.zodiac == "tropical"
    assert chart.ayanamsa == "None"
    assert "Sun" in chart.planets


def test_build_natal_chart_rejects_bad_zodiac():
    with pytest.raises(ValueError):
        build_natal_chart(
            _birth(),
            zodiac="bad",
        )


def test_build_natal_chart_payload():
    payload = build_natal_chart_payload(_birth())

    assert payload["version"] == NATAL_CHART_ENGINE_VERSION
    assert payload["name"] == "Albert Einstein"
    assert "ephemeris" in payload
    assert "sidereal" in payload
    assert "natal_chart" in payload