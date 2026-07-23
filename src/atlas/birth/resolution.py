"""Central policy for resolving possibly-missing birth data.

Atlas profiles range from fully dated to name-only. Downstream code needs
two different things from that fact, and conflating them causes trouble:

* a *status* -- is this profile's birth data known, partial, or unknown --
  which validation cohorts must filter on, so that a name-only profile never
  silently enters a birth-sensitive experiment; and
* occasionally a *concrete datetime*, because some astronomical code cannot
  represent "no time at all".

The rules here are deliberately narrow:

* Wall-clock time is never used. A profile compiled today and the same
  profile compiled next year must produce identical vectors, so ``now()``
  and ``date.today()`` have no place in any analytical path.
* A fallback datetime is never written back into ``birth_data``. Missing
  data stays missing and stays labelled; the fallback is only ever an
  explicit, flagged substitution for code that demands a value.
* The policy is versioned. Changing the epoch, or how status is decided,
  changes vectors for affected profiles, so the version participates in the
  feature-schema hash and invalidates the artifacts it affects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal


BIRTH_RESOLUTION_VERSION = "1.0.0"
UNKNOWN_BIRTH_POLICY = "unknown-birth-fixed-epoch-v1"

# An arbitrary but fixed instant. The value carries no meaning and must never
# be presented as a real birth time; what matters is only that it never
# changes, so that unknown-birth profiles compile identically forever.
UNKNOWN_BIRTH_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)

BirthStatus = Literal["known", "partial", "unknown"]

# Values that appear in the corpus meaning "we do not have this", which must
# not be mistaken for real data.
_PLACEHOLDERS = {"", "unknown", "n/a", "na", "none", "null", "-", "?"}


@dataclass(frozen=True, slots=True)
class BirthDataResolution:
    """The outcome of resolving one profile's birth data."""

    status: BirthStatus
    has_date: bool
    has_time: bool
    has_location: bool
    used_fallback: bool
    fallback_policy: str | None
    effective_datetime: datetime | None
    resolution_version: str = BIRTH_RESOLUTION_VERSION

    @property
    def is_usable_for_birth_features(self) -> bool:
        """Return whether birth-derived features rest on real data.

        A date is the minimum: without one there is no chart to speak of.
        Missing time or place degrade precision but not existence.
        """
        return self.has_date

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation for embedding in an ACF."""
        return {
            "status": self.status,
            "has_date": self.has_date,
            "has_time": self.has_time,
            "has_location": self.has_location,
            "resolution_version": self.resolution_version,
            "fallback": {
                "used": self.used_fallback,
                "policy": self.fallback_policy,
                "effective_datetime": (
                    self.effective_datetime.isoformat()
                    if self.effective_datetime is not None
                    else None
                ),
            },
        }


def is_present(value: object) -> bool:
    """Return whether a birth field carries real information."""
    if value is None:
        return False

    text = str(value).strip()

    return bool(text) and text.lower() not in _PLACEHOLDERS


def resolve_birth_data(
    birth_data: Any | None,
    *,
    require_datetime: bool = False,
) -> BirthDataResolution:
    """Classify birth data and, if asked, supply a deterministic datetime.

    ``birth_data`` may be a ``BirthData`` (either the ``date``/``time``/
    ``location`` or the ``birth_date``/``birth_time``/``birth_place`` shape),
    a mapping, or ``None``.

    ``require_datetime`` is for callers that cannot represent absence. They
    get ``UNKNOWN_BIRTH_EPOCH`` with ``used_fallback=True`` -- never a value
    derived from the current clock.
    """
    date_value, time_value, location_value = _extract(birth_data)

    has_date = is_present(date_value)
    has_time = is_present(time_value)
    has_location = is_present(location_value)

    if has_date and has_time and has_location:
        status: BirthStatus = "known"
    elif has_date or has_time or has_location:
        status = "partial"
    else:
        status = "unknown"

    effective: datetime | None = None
    used_fallback = False

    if require_datetime:
        effective = _parse_datetime(date_value, time_value)

        if effective is None:
            effective = UNKNOWN_BIRTH_EPOCH
            used_fallback = True

    return BirthDataResolution(
        status=status,
        has_date=has_date,
        has_time=has_time,
        has_location=has_location,
        used_fallback=used_fallback,
        fallback_policy=UNKNOWN_BIRTH_POLICY if used_fallback else None,
        effective_datetime=effective,
    )


def _extract(birth_data: Any | None) -> tuple[Any, Any, Any]:
    """Return ``(date, time, location)`` from any supported shape."""
    if birth_data is None:
        return None, None, None

    if isinstance(birth_data, dict):
        get = birth_data.get
    else:

        def get(key: str, default: Any = None) -> Any:
            return getattr(birth_data, key, default)

    date_value = get("date", None)
    if date_value is None:
        date_value = get("birth_date", None)

    time_value = get("time", None)
    if time_value is None:
        time_value = get("birth_time", None)

    location_value = get("location", None)
    if location_value is None:
        location_value = get("birth_place", None)

    return date_value, time_value, location_value


def _parse_datetime(date_value: object, time_value: object) -> datetime | None:
    """Parse an ISO date (and optional HH:MM time) into a UTC datetime.

    Returns ``None`` when there is no usable date; noon is assumed when the
    date is known but the time is not, matching the convention used for
    unknown-time charts elsewhere in Atlas.
    """
    if not is_present(date_value):
        return None

    try:
        parsed_date = datetime.fromisoformat(str(date_value).strip()).date()
    except ValueError:
        return None

    hour, minute = 12, 0

    if is_present(time_value):
        parts = str(time_value).strip().split(":")

        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError):
            hour, minute = 12, 0

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        hour, minute = 12, 0

    return datetime(
        parsed_date.year,
        parsed_date.month,
        parsed_date.day,
        hour,
        minute,
        tzinfo=UTC,
    )
