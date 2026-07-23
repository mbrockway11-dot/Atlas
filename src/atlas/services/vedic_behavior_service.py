"""Vedic Behavior service.

Builds bounded behavioral-assumption hypotheses from Atlas Temporal Intelligence.

Important:
- This service does NOT claim confirmed behavior.
- It does NOT diagnose personality.
- It produces interpretive assumptions derived from Vedic-style temporal factors.
- Every output should be read as a hypothesis layer with confidence and cautions.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.temporal_intelligence_service import (
    build_temporal_intelligence_payload,
)


VEDIC_BEHAVIOR_VERSION = "1.0"


def list_vedic_behavior_profiles() -> list[str]:
    """Return profiles available for Vedic behavior assumptions."""
    return list_saved_profiles()


def build_vedic_behavior_payload(
    profile_key: str,
    *,
    transit_date: str | None = None,
) -> dict[str, Any]:
    """Build Vedic behavioral-assumption payload for one profile."""
    temporal_payload = build_temporal_intelligence_payload(
        profile_key,
        transit_date=transit_date,
    )

    if not temporal_payload.get("success"):
        return failure_payload(
            profile_key=profile_key,
            errors=temporal_payload.get("errors", []),
            warnings=temporal_payload.get("warnings", []),
        )

    temporal_data = temporal_payload.get("data", {})
    temporal_metrics = temporal_payload.get("metrics", {})

    behavior = build_vedic_behavior_model(
        profile_key=profile_key,
        temporal_data=temporal_data,
        temporal_metrics=temporal_metrics,
        source_warnings=temporal_payload.get("warnings", []),
    )

    return {
        "success": True,
        "version": VEDIC_BEHAVIOR_VERSION,
        "profile_key": profile_key,
        "errors": [],
        "warnings": temporal_payload.get("warnings", []) + behavior.get("warnings", []),
        "data": {
            "behavior": behavior,
            "source_summary": summarize_temporal_source(temporal_payload),
        },
        "exports": {
            "behavior_json": behavior,
            "markdown": render_vedic_behavior_markdown(behavior),
        },
        "metrics": build_vedic_behavior_metrics(behavior, temporal_payload),
    }


def build_vedic_behavior_model(
    *,
    profile_key: str,
    temporal_data: dict[str, Any],
    temporal_metrics: dict[str, Any],
    source_warnings: list[str],
) -> dict[str, Any]:
    """Build the Vedic behavior model."""
    tropical_natal = temporal_data.get("natal", {})
    sidereal_natal = temporal_data.get("sidereal", {})
    natal = sidereal_natal or tropical_natal
    birth = temporal_data.get("birth", {})
    dignity = temporal_data.get("dignity", {})
    dasha = temporal_data.get("dasha", {})
    transits = temporal_data.get("transits", {})

    assumptions = []

    assumptions.extend(
        build_planetary_behavior_assumptions(
            natal=natal,
            dignity=dignity,
        )
    )
    assumptions.extend(
        build_moon_nakshatra_assumptions(
            temporal_metrics=temporal_metrics,
            natal=natal,
        )
    )
    assumptions.extend(
        build_dasha_behavior_assumptions(
            dasha=dasha,
            temporal_metrics=temporal_metrics,
        )
    )
    assumptions.extend(
        build_transit_behavior_assumptions(
            transits=transits,
            temporal_metrics=temporal_metrics,
        )
    )

    warnings = build_behavior_warnings(
        birth=birth,
        temporal_metrics=temporal_metrics,
        source_warnings=source_warnings,
    )

    confidence = build_behavior_confidence(
        assumptions=assumptions,
        temporal_metrics=temporal_metrics,
        warnings=warnings,
    )

    sections = build_behavior_sections(
        profile_key=profile_key,
        assumptions=assumptions,
        confidence=confidence,
        warnings=warnings,
    )

    return {
        "version": VEDIC_BEHAVIOR_VERSION,
        "profile_key": profile_key,
        "definition": (
            "Behavioral assumptions are hypothesis-level interpretations derived "
            "from Vedic temporal factors. They are not confirmed behavior, diagnosis, "
            "or deterministic identity."
        ),
        "coordinate_system": {
            "zodiac": (
                natal.get("zodiac", "sidereal")
                if isinstance(natal, dict)
                else "sidereal"
            ),
            "ayanamsa": (
                natal.get("ayanamsa", "Lahiri")
                if isinstance(natal, dict)
                else "Lahiri"
            ),
            "planet_source": (
                "temporal.sidereal"
                if sidereal_natal
                else "temporal.natal_fallback"
            ),
            "fallback_used": not bool(sidereal_natal),
        },
        "confidence": confidence,
        "assumptions": assumptions,
        "sections": sections,
        "warnings": warnings,
        "summary": {
            "assumption_count": len(assumptions),
            "section_count": len(sections),
            "evidence_count": count_evidence(assumptions),
            "warning_count": len(warnings),
            "overall_confidence": confidence.get("overall", {}),
            "moon_nakshatra": temporal_metrics.get("moon_nakshatra", ""),
            "dasha_periods": temporal_metrics.get("dasha_periods", 0),
            "planet_count": temporal_metrics.get("planet_count", 0),
            "transit_contacts": temporal_metrics.get("transit_contacts", 0),
        },
    }


def build_planetary_behavior_assumptions(
    *,
    natal: dict[str, Any],
    dignity: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build assumptions from natal planet placements and dignity."""
    assumptions = []

    planets = extract_planets(natal)
    dignity_items = extract_dignity_items(dignity)

    sun = planets.get("Sun") or planets.get("sun")
    moon = planets.get("Moon") or planets.get("moon")
    mercury = planets.get("Mercury") or planets.get("mercury")
    venus = planets.get("Venus") or planets.get("venus")
    mars = planets.get("Mars") or planets.get("mars")
    jupiter = planets.get("Jupiter") or planets.get("jupiter")
    saturn = planets.get("Saturn") or planets.get("saturn")

    if sun:
        assumptions.append(
            behavior_assumption(
                layer="natal_planet",
                theme="identity_expression",
                assumption="Solar placement may describe preferred style of identity expression and visible agency.",
                confidence="moderate",
                evidence=[planet_evidence("Sun", sun)],
                cautions=["Solar behavior should not be treated as confirmed personality."],
            )
        )

    if moon:
        assumptions.append(
            behavior_assumption(
                layer="natal_planet",
                theme="emotional_processing",
                assumption="Lunar placement may describe default emotional processing, perception, and response rhythm.",
                confidence="moderate",
                evidence=[planet_evidence("Moon", moon)],
                cautions=["Moon-based assumptions are sensitive to birth data quality."],
            )
        )

    if mercury:
        assumptions.append(
            behavior_assumption(
                layer="natal_planet",
                theme="cognitive_style",
                assumption="Mercury placement may describe communication pattern, analysis style, and information processing bias.",
                confidence="moderate",
                evidence=[planet_evidence("Mercury", mercury)],
                cautions=["Communication style must be validated through evidence, not assumed absolutely."],
            )
        )

    if venus:
        assumptions.append(
            behavior_assumption(
                layer="natal_planet",
                theme="relational_preference",
                assumption="Venus placement may describe aesthetic preference, attachment style assumptions, and relational harmony-seeking behavior.",
                confidence="limited",
                evidence=[planet_evidence("Venus", venus)],
                cautions=["Relationship assumptions require external behavioral confirmation."],
            )
        )

    if mars:
        assumptions.append(
            behavior_assumption(
                layer="natal_planet",
                theme="drive_and_conflict",
                assumption="Mars placement may describe action style, conflict response, urgency, and competitive expression.",
                confidence="limited",
                evidence=[planet_evidence("Mars", mars)],
                cautions=["Mars assumptions should not be read as aggression by default."],
            )
        )

    if jupiter:
        assumptions.append(
            behavior_assumption(
                layer="natal_planet",
                theme="growth_orientation",
                assumption="Jupiter placement may describe learning style, belief expansion, mentorship tendency, and meaning-making behavior.",
                confidence="limited",
                evidence=[planet_evidence("Jupiter", jupiter)],
                cautions=["Jupiter assumptions are broad and should be treated as directional."],
            )
        )

    if saturn:
        assumptions.append(
            behavior_assumption(
                layer="natal_planet",
                theme="discipline_and_constraint",
                assumption="Saturn placement may describe responsibility patterns, restraint, endurance, fear boundaries, and long-term discipline.",
                confidence="limited",
                evidence=[planet_evidence("Saturn", saturn)],
                cautions=["Saturn assumptions should not be interpreted as pathology or limitation alone."],
            )
        )

    strongest = strongest_dignity(dignity_items)
    if strongest:
        assumptions.append(
            behavior_assumption(
                layer="dignity",
                theme="strongest_function",
                assumption=(
                    f"The strongest dignity marker may indicate a comparatively emphasized behavioral function: "
                    f"{strongest.get('planet', 'unknown')}."
                ),
                confidence="moderate",
                evidence=[
                    f"Strongest dignity planet: {strongest.get('planet', 'unknown')}",
                    f"Sign: {strongest.get('sign', 'unknown')}",
                    f"Score: {strongest.get('score', 'unknown')}",
                ],
                cautions=["Dignity is symbolic weighting, not proof of actual behavior."],
            )
        )

    return assumptions


def build_moon_nakshatra_assumptions(
    *,
    temporal_metrics: dict[str, Any],
    natal: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build assumptions from Moon Nakshatra."""
    nakshatra = temporal_metrics.get("moon_nakshatra", "")

    if not nakshatra:
        return [
            behavior_assumption(
                layer="nakshatra",
                theme="emotional_archetype",
                assumption="Moon Nakshatra could not be resolved, so nakshatra-based behavioral assumptions remain unavailable.",
                confidence="low",
                evidence=["Moon Nakshatra missing or unresolved."],
                cautions=["Do not infer nakshatra behavior until Moon Nakshatra is resolved."],
            )
        ]

    return [
        behavior_assumption(
            layer="nakshatra",
            theme="emotional_archetype",
            assumption=(
                f"Moon Nakshatra {nakshatra} may provide an emotional-archetype hypothesis "
                "for instinctive response style and inner motivational pattern."
            ),
            confidence="moderate",
            evidence=[f"Moon Nakshatra: {nakshatra}"],
            cautions=["Nakshatra assumptions are interpretive and require behavioral validation."],
        )
    ]


def build_dasha_behavior_assumptions(
    *,
    dasha: Any,
    temporal_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build assumptions from Vimshottari dasha output."""
    dasha_dict = object_to_dict(dasha)
    dasha_periods = temporal_metrics.get("dasha_periods", 0)

    if not dasha_dict or dasha_periods == 0:
        return [
            behavior_assumption(
                layer="dasha",
                theme="life_phase_behavior",
                assumption="Dasha-based behavior assumptions are unavailable or limited.",
                confidence="low",
                evidence=[f"Dasha periods generated: {dasha_periods}"],
                cautions=["Do not infer current life-phase behavior from missing dasha data."],
            )
        ]

    periods = dasha_dict.get("periods", [])

    if not periods:
        periods = dasha_dict.get("mahadashas", [])

    periods = [object_to_dict(period) for period in periods]
    first_period = periods[0] if periods else {}

    evidence = [f"Dasha periods generated: {dasha_periods}"]

    if first_period:
        evidence.append(f"First period lord: {first_period.get('lord', 'unknown')}")
        evidence.append(
            f"First period start: {first_period.get('start_date', first_period.get('start', 'unknown'))}"
        )
        evidence.append(
            f"First period end: {first_period.get('end_date', first_period.get('end', 'unknown'))}"
        )

    return [
        behavior_assumption(
            layer="dasha",
            theme="life_phase_behavior",
            assumption=(
                "Vimshottari dasha sequence may describe phase-based behavioral emphasis, "
                "timing pressure, and recurring developmental themes."
            ),
            confidence="moderate",
            evidence=evidence,
            cautions=["Dasha behavior should be interpreted as phase tendency, not fixed personality."],
        )
    ]


def build_transit_behavior_assumptions(
    *,
    transits: dict[str, Any],
    temporal_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build assumptions from transit contacts."""
    contact_count = temporal_metrics.get("transit_contacts", 0)
    aspect_count = temporal_metrics.get("transit_aspects", 0)

    if contact_count == 0 and aspect_count == 0:
        return [
            behavior_assumption(
                layer="transit",
                theme="current_activation",
                assumption="Transit activation assumptions are unavailable or minimal.",
                confidence="low",
                evidence=[
                    f"Transit contacts: {contact_count}",
                    f"Transit aspects: {aspect_count}",
                ],
                cautions=["Current behavioral activation cannot be inferred without transit contacts."],
            )
        ]

    return [
        behavior_assumption(
            layer="transit",
            theme="current_activation",
            assumption=(
                "Transit contacts may indicate current symbolic activation pressure, "
                "short-term emphasis, or behavioral themes likely to be more visible now."
            ),
            confidence="limited",
            evidence=[
                f"Transit contacts: {contact_count}",
                f"Transit aspects: {aspect_count}",
            ],
            cautions=["Transit behavior is timing-sensitive and should not override natal or evidence layers."],
        )
    ]


def build_behavior_sections(
    *,
    profile_key: str,
    assumptions: list[dict[str, Any]],
    confidence: dict[str, Any],
    warnings: list[str],
) -> list[dict[str, Any]]:
    """Build sectioned behavioral report."""
    return [
        {
            "title": "Behavioral Assumption Overview",
            "summary": (
                f"{profile_key} has {len(assumptions)} Vedic behavioral assumption(s). "
                "These are hypothesis-level interpretive statements derived from temporal factors."
            ),
            "assumptions": assumptions,
            "confidence": confidence.get("overall", {}),
            "cautions": [
                "Behavioral assumptions are not confirmed behaviors.",
                "This layer should support interpretation, not replace evidence.",
            ],
        },
        {
            "title": "Behavioral Cautions",
            "summary": "Vedic behavior interpretation must preserve source limitations.",
            "assumptions": [],
            "confidence": confidence.get("caution", {}),
            "cautions": warnings,
        },
    ]


def build_behavior_confidence(
    *,
    assumptions: list[dict[str, Any]],
    temporal_metrics: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Build behavioral-assumption confidence."""
    planet_count = safe_float(temporal_metrics.get("planet_count"))
    dasha_periods = safe_float(temporal_metrics.get("dasha_periods"))
    transit_contacts = safe_float(temporal_metrics.get("transit_contacts"))
    moon_nakshatra = temporal_metrics.get("moon_nakshatra", "")

    data_score = 0.0

    if planet_count >= 7:
        data_score += 0.30
    elif planet_count > 0:
        data_score += 0.18

    if moon_nakshatra:
        data_score += 0.20

    if dasha_periods > 0:
        data_score += 0.20

    if transit_contacts > 0:
        data_score += 0.10

    if assumptions:
        data_score += 0.10

    caution_penalty = min(len(warnings) * 0.04, 0.24)

    assumption_score = confidence_average(
        [assumption.get("confidence", {}) for assumption in assumptions]
    )

    overall_score = clamp(
        data_score * 0.55
        + assumption_score * 0.45
        - caution_penalty
    )

    return {
        "data": confidence_record(data_score),
        "assumptions": confidence_record(assumption_score),
        "caution": confidence_record(max(0.0, 1.0 - caution_penalty)),
        "overall": confidence_record(overall_score),
        "penalties": {
            "warnings": {
                "count": len(warnings),
                "penalty": round(caution_penalty, 4),
            }
        },
    }


def build_behavior_warnings(
    *,
    birth: dict[str, Any],
    temporal_metrics: dict[str, Any],
    source_warnings: list[str],
) -> list[str]:
    """Build warnings for behavioral assumptions."""
    warnings = list(source_warnings)

    birth_time = temporal_metrics.get("birth_time", "")
    birth_place = temporal_metrics.get("birth_place", "")

    if not temporal_metrics.get("moon_nakshatra"):
        warnings.append("Moon Nakshatra is unresolved; emotional-archetype assumptions are limited.")

    if not birth_time or str(birth_time).lower() == "unknown":
        warnings.append("Birth time is unknown; timing-sensitive behavioral assumptions require caution.")

    if not birth_place:
        warnings.append("Birth place is missing; coordinate-sensitive assumptions may be fallback-based.")

    if temporal_metrics.get("house_count", 0) == 0:
        warnings.append("House count is zero; house-based behavioral assumptions should not be used.")

    return dedupe(warnings)


def behavior_assumption(
    *,
    layer: str,
    theme: str,
    assumption: str,
    confidence: str,
    evidence: list[str],
    cautions: list[str],
) -> dict[str, Any]:
    """Build one behavioral assumption."""
    score = {
        "high": 0.85,
        "moderate": 0.70,
        "limited": 0.50,
        "low": 0.25,
    }.get(confidence, 0.40)

    return {
        "layer": layer,
        "theme": theme,
        "assumption": assumption,
        "confidence": confidence_record(score),
        "evidence": evidence,
        "cautions": cautions,
    }


def render_vedic_behavior_markdown(behavior: dict[str, Any]) -> str:
    """Render Vedic behavior model as Markdown."""
    lines = [
        f"# Vedic Behavioral Assumptions: {behavior.get('profile_key', 'Profile')}",
        "",
        f"**Version:** {behavior.get('version', VEDIC_BEHAVIOR_VERSION)}",
        "",
        "## Definition",
        behavior.get("definition", ""),
        "",
        "## Confidence",
    ]

    confidence = behavior.get("confidence", {})
    for key, record in confidence.items():
        if isinstance(record, dict) and "percent" in record:
            lines.append(
                f"- {key.title()}: {record.get('label', 'unknown')} "
                f"({record.get('percent', 0)}%)"
            )

    lines.append("")
    lines.append("## Assumptions")

    for item in behavior.get("assumptions", []):
        item_confidence = item.get("confidence", {})
        lines.append(f"### {item.get('theme', 'Theme')}")
        lines.append(item.get("assumption", ""))
        lines.append(
            f"Confidence: {item_confidence.get('label', 'unknown')} "
            f"({item_confidence.get('percent', 0)}%)"
        )

        evidence = item.get("evidence", [])
        if evidence:
            lines.append("")
            lines.append("Evidence:")
            for entry in evidence:
                lines.append(f"- {entry}")

        cautions = item.get("cautions", [])
        if cautions:
            lines.append("")
            lines.append("Cautions:")
            for caution in cautions:
                lines.append(f"- {caution}")

        lines.append("")

    warnings = behavior.get("warnings", [])
    if warnings:
        lines.append("## Warnings")
        for warning in warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines).strip() + "\n"


def build_vedic_behavior_metrics(
    behavior: dict[str, Any],
    temporal_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build Vedic behavior metrics."""
    markdown = render_vedic_behavior_markdown(behavior)
    summary = behavior.get("summary", {})

    return {
        "assumption_count": summary.get("assumption_count", 0),
        "section_count": summary.get("section_count", 0),
        "evidence_count": summary.get("evidence_count", 0),
        "warning_count": summary.get("warning_count", 0),
        "word_count": len(markdown.split()),
        "overall_confidence": summary.get("overall_confidence", {}),
        "moon_nakshatra": summary.get("moon_nakshatra", ""),
        "dasha_periods": summary.get("dasha_periods", 0),
        "planet_count": summary.get("planet_count", 0),
        "transit_contacts": summary.get("transit_contacts", 0),
        "source_warnings": len(temporal_payload.get("warnings", [])),
        "source_errors": len(temporal_payload.get("errors", [])),
    }


def summarize_temporal_source(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe temporal source summary."""
    return {
        "success": payload.get("success"),
        "warnings": payload.get("warnings", []),
        "errors": payload.get("errors", []),
        "metrics": payload.get("metrics", {}),
        "data_keys": sorted(list((payload.get("data") or {}).keys())),
        "export_keys": sorted(list((payload.get("exports") or {}).keys())),
    }

def object_to_dict(value: Any) -> dict[str, Any]:
    """Convert dict-like or object-like values to a dictionary."""
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            if isinstance(dumped, dict):
                return dumped
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        return {
            key: item
            for key, item in vars(value).items()
            if not key.startswith("_")
        }

    return {}

def extract_planets(natal: Any) -> dict[str, Any]:
    """Extract planets from natal output."""
    natal_dict = object_to_dict(natal)

    if "planets" in natal_dict and isinstance(natal_dict.get("planets"), dict):
        return natal_dict.get("planets", {})

    if "placements" in natal_dict and isinstance(natal_dict.get("placements"), dict):
        return natal_dict.get("placements", {})

    return {
        key: value
        for key, value in natal_dict.items()
        if str(key).lower() in {
            "sun",
            "moon",
            "mercury",
            "venus",
            "mars",
            "jupiter",
            "saturn",
            "rahu",
            "ketu",
        }
    }


def extract_dignity_items(dignity: Any) -> list[dict[str, Any]]:
    """Extract dignity items safely."""
    dignity_dict = object_to_dict(dignity)

    if isinstance(dignity_dict.get("items"), list):
        return [object_to_dict(item) for item in dignity_dict.get("items", [])]

    if isinstance(dignity_dict.get("dignities"), list):
        return [object_to_dict(item) for item in dignity_dict.get("dignities", [])]

    if isinstance(dignity_dict.get("planets"), list):
        return [object_to_dict(item) for item in dignity_dict.get("planets", [])]

    rows = []
    for planet, value in dignity_dict.items():
        value_dict = object_to_dict(value)
        if value_dict:
            row = {"planet": planet}
            row.update(value_dict)
            rows.append(row)

    return rows


def strongest_dignity(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return strongest dignity row."""
    if not items:
        return None

    return max(items, key=lambda item: safe_float(item.get("score")))


def planet_evidence(planet: str, placement: Any) -> str:
    """Build planet evidence string."""
    placement_dict = object_to_dict(placement)

    if placement_dict:
        sign = placement_dict.get("sign", placement_dict.get("rashi", "unknown"))
        degree = placement_dict.get("degree", placement_dict.get("longitude", "unknown"))
        return f"{planet}: {sign} {degree}"

    return f"{planet}: {placement}"


def count_evidence(assumptions: list[dict[str, Any]]) -> int:
    """Count evidence items."""
    return sum(len(item.get("evidence", [])) for item in assumptions)


def confidence_average(records: list[dict[str, Any]]) -> float:
    """Average confidence records."""
    scores = [
        safe_float(record.get("score"))
        for record in records
        if isinstance(record, dict)
    ]

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def confidence_record(score: float) -> dict[str, Any]:
    """Build confidence record."""
    score = clamp(score)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": confidence_label(score),
    }


def confidence_label(score: float) -> str:
    """Resolve confidence label."""
    if score >= 0.85:
        return "high"

    if score >= 0.65:
        return "moderate"

    if score >= 0.40:
        return "limited"

    return "low"


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clamp(value: float) -> float:
    """Clamp value to 0..1."""
    return max(0.0, min(1.0, value))


def dedupe(values: list[str]) -> list[str]:
    """Dedupe values while preserving order."""
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


def failure_payload(
    *,
    profile_key: str,
    errors: list[Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": VEDIC_BEHAVIOR_VERSION,
        "profile_key": profile_key,
        "errors": errors,
        "warnings": warnings,
        "data": {},
        "exports": {},
        "metrics": {},
    }


def json_export(data: Any) -> str:
    """Serialize Vedic behavior JSON."""
    return json.dumps(data, indent=2, sort_keys=True)
