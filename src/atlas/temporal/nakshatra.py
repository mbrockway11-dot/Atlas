"""Nakshatra engine for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.temporal.models import (
    NakshatraPosition,
    NatalChart,
)


NAKSHATRA_ENGINE_VERSION = "1.0"

NAKSHATRA_SIZE = 360.0 / 27.0
PADA_SIZE = NAKSHATRA_SIZE / 4.0


@dataclass(frozen=True)
class NakshatraMetadata:
    """Immutable metadata describing one Nakshatra."""

    index: int
    name: str
    ruler: str
    deity: str
    symbol: str
    gana: str
    element: str
    varna: str
    yoni: str
    nadi: str
    purpose: str


@dataclass(frozen=True)
class NakshatraChart:
    """Complete Nakshatra chart."""

    version: str
    name: str
    positions: dict[str, NakshatraPosition]
    summary: dict[str, Any]


NAKSHATRAS = [

    NakshatraMetadata(
        1,"Ashwini","Ketu",
        "Ashwini Kumaras",
        "Horse Head",
        "Deva",
        "Earth",
        "Kshatriya",
        "Horse",
        "Adi",
        "Dharma",
    ),

    NakshatraMetadata(
        2,"Bharani","Venus",
        "Yama",
        "Yoni",
        "Manushya",
        "Earth",
        "Shudra",
        "Elephant",
        "Madhya",
        "Artha",
    ),

    NakshatraMetadata(
        3,"Krittika","Sun",
        "Agni",
        "Knife",
        "Rakshasa",
        "Fire",
        "Brahmin",
        "Sheep",
        "Antya",
        "Kama",
    ),

    NakshatraMetadata(
        4,"Rohini","Moon",
        "Brahma",
        "Cart",
        "Manushya",
        "Earth",
        "Vaishya",
        "Serpent",
        "Antya",
        "Moksha",
    ),

    NakshatraMetadata(
        5,"Mrigashira","Mars",
        "Soma",
        "Deer's Head",
        "Deva",
        "Earth",
        "Farmer",
        "Serpent",
        "Madhya",
        "Dharma",
    ),

    NakshatraMetadata(
        6,"Ardra","Rahu",
        "Rudra",
        "Tear",
        "Manushya",
        "Water",
        "Shudra",
        "Dog",
        "Adi",
        "Artha",
    ),

    NakshatraMetadata(
        7,"Punarvasu","Jupiter",
        "Aditi",
        "Bow",
        "Deva",
        "Water",
        "Kshatriya",
        "Cat",
        "Adi",
        "Kama",
    ),

    NakshatraMetadata(
        8,"Pushya","Saturn",
        "Brihaspati",
        "Flower",
        "Deva",
        "Water",
        "Kshatriya",
        "Sheep",
        "Madhya",
        "Moksha",
    ),

    NakshatraMetadata(
        9,"Ashlesha","Mercury",
        "Nagas",
        "Coiled Serpent",
        "Rakshasa",
        "Water",
        "Brahmin",
        "Cat",
        "Antya",
        "Dharma",
    ),

    NakshatraMetadata(
        10,"Magha","Ketu",
        "Pitris",
        "Royal Throne",
        "Rakshasa",
        "Fire",
        "Kshatriya",
        "Rat",
        "Antya",
        "Artha",
    ),

    NakshatraMetadata(
        11,"Purva Phalguni","Venus",
        "Bhaga",
        "Bed",
        "Manushya",
        "Fire",
        "Brahmin",
        "Rat",
        "Madhya",
        "Kama",
    ),

    NakshatraMetadata(
        12,"Uttara Phalguni","Sun",
        "Aryaman",
        "Bed",
        "Manushya",
        "Fire",
        "Kshatriya",
        "Cow",
        "Adi",
        "Moksha",
    ),

    NakshatraMetadata(
        13,"Hasta","Moon",
        "Savitar",
        "Hand",
        "Deva",
        "Earth",
        "Vaishya",
        "Buffalo",
        "Adi",
        "Dharma",
    ),

    NakshatraMetadata(
        14,"Chitra","Mars",
        "Tvashtar",
        "Pearl",
        "Rakshasa",
        "Fire",
        "Shudra",
        "Tiger",
        "Madhya",
        "Artha",
    ),

    NakshatraMetadata(
        15,"Swati","Rahu",
        "Vayu",
        "Coral",
        "Deva",
        "Air",
        "Vaishya",
        "Buffalo",
        "Antya",
        "Kama",
    ),

    NakshatraMetadata(
        16,"Vishakha","Jupiter",
        "Indra-Agni",
        "Triumphal Arch",
        "Rakshasa",
        "Fire",
        "Kshatriya",
        "Tiger",
        "Antya",
        "Moksha",
    ),

    NakshatraMetadata(
        17,"Anuradha","Saturn",
        "Mitra",
        "Lotus",
        "Deva",
        "Water",
        "Shudra",
        "Deer",
        "Madhya",
        "Dharma",
    ),

    NakshatraMetadata(
        18,"Jyeshtha","Mercury",
        "Indra",
        "Earring",
        "Rakshasa",
        "Water",
        "Brahmin",
        "Deer",
        "Adi",
        "Artha",
    ),

    NakshatraMetadata(
        19,"Mula","Ketu",
        "Nirriti",
        "Roots",
        "Rakshasa",
        "Air",
        "Butcher",
        "Dog",
        "Adi",
        "Kama",
    ),

    NakshatraMetadata(
        20,"Purva Ashadha","Venus",
        "Apas",
        "Fan",
        "Manushya",
        "Air",
        "Brahmin",
        "Monkey",
        "Madhya",
        "Moksha",
    ),

    NakshatraMetadata(
        21,"Uttara Ashadha","Sun",
        "Vishvadevas",
        "Elephant Tusk",
        "Manushya",
        "Air",
        "Kshatriya",
        "Mongoose",
        "Antya",
        "Dharma",
    ),

    NakshatraMetadata(
        22,"Shravana","Moon",
        "Vishnu",
        "Ear",
        "Deva",
        "Earth",
        "Vaishya",
        "Monkey",
        "Antya",
        "Artha",
    ),

    NakshatraMetadata(
        23,"Dhanishta","Mars",
        "Vasus",
        "Drum",
        "Rakshasa",
        "Air",
        "Shudra",
        "Lion",
        "Madhya",
        "Kama",
    ),

    NakshatraMetadata(
        24,"Shatabhisha","Rahu",
        "Varuna",
        "Circle",
        "Rakshasa",
        "Air",
        "Butcher",
        "Horse",
        "Adi",
        "Moksha",
    ),

    NakshatraMetadata(
        25,"Purva Bhadrapada","Jupiter",
        "Aja Ekapada",
        "Sword",
        "Manushya",
        "Fire",
        "Brahmin",
        "Lion",
        "Adi",
        "Dharma",
    ),

    NakshatraMetadata(
        26,"Uttara Bhadrapada","Saturn",
        "Ahirbudhnya",
        "Twins",
        "Manushya",
        "Water",
        "Kshatriya",
        "Cow",
        "Madhya",
        "Artha",
    ),

    NakshatraMetadata(
        27,"Revati","Mercury",
        "Pushan",
        "Fish",
        "Deva",
        "Water",
        "Brahmin",
        "Elephant",
        "Antya",
        "Moksha",
    ),

]   

# ------------------------------------------------------------
# Lookup Tables
# ------------------------------------------------------------

NAKSHATRA_BY_INDEX = {
    nakshatra.index: nakshatra
    for nakshatra in NAKSHATRAS
}

NAKSHATRA_BY_NAME = {
    nakshatra.name: nakshatra
    for nakshatra in NAKSHATRAS
}

# ------------------------------------------------------------
# Lookup Engine
# ------------------------------------------------------------

def longitude_to_nakshatra(
    longitude: float,
) -> NakshatraPosition:
    """Convert a sidereal longitude into a Nakshatra position."""

    longitude %= 360.0

    nakshatra_index = int(
        longitude // NAKSHATRA_SIZE
    )

    metadata = NAKSHATRA_BY_INDEX[
        nakshatra_index + 1
    ]

    degree_in_nakshatra = (
        longitude
        - (nakshatra_index * NAKSHATRA_SIZE)
    )

    pada = int(
        degree_in_nakshatra // PADA_SIZE
    ) + 1

    return NakshatraPosition(
        body="",
        nakshatra=metadata.name,
        nakshatra_index=metadata.index,
        pada=pada,
        longitude=longitude,
        degree_in_nakshatra=degree_in_nakshatra,
    )


def build_nakshatra_chart(
    natal_chart: NatalChart,
) -> NakshatraChart:
    """Build Nakshatra chart."""

    positions: dict[str, NakshatraPosition] = {}

    for body, position in natal_chart.planets.items():
        nakshatra = longitude_to_nakshatra(
            position.longitude,
        )

        positions[body] = NakshatraPosition(
            body=body,
            nakshatra=nakshatra.nakshatra,
            nakshatra_index=nakshatra.nakshatra_index,
            pada=nakshatra.pada,
            longitude=nakshatra.longitude,
            degree_in_nakshatra=nakshatra.degree_in_nakshatra,
        )

    return NakshatraChart(
        version=NAKSHATRA_ENGINE_VERSION,
        name=natal_chart.name,
        positions=positions,
        summary={
            "body_count": len(positions),
            "nakshatra_count": len(
                {
                    position.nakshatra
                    for position in positions.values()
                }
            ),
        },
    )


def get_nakshatra_metadata(
    name: str,
) -> NakshatraMetadata:
    """Lookup immutable metadata by Nakshatra name."""

    return NAKSHATRA_BY_NAME[name]


def get_nakshatra_metadata_by_index(
    index: int,
) -> NakshatraMetadata:
    """Lookup immutable metadata by Nakshatra index."""

    return NAKSHATRA_BY_INDEX[index]


def nakshatra_position_to_dict(
    position: NakshatraPosition,
) -> dict[str, Any]:
    """Convert NakshatraPosition into a dictionary."""

    return asdict(position)


def nakshatra_metadata_to_dict(
    metadata: NakshatraMetadata,
) -> dict[str, Any]:
    """Convert NakshatraMetadata into a dictionary."""

    return asdict(metadata)

def nakshatra_chart_to_dict(
    chart: NakshatraChart,
) -> dict[str, Any]:
    """Convert NakshatraChart into a dictionary."""

    return {
        "version": chart.version,
        "name": chart.name,
        "positions": {
            body: nakshatra_position_to_dict(position)
            for body, position in chart.positions.items()
        },
        "summary": chart.summary,
    }