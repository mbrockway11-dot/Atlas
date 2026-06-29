"""Vimshottari Dasha engine for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any

from atlas.temporal.nakshatra import (
    NAKSHATRA_SIZE,
    NakshatraChart,
    get_nakshatra_metadata,
)


VIMSHOTTARI_DASHA_VERSION = "1.0"

DASHA_SEQUENCE = (
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
)

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

YEAR_DAYS = 365.2425


@dataclass(frozen=True)
class DashaPeriod:
    """One Vimshottari dasha period."""

    lord: str
    start_date: str
    end_date: str
    years: float
    level: str


@dataclass(frozen=True)
class VimshottariDasha:
    """Complete Vimshottari dasha result."""

    version: str
    name: str
    birth_date: str
    moon_nakshatra: str
    moon_nakshatra_lord: str
    moon_nakshatra_fraction_remaining: float
    periods: list[DashaPeriod]
    summary: dict[str, Any]


def build_vimshottari_dasha(
    *,
    name: str,
    birth_date: str,
    nakshatra_chart: NakshatraChart,
) -> VimshottariDasha:
    """Build Vimshottari Mahadasha timeline from Moon Nakshatra."""

    moon = nakshatra_chart.positions["Moon"]

    metadata = get_nakshatra_metadata(
        moon.nakshatra,
    )

    birth = parse_birth_date(
        birth_date,
    )

    fraction_remaining = compute_nakshatra_fraction_remaining(
        moon.degree_in_nakshatra,
    )

    periods = build_mahadasha_periods(
        start_lord=metadata.ruler,
        birth=birth,
        first_fraction=fraction_remaining,
    )

    return VimshottariDasha(
        version=VIMSHOTTARI_DASHA_VERSION,
        name=name,
        birth_date=birth_date,
        moon_nakshatra=moon.nakshatra,
        moon_nakshatra_lord=metadata.ruler,
        moon_nakshatra_fraction_remaining=fraction_remaining,
        periods=periods,
        summary={
            "period_count": len(periods),
            "starting_lord": metadata.ruler,
            "total_years": sum(period.years for period in periods),
        },
    )


def compute_nakshatra_fraction_remaining(
    degree_in_nakshatra: float,
) -> float:
    """Compute remaining portion of Moon Nakshatra."""

    elapsed = degree_in_nakshatra / NAKSHATRA_SIZE

    remaining = 1.0 - elapsed

    return max(
        0.0,
        min(
            1.0,
            remaining,
        ),
    )


def build_mahadasha_periods(
    *,
    start_lord: str,
    birth: date,
    first_fraction: float,
) -> list[DashaPeriod]:
    """Build Mahadasha periods from birth."""

    sequence = rotate_sequence_to_lord(
        start_lord,
    )

    periods: list[DashaPeriod] = []
    current = birth

    first = True

    while total_period_years(periods) < 120.0:
        for lord in sequence:
            years = float(DASHA_YEARS[lord])

            if first:
                years *= first_fraction
                first = False

            if years <= 0.0:
                continue

            end = current + timedelta(
                days=years * YEAR_DAYS,
            )

            periods.append(
                DashaPeriod(
                    lord=lord,
                    start_date=current.isoformat(),
                    end_date=end.isoformat(),
                    years=years,
                    level="mahadasha",
                )
            )

            current = end

            if total_period_years(periods) >= 120.0:
                break

    return periods


def rotate_sequence_to_lord(
    lord: str,
) -> tuple[str, ...]:
    """Rotate Vimshottari sequence so lord is first."""

    if lord not in DASHA_SEQUENCE:
        raise ValueError(f"Unsupported dasha lord: {lord}")

    index = DASHA_SEQUENCE.index(lord)

    return (
        DASHA_SEQUENCE[index:]
        + DASHA_SEQUENCE[:index]
    )


def total_period_years(
    periods: list[DashaPeriod],
) -> float:
    """Return total years in periods."""

    return sum(
        period.years
        for period in periods
    )


def parse_birth_date(
    birth_date: str,
) -> date:
    """Parse YYYY-MM-DD birth date."""

    year, month, day = birth_date.split("-")

    return date(
        int(year),
        int(month),
        int(day),
    )


def dasha_period_to_dict(
    period: DashaPeriod,
) -> dict[str, Any]:
    """Convert DashaPeriod to dictionary."""

    return asdict(period)


def vimshottari_dasha_to_dict(
    dasha: VimshottariDasha,
) -> dict[str, Any]:
    """Convert VimshottariDasha to dictionary."""

    return {
        "version": dasha.version,
        "name": dasha.name,
        "birth_date": dasha.birth_date,
        "moon_nakshatra": dasha.moon_nakshatra,
        "moon_nakshatra_lord": dasha.moon_nakshatra_lord,
        "moon_nakshatra_fraction_remaining": (
            dasha.moon_nakshatra_fraction_remaining
        ),
        "periods": [
            dasha_period_to_dict(period)
            for period in dasha.periods
        ],
        "summary": dasha.summary,
    }