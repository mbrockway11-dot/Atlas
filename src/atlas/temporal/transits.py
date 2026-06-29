"""Transit engine for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from atlas.temporal.birth import build_birth_data_from_intake
from atlas.temporal.ephemeris import build_ephemeris
from atlas.temporal.models import BirthData, NatalChart, PlanetPosition
from atlas.temporal.natal_chart import build_natal_chart


TRANSIT_ENGINE_VERSION = "1.0"


@dataclass(frozen=True)
class TransitContact:
    """Relationship between a transit planet and natal planet."""

    transit_planet: str
    natal_planet: str
    transit_sign: str
    natal_sign: str
    sign_distance: int
    same_sign: bool
    opposition: bool


@dataclass(frozen=True)
class TransitChart:
    """Current transit chart against a natal chart."""

    version: str
    name: str
    transit_date: str
    natal_chart: NatalChart
    transit_chart: NatalChart
    contacts: list[TransitContact]
    summary: dict[str, Any]


def build_transit_chart(
    natal: NatalChart,
    *,
    transit_date: str | None = None,
) -> TransitChart:
    """Build transit chart for a natal chart."""

    resolved_date = transit_date or date.today().isoformat()

    transit_birth = BirthData(
        name=f"{natal.name} Transit",
        birth_date=resolved_date,
        birth_time="12:00",
        birth_place="Transit",
        latitude=natal.birth.latitude,
        longitude=natal.birth.longitude,
        timezone=natal.birth.timezone,
        time_known=False,
    )

    transit_chart = build_natal_chart(
        transit_birth,
        ayanamsa=natal.ayanamsa,
        zodiac=natal.zodiac,
    )

    contacts = build_transit_contacts(
        natal=natal,
        transit=transit_chart,
    )

    return TransitChart(
        version=TRANSIT_ENGINE_VERSION,
        name=natal.name,
        transit_date=resolved_date,
        natal_chart=natal,
        transit_chart=transit_chart,
        contacts=contacts,
        summary={
            "contact_count": len(contacts),
            "same_sign_count": count_same_sign_contacts(contacts),
            "opposition_count": count_opposition_contacts(contacts),
            "transit_planet_count": len(transit_chart.planets),
            "natal_planet_count": len(natal.planets),
        },
    )


def build_transit_contacts(
    *,
    natal: NatalChart,
    transit: NatalChart,
) -> list[TransitContact]:
    """Build transit-to-natal sign contacts."""

    contacts: list[TransitContact] = []

    for transit_planet, transit_position in transit.planets.items():
        for natal_planet, natal_position in natal.planets.items():
            distance = sign_distance(
                transit_position.sign_index,
                natal_position.sign_index,
            )

            contacts.append(
                TransitContact(
                    transit_planet=transit_planet,
                    natal_planet=natal_planet,
                    transit_sign=transit_position.sign,
                    natal_sign=natal_position.sign,
                    sign_distance=distance,
                    same_sign=distance == 1,
                    opposition=distance == 7,
                )
            )

    return contacts


def sign_distance(
    source_sign_index: int,
    target_sign_index: int,
) -> int:
    """Return forward sign distance using 1-based inclusive counting."""

    return ((target_sign_index - source_sign_index) % 12) + 1


def same_sign_contacts(
    contacts: list[TransitContact],
) -> list[TransitContact]:
    """Return same-sign transit contacts."""

    return [
        contact
        for contact in contacts
        if contact.same_sign
    ]


def opposition_contacts(
    contacts: list[TransitContact],
) -> list[TransitContact]:
    """Return opposition contacts."""

    return [
        contact
        for contact in contacts
        if contact.opposition
    ]


def count_same_sign_contacts(
    contacts: list[TransitContact],
) -> int:
    """Count same-sign contacts."""

    return len(
        same_sign_contacts(contacts)
    )


def count_opposition_contacts(
    contacts: list[TransitContact],
) -> int:
    """Count opposition contacts."""

    return len(
        opposition_contacts(contacts)
    )


def transit_contact_to_dict(
    contact: TransitContact,
) -> dict[str, Any]:
    """Convert TransitContact to dictionary."""

    return asdict(contact)


def transit_chart_to_dict(
    chart: TransitChart,
) -> dict[str, Any]:
    """Convert TransitChart to dictionary."""

    from atlas.temporal.natal_chart import natal_chart_to_dict

    return {
        "version": chart.version,
        "name": chart.name,
        "transit_date": chart.transit_date,
        "natal_chart": natal_chart_to_dict(chart.natal_chart),
        "transit_chart": natal_chart_to_dict(chart.transit_chart),
        "contacts": [
            transit_contact_to_dict(contact)
            for contact in chart.contacts
        ],
        "summary": chart.summary,
    }