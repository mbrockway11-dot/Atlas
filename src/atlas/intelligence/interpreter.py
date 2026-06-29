"""Atlas Intelligence Interpreter.

Synthesize AtlasIdentity into readable research summaries.

This module does not compute new astrology, graph topology, or population
statistics. It interprets already-computed Atlas layers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from atlas.identity_bridge import AtlasIdentity


INTERPRETER_VERSION = "1.0"


@dataclass(frozen=True)
class InterpretationSection:
    """One interpreted report section."""

    title: str
    summary: str
    bullets: list[str]
    data: dict[str, Any]


@dataclass(frozen=True)
class AtlasInterpretation:
    """Complete interpreted Atlas identity report."""

    version: str
    name: str
    sections: list[InterpretationSection]
    summary: dict[str, Any]


def interpret_identity(
    identity: AtlasIdentity,
) -> AtlasInterpretation:
    """Interpret a unified Atlas identity object."""

    sections = [
        interpret_identity_overview(identity),
        interpret_temporal_overview(identity),
        interpret_natal_signature(identity),
        interpret_dasha_state(identity),
        interpret_transit_state(identity),
        interpret_research_flags(identity),
    ]

    return AtlasInterpretation(
        version=INTERPRETER_VERSION,
        name=identity.name,
        sections=sections,
        summary={
            "section_count": len(sections),
            "has_temporal": bool(identity.temporal),
            "has_acf": bool(identity.acf),
            "has_intake": bool(identity.intake),
        },
    )


def interpret_identity_overview(
    identity: AtlasIdentity,
) -> InterpretationSection:
    """Interpret profile-level identity state."""

    intake = identity.intake
    summary = identity.summary

    name = identity.name
    birth_date = intake.get("birth_date", "Unknown")
    birth_place = intake.get("birth_place", "Unknown")
    time_known = summary.get("time_known", False)

    bullets = [
        f"Birth date: {birth_date or 'Unknown'}",
        f"Birth place: {birth_place or 'Unknown'}",
        f"Birth time known: {time_known}",
        f"ACF profile present: {summary.get('has_acf', False)}",
        f"Intake metadata present: {summary.get('has_intake', False)}",
    ]

    return InterpretationSection(
        title="Identity Overview",
        summary=(
            f"{name} has been unified into an AtlasIdentity object "
            "combining intake, ACF, and computed temporal layers."
        ),
        bullets=bullets,
        data={
            "name": name,
            "birth_date": birth_date,
            "birth_place": birth_place,
            "time_known": time_known,
        },
    )


def interpret_temporal_overview(
    identity: AtlasIdentity,
) -> InterpretationSection:
    """Interpret available temporal layers."""

    temporal = identity.temporal

    layers = [
        layer
        for layer in [
            "birth",
            "natal",
            "houses",
            "nakshatras",
            "dignity",
            "aspects",
            "yogas",
            "navamsa",
            "dasha",
            "transits",
        ]
        if layer in temporal
    ]

    return InterpretationSection(
        title="Temporal Overview",
        summary=(
            "Temporal Intelligence layers are present and available "
            "for interpretation."
            if layers
            else "No temporal layers are available."
        ),
        bullets=[
            f"Layer available: {layer}"
            for layer in layers
        ],
        data={
            "layers": layers,
            "layer_count": len(layers),
        },
    )


def interpret_natal_signature(
    identity: AtlasIdentity,
) -> InterpretationSection:
    """Interpret natal chart headline features."""

    temporal = identity.temporal
    natal = temporal.get("natal", {})
    houses = temporal.get("houses", {})
    nakshatras = temporal.get("nakshatras", {})
    dignity = temporal.get("dignity", {})

    planets = natal.get("planets", {})
    placements = houses.get("placements", {})
    nak_positions = nakshatras.get("positions", {})
    dignities = dignity.get("dignities", {})

    sun = planets.get("Sun", {})
    moon = planets.get("Moon", {})
    ascendant = houses.get("ascendant", {})
    moon_nakshatra = nak_positions.get("Moon", {})
    strongest = strongest_dignity(dignities)

    bullets = [
        f"Sun: {format_sign_degree(sun)}",
        f"Moon: {format_sign_degree(moon)}",
        f"Ascendant: {ascendant.get('sign', 'Unknown')}",
        f"Moon Nakshatra: {moon_nakshatra.get('nakshatra', 'Unknown')}",
        f"Strongest dignity: {strongest}",
        f"Planets with house placements: {len(placements)}",
    ]

    return InterpretationSection(
        title="Natal Signature",
        summary=(
            "The natal signature summarizes the core sidereal placements, "
            "ascendant, Moon Nakshatra, and strongest dignity marker."
        ),
        bullets=bullets,
        data={
            "sun": sun,
            "moon": moon,
            "ascendant": ascendant,
            "moon_nakshatra": moon_nakshatra,
            "strongest_dignity": strongest,
        },
    )


def interpret_dasha_state(
    identity: AtlasIdentity,
) -> InterpretationSection:
    """Interpret Vimshottari Dasha state."""

    dasha = identity.temporal.get("dasha", {})
    periods = dasha.get("periods", [])

    first_period = periods[0] if periods else {}

    bullets = [
        f"Moon Nakshatra: {dasha.get('moon_nakshatra', 'Unknown')}",
        f"Starting lord: {dasha.get('moon_nakshatra_lord', 'Unknown')}",
        f"First period lord: {first_period.get('lord', 'Unknown')}",
        f"First period: {first_period.get('start_date', 'Unknown')} to {first_period.get('end_date', 'Unknown')}",
        f"Total periods generated: {len(periods)}",
    ]

    return InterpretationSection(
        title="Dasha State",
        summary=(
            "The Vimshottari timeline identifies the starting Mahadasha "
            "from the Moon Nakshatra and maps the major period sequence."
        ),
        bullets=bullets,
        data={
            "dasha": dasha,
        },
    )


def interpret_transit_state(
    identity: AtlasIdentity,
) -> InterpretationSection:
    """Interpret transit contact state."""

    transits = identity.temporal.get("transits", {})
    summary = transits.get("summary", {})

    bullets = [
        f"Transit date: {transits.get('transit_date', 'Unknown')}",
        f"Transit contacts: {summary.get('contact_count', 0)}",
        f"Same-sign contacts: {summary.get('same_sign_count', 0)}",
        f"Opposition contacts: {summary.get('opposition_count', 0)}",
    ]

    return InterpretationSection(
        title="Transit State",
        summary=(
            "Transit state compares current planetary signs against natal "
            "planetary signs using same-sign and opposition contacts."
        ),
        bullets=bullets,
        data={
            "summary": summary,
        },
    )


def interpret_research_flags(
    identity: AtlasIdentity,
) -> InterpretationSection:
    """Generate caution and research flags."""

    flags: list[str] = []

    birth = identity.temporal.get("birth", {})

    if not birth.get("time_known", False):
        flags.append(
            "Birth time is unknown or uncertain; house, ascendant, and timing-sensitive results need caution."
        )

    if not birth.get("latitude") or not birth.get("longitude"):
        flags.append(
            "Latitude or longitude is missing; house and ascendant calculations may be fallback-based."
        )

    if "error" in identity.temporal:
        flags.append(
            f"Temporal payload error: {identity.temporal['error']}"
        )

    if not flags:
        flags.append(
            "No major research flags detected in the current identity payload."
        )

    return InterpretationSection(
        title="Research Flags",
        summary="Quality-control notes for interpreting this AtlasIdentity.",
        bullets=flags,
        data={
            "flags": flags,
        },
    )


def format_sign_degree(
    position: dict[str, Any],
) -> str:
    """Format sign and degree."""

    sign = position.get("sign", "Unknown")
    degree = position.get("degree_in_sign")

    if degree is None:
        return sign

    return f"{sign} {round(float(degree), 2)}°"


def strongest_dignity(
    dignities: dict[str, dict[str, Any]],
) -> str:
    """Return strongest dignity marker."""

    if not dignities:
        return "Unknown"

    planet, value = max(
        dignities.items(),
        key=lambda item: item[1].get("strength_score", 0.0),
    )

    return (
        f"{planet} "
        f"({value.get('sign', 'Unknown')}, "
        f"score {value.get('strength_score', 0.0)})"
    )


def interpretation_section_to_dict(
    section: InterpretationSection,
) -> dict[str, Any]:
    """Convert section to dictionary."""

    return asdict(section)


def atlas_interpretation_to_dict(
    interpretation: AtlasInterpretation,
) -> dict[str, Any]:
    """Convert AtlasInterpretation to dictionary."""

    return {
        "version": interpretation.version,
        "name": interpretation.name,
        "sections": [
            interpretation_section_to_dict(section)
            for section in interpretation.sections
        ],
        "summary": interpretation.summary,
    }