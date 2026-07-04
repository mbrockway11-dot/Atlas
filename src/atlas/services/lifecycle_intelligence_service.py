"""Lifecycle Intelligence Service.

Builds temporal lifecycle records for people, organizations, civilizations,
and other Atlas entities.

For historical people, death data closes the observable lifecycle.
For living people, the lifecycle remains open.

This service does not predict death. It only uses death dates retrospectively
when known.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


LIFECYCLE_INTELLIGENCE_VERSION = "1.0"


def build_lifecycle_record(
    *,
    profile_key: str,
    birth_date: str = "",
    birth_time: str = "",
    birth_place: str = "",
    death_date: str = "",
    death_place: str = "",
    major_events: list[dict[str, Any]] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Build a lifecycle intelligence record."""
    major_events = major_events or []

    status = "closed_historical_lifecycle" if death_date.strip() else "open_lifecycle"

    events = normalize_events(
        birth_date=birth_date,
        birth_place=birth_place,
        death_date=death_date,
        death_place=death_place,
        major_events=major_events,
    )

    return {
        "success": True,
        "version": LIFECYCLE_INTELLIGENCE_VERSION,
        "profile_key": profile_key,
        "lifecycle_status": status,
        "birth": {
            "date": birth_date.strip(),
            "time": birth_time.strip(),
            "place": birth_place.strip(),
            "has_date": bool(birth_date.strip()),
            "has_time": bool(birth_time.strip()),
            "has_place": bool(birth_place.strip()),
        },
        "death": {
            "date": death_date.strip(),
            "place": death_place.strip(),
            "has_date": bool(death_date.strip()),
            "has_place": bool(death_place.strip()),
            "interpretation": death_interpretation(death_date),
        },
        "timeline": events,
        "age_at_death": calculate_age_at_death(birth_date, death_date),
        "observed_lifespan": observed_lifespan_summary(birth_date, death_date),
        "phase_model": build_phase_model(
            birth_date=birth_date,
            death_date=death_date,
            events=events,
        ),
        "historical_validation": build_historical_validation(events, death_date),
        "human_summary": build_human_summary(profile_key, status, birth_date, death_date),
        "warnings": build_warnings(birth_date, birth_time, birth_place, death_date),
        "notes": notes.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def normalize_events(
    *,
    birth_date: str,
    birth_place: str,
    death_date: str,
    death_place: str,
    major_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize lifecycle events."""
    events: list[dict[str, Any]] = []

    if birth_date.strip():
        events.append(
            {
                "type": "birth",
                "date": birth_date.strip(),
                "place": birth_place.strip(),
                "label": "Birth",
                "summary": "Lifecycle begins.",
                "confidence": "provided",
            }
        )

    for event in major_events:
        if isinstance(event, dict):
            events.append(
                {
                    "type": event.get("type", "major_event"),
                    "date": str(event.get("date", "")).strip(),
                    "place": str(event.get("place", "")).strip(),
                    "label": str(event.get("label", event.get("title", "Major Event"))).strip(),
                    "summary": str(event.get("summary", event.get("description", ""))).strip(),
                    "confidence": str(event.get("confidence", "unknown")).strip(),
                }
            )

    if death_date.strip():
        events.append(
            {
                "type": "death",
                "date": death_date.strip(),
                "place": death_place.strip(),
                "label": "Death",
                "summary": "Observable historical lifecycle closes.",
                "confidence": "provided",
            }
        )

    return sorted(events, key=event_sort_key)


def build_phase_model(
    *,
    birth_date: str,
    death_date: str,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build broad lifecycle phases."""
    if not birth_date:
        return [
            {
                "phase": "unknown",
                "summary": "Birth date missing; lifecycle phases cannot be estimated.",
            }
        ]

    closed = bool(death_date.strip())

    phases = [
        {
            "phase": "origin",
            "summary": "Birth conditions and early identity formation.",
            "anchor": birth_date,
        },
        {
            "phase": "emergence",
            "summary": "Period where core tendencies begin to become observable.",
        },
        {
            "phase": "expression",
            "summary": "Period where the profile's dominant role becomes historically visible.",
        },
        {
            "phase": "legacy",
            "summary": "Period where outputs, consequences, and influence become clearer.",
        },
    ]

    if closed:
        phases.append(
            {
                "phase": "closure",
                "summary": "The observable life arc is complete and can be studied retrospectively.",
                "anchor": death_date,
            }
        )
    else:
        phases.append(
            {
                "phase": "open_future",
                "summary": "The lifecycle is still open; future claims must remain scenario-based.",
            }
        )

    if events:
        phases.append(
            {
                "phase": "event_overlay",
                "summary": f"{len(events)} lifecycle events are available for temporal validation.",
            }
        )

    return phases


def build_historical_validation(
    events: list[dict[str, Any]],
    death_date: str,
) -> dict[str, Any]:
    """Build historical validation summary."""
    return {
        "event_count": len(events),
        "has_death_boundary": bool(death_date.strip()),
        "validation_use": (
            "Closed lifecycles can be used to test temporal hypotheses against known outcomes."
            if death_date.strip()
            else "Open lifecycles should be interpreted prospectively and cautiously."
        ),
        "recommended_tests": [
            "Overlay major events against temporal activations.",
            "Compare early-life, peak-expression, and late-life phases.",
            "Check whether graph role expression strengthens, weakens, or mutates over time.",
            "Compare this lifecycle against nearest structural neighbors.",
        ],
    }


def death_interpretation(death_date: str) -> str:
    """Interpret death date as lifecycle boundary only."""
    if not death_date.strip():
        return (
            "No death date is recorded. Atlas treats this as an open lifecycle and must not infer closure."
        )

    return (
        "Death date closes the observable historical lifecycle. Atlas uses it only for retrospective "
        "timeline validation, not for prediction."
    )


def calculate_age_at_death(birth_date: str, death_date: str) -> int | None:
    """Calculate approximate age at death from ISO dates."""
    birth = parse_date(birth_date)
    death = parse_date(death_date)

    if not birth or not death:
        return None

    age = death.year - birth.year
    if (death.month, death.day) < (birth.month, birth.day):
        age -= 1

    return age


def observed_lifespan_summary(birth_date: str, death_date: str) -> str:
    """Build observed lifespan summary."""
    age = calculate_age_at_death(birth_date, death_date)

    if age is not None:
        return f"Observed historical lifespan: approximately {age} years."

    if birth_date and not death_date:
        return "Lifecycle is open from recorded birth date to present/future observation."

    return "Observed lifespan cannot be calculated from available data."


def build_human_summary(
    profile_key: str,
    status: str,
    birth_date: str,
    death_date: str,
) -> str:
    """Build human-readable lifecycle summary."""
    name = humanize(profile_key)

    if status == "closed_historical_lifecycle":
        return (
            f"{name} has a closed historical lifecycle from {birth_date or 'unknown birth'} "
            f"to {death_date}. This allows Atlas to compare temporal hypotheses against a complete "
            "observable life arc."
        )

    return (
        f"{name} has an open lifecycle. Atlas can model current and future scenarios, but should not "
        "treat the timeline as complete."
    )


def build_warnings(
    birth_date: str,
    birth_time: str,
    birth_place: str,
    death_date: str,
) -> list[str]:
    """Build lifecycle warnings."""
    warnings: list[str] = []

    if not birth_date:
        warnings.append("Birth date missing; lifecycle timing is limited.")

    if not birth_time:
        warnings.append("Birth time missing; natal timing precision is limited.")

    if not birth_place:
        warnings.append("Birth place missing; location-sensitive natal/temporal layers are limited.")

    if not death_date:
        warnings.append("Death date missing or not applicable; lifecycle remains open.")

    return warnings


def parse_date(value: str) -> date | None:
    """Parse YYYY-MM-DD date safely."""
    if not value:
        return None

    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def event_sort_key(event: dict[str, Any]) -> str:
    """Sort events by date with undated events last."""
    value = event.get("date", "")
    return str(value) if value else "9999-99-99"


def humanize(value: str) -> str:
    """Humanize profile keys."""
    return str(value).replace("_", " ").title()
