"""Historical event catalogues for temporal validation.

Events enter a temporal study the way variant pairs entered an identity one:
with an explicit evidential state, and with confirmatory inference gated on
it. The identity branch learned this the hard way -- 52 pilot pairs recorded
from general knowledge could not support an inferential claim, and saying so
up front was what kept the pilot honest.

The same rule applies here, and matters more. An earthquake timestamp
recorded from memory is not a measurement, and a temporal study is *entirely*
a study of timestamps.

    catalogue_verified      loaded from a cited catalogue file (USGS, ISC)
    secondary_source        from a published secondary source, cited
    provisional             recorded from general knowledge, exploratory only
    rejected                excluded, with a reason

Only ``catalogue_verified`` and ``secondary_source`` may enter a confirmatory
analysis. The seed set below is deliberately ``provisional``: it exercises the
harness and nothing more.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Sequence


EVENT_CATALOGUE_SCHEMA = "atlas.validation.event-catalogue.v1"


class EventProvenance(str, Enum):
    """Evidential state of an event record."""

    CATALOGUE_VERIFIED = "catalogue_verified"
    SECONDARY_SOURCE = "secondary_source"
    PROVISIONAL = "provisional"
    REJECTED = "rejected"


CONFIRMATORY_PROVENANCE: frozenset[EventProvenance] = frozenset(
    {
        EventProvenance.CATALOGUE_VERIFIED,
        EventProvenance.SECONDARY_SOURCE,
    }
)


class TimestampPrecision(str, Enum):
    """How precisely an event's time is known.

    The R0 audit measured feature stability against timestamp offset: every
    feature is stable at +/-1, 5, and 30 minutes, and only at a full day do
    23 of 140 become highly sensitive. So minute- and second-precision events
    are usable as-is, while date-only events must be either excluded or
    analysed with the day-sensitive features masked out.
    """

    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


# Offsets, in seconds, implied by each precision level. Used to decide which
# features an event can support.
PRECISION_SECONDS: dict[TimestampPrecision, int] = {
    TimestampPrecision.SECOND: 1,
    TimestampPrecision.MINUTE: 60,
    TimestampPrecision.HOUR: 3_600,
    TimestampPrecision.DAY: 86_400,
}


class EventCatalogueError(ValueError):
    """A catalogue could not be loaded or violates its inclusion rule."""


@dataclass(frozen=True, slots=True)
class EventRecord:
    """One timestamped historical event."""

    event_id: str
    label: str
    instant: datetime
    event_class: str
    magnitude: float | None
    latitude: float | None
    longitude: float | None
    provenance: EventProvenance
    source: str
    timestamp_precision: TimestampPrecision
    # Everything the source catalogue carried. Retained even when the
    # current experiment does not consume it: a field discarded at import
    # cannot be recovered without re-fetching, and a later representation
    # (topocentric positions, houses, local angles) will need depth and
    # location.
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def confirmatory_eligible(self) -> bool:
        """Return whether this record may enter a confirmatory analysis."""
        return self.provenance in CONFIRMATORY_PROVENANCE

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "event_id": self.event_id,
            "label": self.label,
            "instant": self.instant.isoformat(),
            "event_class": self.event_class,
            "magnitude": self.magnitude,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "provenance": self.provenance.value,
            "source": self.source,
            "timestamp_precision": self.timestamp_precision.value,
            "precision_seconds": PRECISION_SECONDS[self.timestamp_precision],
            "confirmatory_eligible": self.confirmatory_eligible,
            **{f"source_{k}": v for k, v in self.extra.items()},
        }


@dataclass(frozen=True, slots=True)
class InclusionRule:
    """An objective, stated-in-advance rule for catalogue membership.

    Recorded with the catalogue so a reader can see what was included and
    what was filtered, rather than inferring it from the surviving rows.
    """

    event_class: str
    minimum_magnitude: float | None = None
    earliest: datetime | None = None
    latest: datetime | None = None
    required_precision: tuple[TimestampPrecision, ...] = (
        TimestampPrecision.SECOND,
        TimestampPrecision.MINUTE,
    )

    def admits(self, record: EventRecord) -> tuple[bool, str]:
        """Return whether a record qualifies, and why not if it does not."""
        if record.event_class != self.event_class:
            return False, "event_class"

        if (
            self.minimum_magnitude is not None
            and (record.magnitude is None
                 or record.magnitude < self.minimum_magnitude)
        ):
            return False, "magnitude"

        if self.earliest is not None and record.instant < self.earliest:
            return False, "earliest"

        if self.latest is not None and record.instant > self.latest:
            return False, "latest"

        if record.timestamp_precision not in self.required_precision:
            return False, "timestamp_precision"

        return True, ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "event_class": self.event_class,
            "minimum_magnitude": self.minimum_magnitude,
            "earliest": self.earliest.isoformat() if self.earliest else None,
            "latest": self.latest.isoformat() if self.latest else None,
            "required_precision": [
                precision.value for precision in self.required_precision
            ],
        }


# ---------------------------------------------------------------------------
# Seed set
# ---------------------------------------------------------------------------
#
# Major earthquakes recorded from general knowledge. Every row is
# PROVISIONAL: the timestamps are approximately right but have not been
# checked against USGS or ISC, and a temporal study is entirely a study of
# timestamps. This set exists to exercise the harness end to end. It must not
# support an inferential claim, and the runner enforces that.

PROVISIONAL_EARTHQUAKES: tuple[dict[str, Any], ...] = (
    ("valdivia_1960", "Valdivia, Chile", "1960-05-22T19:11:14", 9.5, -38.14, -73.41),
    ("alaska_1964", "Prince William Sound, Alaska", "1964-03-28T03:36:14", 9.2, 60.91, -147.34),
    ("sumatra_2004", "Sumatra-Andaman", "2004-12-26T00:58:53", 9.1, 3.30, 95.98),
    ("tohoku_2011", "Tohoku, Japan", "2011-03-11T05:46:24", 9.1, 38.30, 142.37),
    ("kamchatka_1952", "Kamchatka", "1952-11-04T16:58:26", 9.0, 52.76, 160.06),
    ("maule_2010", "Maule, Chile", "2010-02-27T06:34:14", 8.8, -36.12, -72.90),
    ("ecuador_1906", "Ecuador-Colombia", "1906-01-31T15:36:00", 8.8, 1.00, -81.50),
    ("rat_islands_1965", "Rat Islands, Alaska", "1965-02-04T05:01:22", 8.7, 51.21, 178.50),
    ("assam_1950", "Assam-Tibet", "1950-08-15T14:09:34", 8.6, 28.36, 96.45),
    ("nias_2005", "Nias, Sumatra", "2005-03-28T16:09:36", 8.6, 2.09, 97.11),
    ("sumatra_2012", "Off Sumatra", "2012-04-11T08:38:37", 8.6, 2.33, 93.06),
    ("banda_sea_1938", "Banda Sea", "1938-02-01T19:04:18", 8.5, -5.05, 131.62),
    ("kuril_1963", "Kuril Islands", "1963-10-13T05:17:58", 8.5, 44.87, 149.48),
    ("sumatra_2007", "Southern Sumatra", "2007-09-12T11:10:26", 8.5, -4.44, 101.37),
    ("iquique_2014", "Iquique, Chile", "2014-04-01T23:46:47", 8.2, -19.61, -70.77),
    ("chiapas_2017", "Chiapas, Mexico", "2017-09-08T04:49:19", 8.2, 15.02, -93.90),
    ("sichuan_2008", "Sichuan, China", "2008-05-12T06:28:01", 7.9, 31.00, 103.32),
    ("nepal_2015", "Gorkha, Nepal", "2015-04-25T06:11:26", 7.8, 28.23, 84.73),
    ("tangshan_1976", "Tangshan, China", "1976-07-28T19:42:53", 7.6, 39.61, 118.10),
    ("haiti_2010", "Haiti", "2010-01-12T21:53:10", 7.0, 18.44, -72.57),
)


def seed_earthquake_catalogue() -> list[EventRecord]:
    """Return the provisional earthquake seed set."""
    records: list[EventRecord] = []

    for event_id, label, stamp, magnitude, lat, lon in PROVISIONAL_EARTHQUAKES:
        records.append(
            EventRecord(
                event_id=event_id,
                label=label,
                instant=datetime.fromisoformat(stamp).replace(tzinfo=UTC),
                event_class="earthquake",
                magnitude=magnitude,
                latitude=lat,
                longitude=lon,
                provenance=EventProvenance.PROVISIONAL,
                source="general_knowledge",
                timestamp_precision=TimestampPrecision.SECOND,
            )
        )

    return records


def load_catalogue(path: str | Path) -> list[EventRecord]:
    """Load an event catalogue from JSON.

    The expected shape is ``{"events": [...]}`` with each row carrying its own
    ``provenance`` and ``source``. A row without them is refused rather than
    defaulted: an unlabelled record would silently become eligible for
    confirmatory inference.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(payload, dict) or "events" not in payload:
        raise EventCatalogueError(
            f"Catalogue must be an object with an 'events' list: {path}"
        )

    records: list[EventRecord] = []

    for index, row in enumerate(payload["events"]):
        for field in ("event_id", "instant", "provenance", "source"):
            if field not in row:
                raise EventCatalogueError(
                    f"Event {index} is missing required field {field!r}. "
                    "Records without explicit provenance cannot be admitted."
                )

        instant = datetime.fromisoformat(str(row["instant"]))

        if instant.tzinfo is None:
            raise EventCatalogueError(
                f"Event {row['event_id']!r} has a naive timestamp. Event "
                "times must state their zone; assuming UTC would shift the "
                "sky by the catalogue's local offset."
            )

        records.append(
            EventRecord(
                event_id=str(row["event_id"]),
                label=str(row.get("label", row["event_id"])),
                instant=instant.astimezone(UTC),
                event_class=str(row.get("event_class", "earthquake")),
                magnitude=(
                    float(row["magnitude"])
                    if row.get("magnitude") is not None
                    else None
                ),
                latitude=(
                    float(row["latitude"])
                    if row.get("latitude") is not None
                    else None
                ),
                longitude=(
                    float(row["longitude"])
                    if row.get("longitude") is not None
                    else None
                ),
                provenance=EventProvenance(str(row["provenance"])),
                source=str(row["source"]),
                timestamp_precision=TimestampPrecision(
                    str(row.get("timestamp_precision", "second"))
                ),
                extra={
                    key[len("source_"):]: value
                    for key, value in row.items()
                    if key.startswith("source_")
                },
            )
        )

    return records


def apply_inclusion_rule(
    records: Sequence[EventRecord],
    rule: InclusionRule,
) -> dict[str, Any]:
    """Filter a catalogue by its stated rule and report what was excluded."""
    admitted: list[EventRecord] = []
    excluded: list[dict[str, Any]] = []

    for record in records:
        ok, reason = rule.admits(record)

        if ok:
            admitted.append(record)
        else:
            excluded.append(
                {"event_id": record.event_id, "reason": reason}
            )

    return {
        "rule": rule.to_dict(),
        "admitted": admitted,
        "admitted_count": len(admitted),
        "excluded": excluded,
        "excluded_count": len(excluded),
    }


def summarize_catalogue(records: Iterable[EventRecord]) -> dict[str, Any]:
    """Summarize a catalogue's composition and evidential state."""
    rows = list(records)

    if not rows:
        return {"total": 0, "confirmatory_eligible": 0}

    by_provenance: dict[str, int] = {}
    by_precision: dict[str, int] = {}

    for record in rows:
        key = record.provenance.value
        by_provenance[key] = by_provenance.get(key, 0) + 1
        precision = record.timestamp_precision.value
        by_precision[precision] = by_precision.get(precision, 0) + 1

    eligible = sum(1 for record in rows if record.confirmatory_eligible)

    return {
        "schema_version": EVENT_CATALOGUE_SCHEMA,
        "total": len(rows),
        "confirmatory_eligible": eligible,
        "exploratory_only": len(rows) - eligible,
        "by_provenance": dict(sorted(by_provenance.items())),
        "by_timestamp_precision": dict(sorted(by_precision.items())),
        "date_range": [
            min(r.instant for r in rows).isoformat(),
            max(r.instant for r in rows).isoformat(),
        ],
    }
