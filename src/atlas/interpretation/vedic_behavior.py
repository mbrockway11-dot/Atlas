"""Vedic behavior interpretation.

Translates Vedic/natal factors into human-readable behavioral tendencies.

This module does not calculate charts. It interprets available chart payloads.
"""

from __future__ import annotations

from typing import Any


VEDIC_BEHAVIOR_VERSION = "1.0"


def interpret_vedic_behavior(
    *,
    profile_key: str,
    natal_payload: dict[str, Any] | None = None,
    temporal_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build human behavior interpretation from available Vedic/natal data."""
    natal_payload = natal_payload or {}
    temporal_payload = temporal_payload or {}

    moon = read_factor(natal_payload, "moon")
    sun = read_factor(natal_payload, "sun")
    mercury = read_factor(natal_payload, "mercury")
    venus = read_factor(natal_payload, "venus")
    mars = read_factor(natal_payload, "mars")
    jupiter = read_factor(natal_payload, "jupiter")
    saturn = read_factor(natal_payload, "saturn")
    rahu = read_factor(natal_payload, "rahu")
    ketu = read_factor(natal_payload, "ketu")
    lagna = read_factor(natal_payload, "lagna") or read_factor(natal_payload, "ascendant")

    dasha = read_temporal_factor(temporal_payload, "dasha")
    transit = read_temporal_factor(temporal_payload, "transit")

    return {
        "success": True,
        "version": VEDIC_BEHAVIOR_VERSION,
        "profile_key": profile_key,
        "name": humanize(profile_key),
        "behavioral_summary": build_behavioral_summary(
            profile_key=profile_key,
            moon=moon,
            sun=sun,
            lagna=lagna,
            mercury=mercury,
            mars=mars,
            venus=venus,
            jupiter=jupiter,
            saturn=saturn,
            rahu=rahu,
            ketu=ketu,
            dasha=dasha,
            transit=transit,
        ),
        "emotional_reflex": interpret_moon(moon),
        "life_approach": interpret_lagna(lagna),
        "identity_style": interpret_sun(sun),
        "thinking_speech": interpret_mercury(mercury),
        "bonding_values": interpret_venus(venus),
        "action_conflict": interpret_mars(mars),
        "growth_belief": interpret_jupiter(jupiter),
        "discipline_pressure": interpret_saturn(saturn),
        "obsession_release_axis": interpret_nodes(rahu, ketu),
        "active_temporal_state": interpret_temporal_state(dasha, transit),
        "stress_behavior": build_stress_behavior(moon, mars, saturn, rahu),
        "growth_path": build_growth_path(jupiter, saturn, ketu),
        "confidence": resolve_confidence(natal_payload, temporal_payload),
        "missing_requirements": missing_requirements(natal_payload, temporal_payload),
        "raw_factors": {
            "lagna": lagna,
            "sun": sun,
            "moon": moon,
            "mercury": mercury,
            "venus": venus,
            "mars": mars,
            "jupiter": jupiter,
            "saturn": saturn,
            "rahu": rahu,
            "ketu": ketu,
            "dasha": dasha,
            "transit": transit,
        },
    }


def build_behavioral_summary(
    *,
    profile_key: str,
    moon: dict[str, Any],
    sun: dict[str, Any],
    lagna: dict[str, Any],
    mercury: dict[str, Any],
    mars: dict[str, Any],
    venus: dict[str, Any],
    jupiter: dict[str, Any],
    saturn: dict[str, Any],
    rahu: dict[str, Any],
    ketu: dict[str, Any],
    dasha: dict[str, Any],
    transit: dict[str, Any],
) -> str:
    """Create concise behavioral synthesis."""
    name = humanize(profile_key)

    if not any([moon, sun, lagna, mercury, mars, venus, jupiter, saturn, rahu, ketu]):
        return (
            f"{name} does not yet have enough Vedic chart data loaded for a precise behavioral "
            "interpretation. Atlas can still describe probable behavior from graph and semantic layers, "
            "but the Vedic layer should be marked provisional."
        )

    return (
        f"{name}'s Vedic behavior layer describes how their structure becomes lived behavior: "
        "Moon shows emotional reflex, Lagna shows how life is approached, Mercury shows thought "
        "and speech, Mars shows action under pressure, Venus shows bonding and value orientation, "
        "Jupiter shows growth instinct, Saturn shows discipline and constraint, and Rahu/Ketu show "
        "the axis of hunger and release. The current dasha/transit state describes which parts of "
        "that pattern are most active now."
    )


def interpret_moon(factor: dict[str, Any]) -> str:
    """Interpret Moon as emotional reflex."""
    if not factor:
        return "Moon data is unavailable, so emotional reflex remains provisional."

    sign = label(factor, "sign")
    nakshatra = label(factor, "nakshatra")

    return (
        f"The Moon indicates instinctive emotional response. With Moon context "
        f"{format_factor(sign, nakshatra)}, this profile's emotional life should be read through "
        "habitual safety needs, reaction speed, memory, attachment, and inner weather."
    )


def interpret_lagna(factor: dict[str, Any]) -> str:
    """Interpret Lagna/Ascendant as life approach."""
    if not factor:
        return "Lagna/Ascendant data is unavailable, so life approach remains provisional."

    sign = label(factor, "sign")
    nakshatra = label(factor, "nakshatra")

    return (
        f"The Lagna describes how the person enters life and meets circumstances. "
        f"With Lagna context {format_factor(sign, nakshatra)}, their first strategy is shown "
        "through posture, orientation, physical presence, and default approach to new conditions."
    )


def interpret_sun(factor: dict[str, Any]) -> str:
    """Interpret Sun as identity style."""
    if not factor:
        return "Sun data is unavailable, so identity style remains provisional."

    return (
        f"The Sun describes identity, vitality, and the need to express a central organizing principle. "
        f"With Sun context {format_factor(label(factor, 'sign'), label(factor, 'nakshatra'))}, "
        "Atlas reads identity through purpose, pride, authority, visibility, and self-definition."
    )


def interpret_mercury(factor: dict[str, Any]) -> str:
    """Interpret Mercury as cognition and speech."""
    if not factor:
        return "Mercury data is unavailable, so thinking and speech remain provisional."

    return (
        f"Mercury describes language, interpretation, trade, analysis, and mental movement. "
        f"With Mercury context {format_factor(label(factor, 'sign'), label(factor, 'nakshatra'))}, "
        "Atlas reads cognition through how the person names patterns, translates information, "
        "debates, learns, and adapts."
    )


def interpret_venus(factor: dict[str, Any]) -> str:
    """Interpret Venus as bonding and values."""
    if not factor:
        return "Venus data is unavailable, so bonding and values remain provisional."

    return (
        f"Venus describes affection, taste, harmony, aesthetics, pleasure, and relational values. "
        f"With Venus context {format_factor(label(factor, 'sign'), label(factor, 'nakshatra'))}, "
        "Atlas reads how the person attracts, softens, beautifies, collaborates, and chooses what feels worthwhile."
    )


def interpret_mars(factor: dict[str, Any]) -> str:
    """Interpret Mars as action and conflict."""
    if not factor:
        return "Mars data is unavailable, so action and conflict style remain provisional."

    return (
        f"Mars describes action, pressure, force, courage, irritation, and conflict style. "
        f"With Mars context {format_factor(label(factor, 'sign'), label(factor, 'nakshatra'))}, "
        "Atlas reads how the person initiates, defends, competes, cuts through resistance, and behaves under heat."
    )


def interpret_jupiter(factor: dict[str, Any]) -> str:
    """Interpret Jupiter as growth and belief."""
    if not factor:
        return "Jupiter data is unavailable, so growth and belief remain provisional."

    return (
        f"Jupiter describes expansion, teaching, faith, ethics, wisdom, and long-range development. "
        f"With Jupiter context {format_factor(label(factor, 'sign'), label(factor, 'nakshatra'))}, "
        "Atlas reads how the person grows, trusts, mentors, seeks meaning, and expands beyond immediate conditions."
    )


def interpret_saturn(factor: dict[str, Any]) -> str:
    """Interpret Saturn as pressure and discipline."""
    if not factor:
        return "Saturn data is unavailable, so discipline and pressure remain provisional."

    return (
        f"Saturn describes limits, duty, delay, endurance, fear, mastery, and structural pressure. "
        f"With Saturn context {format_factor(label(factor, 'sign'), label(factor, 'nakshatra'))}, "
        "Atlas reads where the person must mature, simplify, endure, become precise, and take responsibility."
    )


def interpret_nodes(rahu: dict[str, Any], ketu: dict[str, Any]) -> str:
    """Interpret Rahu/Ketu axis."""
    if not rahu and not ketu:
        return "Rahu/Ketu data is unavailable, so obsession-release axis remains provisional."

    return (
        f"Rahu/Ketu describe the hunger-release axis. Rahu context "
        f"{format_factor(label(rahu, 'sign'), label(rahu, 'nakshatra'))} shows intensification, desire, "
        f"foreignness, experimentation, and fixation. Ketu context "
        f"{format_factor(label(ketu, 'sign'), label(ketu, 'nakshatra'))} shows detachment, instinctive mastery, "
        "past-pattern residue, simplification, and release."
    )


def interpret_temporal_state(dasha: dict[str, Any], transit: dict[str, Any]) -> str:
    """Interpret active dasha/transit state."""
    if not dasha and not transit:
        return (
            "No active dasha or transit payload is available. Atlas can describe baseline behavior, "
            "but timing-specific behavior remains provisional."
        )

    parts: list[str] = []

    if dasha:
        lord = label(dasha, "lord") or label(dasha, "planet")
        period = label(dasha, "period") or label(dasha, "name")
        parts.append(
            f"Dasha context {format_factor(lord, period)} describes the longer behavioral chapter currently active."
        )

    if transit:
        emphasis = label(transit, "emphasis") or label(transit, "planet") or label(transit, "summary")
        parts.append(
            f"Transit context {emphasis or 'available'} describes temporary activation, pressure, or opportunity."
        )

    return " ".join(parts)


def build_stress_behavior(
    moon: dict[str, Any],
    mars: dict[str, Any],
    saturn: dict[str, Any],
    rahu: dict[str, Any],
) -> str:
    """Build stress behavior from core pressure indicators."""
    if not any([moon, mars, saturn, rahu]):
        return "Stress behavior remains provisional until Moon, Mars, Saturn, and Rahu data are available."

    return (
        "Stress behavior is read through Moon reaction, Mars pressure, Saturn constraint, and Rahu fixation. "
        "When activated, the person may regress into emotional habit, force action prematurely, tighten control, "
        "or chase an unresolved hunger depending on which factor is strongest."
    )


def build_growth_path(
    jupiter: dict[str, Any],
    saturn: dict[str, Any],
    ketu: dict[str, Any],
) -> str:
    """Build growth path from Jupiter/Saturn/Ketu."""
    if not any([jupiter, saturn, ketu]):
        return "Growth path remains provisional until Jupiter, Saturn, and Ketu data are available."

    return (
        "Growth comes from balancing Jupiter's expansion with Saturn's discipline and Ketu's release. "
        "The healthiest development path is not endless growth or endless control, but meaningful expansion "
        "with mature limits and conscious detachment from outdated patterns."
    )


def read_factor(payload: dict[str, Any], name: str) -> dict[str, Any]:
    """Read a natal factor from flexible payload structures."""
    if not payload:
        return {}

    candidates = [
        payload.get(name),
        payload.get(name.capitalize()),
        payload.get(name.upper()),
        payload.get("planets", {}).get(name),
        payload.get("planets", {}).get(name.capitalize()),
        payload.get("vedic", {}).get(name),
        payload.get("vedic", {}).get("planets", {}).get(name),
        payload.get("ephemeris", {}).get(name),
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    return {}


def read_temporal_factor(payload: dict[str, Any], name: str) -> dict[str, Any]:
    """Read temporal factor from flexible payload structures."""
    if not payload:
        return {}

    candidates = [
        payload.get(name),
        payload.get(name.capitalize()),
        payload.get(name.upper()),
        payload.get("temporal", {}).get(name),
        payload.get("vedic", {}).get(name),
        payload.get("dasha") if name == "dasha" else None,
        payload.get("transits") if name == "transit" else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    return {}


def resolve_confidence(
    natal_payload: dict[str, Any],
    temporal_payload: dict[str, Any],
) -> str:
    """Resolve confidence from data availability."""
    if natal_payload and temporal_payload:
        return "moderate-high"

    if natal_payload:
        return "moderate"

    if temporal_payload:
        return "low-moderate"

    return "provisional"


def missing_requirements(
    natal_payload: dict[str, Any],
    temporal_payload: dict[str, Any],
) -> list[str]:
    """List missing requirements."""
    missing: list[str] = []

    if not natal_payload:
        missing.append("natal_payload")

    if not temporal_payload:
        missing.append("temporal_payload")

    return missing


def label(payload: dict[str, Any], key: str) -> str:
    """Read a display label."""
    if not isinstance(payload, dict):
        return ""

    value = payload.get(key)
    return str(value) if value is not None else ""


def format_factor(primary: str, secondary: str) -> str:
    """Format factor context."""
    if primary and secondary:
        return f"{primary} / {secondary}"

    if primary:
        return primary

    if secondary:
        return secondary

    return "available but unspecified"


def humanize(profile_key: str) -> str:
    """Humanize profile key."""
    return str(profile_key).replace("_", " ").title()