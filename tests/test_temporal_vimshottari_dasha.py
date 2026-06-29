from atlas.temporal.models import BirthData
from atlas.temporal.nakshatra import build_nakshatra_chart
from atlas.temporal.natal_chart import build_natal_chart
from atlas.temporal.vimshottari_dasha import (
    DASHA_SEQUENCE,
    VIMSHOTTARI_DASHA_VERSION,
    build_vimshottari_dasha,
    compute_nakshatra_fraction_remaining,
    rotate_sequence_to_lord,
    vimshottari_dasha_to_dict,
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


def test_rotate_sequence_to_lord():
    sequence = rotate_sequence_to_lord("Moon")

    assert sequence[0] == "Moon"
    assert set(sequence) == set(DASHA_SEQUENCE)


def test_fraction_remaining_bounds():
    assert compute_nakshatra_fraction_remaining(0.0) == 1.0

    value = compute_nakshatra_fraction_remaining(5.0)

    assert 0.0 <= value <= 1.0


def test_build_vimshottari_dasha():
    birth = _birth()
    natal = build_natal_chart(birth)
    nakshatra = build_nakshatra_chart(natal)

    dasha = build_vimshottari_dasha(
        name=birth.name,
        birth_date=birth.birth_date,
        nakshatra_chart=nakshatra,
    )

    assert dasha.version == VIMSHOTTARI_DASHA_VERSION
    assert dasha.name == "Albert Einstein"
    assert dasha.birth_date == "1879-03-14"
    assert dasha.moon_nakshatra
    assert dasha.moon_nakshatra_lord
    assert len(dasha.periods) > 0
    assert dasha.periods[0].lord == dasha.moon_nakshatra_lord


def test_vimshottari_dasha_to_dict():
    birth = _birth()
    natal = build_natal_chart(birth)
    nakshatra = build_nakshatra_chart(natal)

    dasha = build_vimshottari_dasha(
        name=birth.name,
        birth_date=birth.birth_date,
        nakshatra_chart=nakshatra,
    )

    data = vimshottari_dasha_to_dict(dasha)

    assert data["version"] == VIMSHOTTARI_DASHA_VERSION
    assert "periods" in data
    assert "summary" in data