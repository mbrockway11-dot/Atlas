"""Tests for event catalogues and their provenance gating.

A temporal study is entirely a study of timestamps, so the gate that keeps
unverified timestamps out of confirmatory inference is the most important
thing here. The identity branch learned the same lesson with 52 pilot pairs
recorded from general knowledge.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from atlas.validation.event_catalogue import (
    CONFIRMATORY_PROVENANCE,
    PRECISION_SECONDS,
    EventCatalogueError,
    EventProvenance,
    EventRecord,
    InclusionRule,
    TimestampPrecision,
    apply_inclusion_rule,
    load_catalogue,
    seed_earthquake_catalogue,
    summarize_catalogue,
)


def _record(
    event_id: str = "e1",
    *,
    magnitude: float = 8.0,
    provenance: EventProvenance = EventProvenance.CATALOGUE_VERIFIED,
    precision: TimestampPrecision = TimestampPrecision.SECOND,
    instant: datetime | None = None,
    event_class: str = "earthquake",
) -> EventRecord:
    """Build an event record for testing."""
    return EventRecord(
        event_id=event_id,
        label=event_id,
        instant=instant or datetime(2011, 3, 11, 5, 46, 24, tzinfo=UTC),
        event_class=event_class,
        magnitude=magnitude,
        latitude=38.3,
        longitude=142.4,
        provenance=provenance,
        source="test",
        timestamp_precision=precision,
    )


# ---------------------------------------------------------------------------
# Provenance gating
# ---------------------------------------------------------------------------


def test_only_cited_provenance_is_confirmatory_eligible() -> None:
    """Provisional records may explore; they may not support inference."""
    assert _record(provenance=EventProvenance.CATALOGUE_VERIFIED).confirmatory_eligible
    assert _record(provenance=EventProvenance.SECONDARY_SOURCE).confirmatory_eligible
    assert not _record(provenance=EventProvenance.PROVISIONAL).confirmatory_eligible
    assert not _record(provenance=EventProvenance.REJECTED).confirmatory_eligible


def test_confirmatory_set_is_exactly_the_cited_states() -> None:
    """The eligible set is explicit, not inferred."""
    assert CONFIRMATORY_PROVENANCE == frozenset(
        {
            EventProvenance.CATALOGUE_VERIFIED,
            EventProvenance.SECONDARY_SOURCE,
        }
    )


def test_seed_catalogue_is_entirely_provisional() -> None:
    """The shipped seed must never be mistaken for verified data."""
    records = seed_earthquake_catalogue()

    assert records
    assert all(
        record.provenance is EventProvenance.PROVISIONAL for record in records
    )
    assert not any(record.confirmatory_eligible for record in records)


def test_summary_separates_eligible_from_exploratory() -> None:
    """A catalogue summary states how much of it can be used for inference."""
    summary = summarize_catalogue(
        [
            _record("a", provenance=EventProvenance.CATALOGUE_VERIFIED),
            _record("b", provenance=EventProvenance.PROVISIONAL),
        ]
    )

    assert summary["total"] == 2
    assert summary["confirmatory_eligible"] == 1
    assert summary["exploratory_only"] == 1


# ---------------------------------------------------------------------------
# Inclusion rules
# ---------------------------------------------------------------------------


def test_inclusion_rule_filters_by_magnitude() -> None:
    """The threshold is objective and stated in advance."""
    rule = InclusionRule(event_class="earthquake", minimum_magnitude=7.0)

    result = apply_inclusion_rule(
        [_record("big", magnitude=8.0), _record("small", magnitude=6.0)],
        rule,
    )

    assert result["admitted_count"] == 1
    assert result["excluded"][0]["reason"] == "magnitude"


def test_inclusion_rule_filters_by_timestamp_precision() -> None:
    """Day-only timestamps cannot support minute-scale features.

    The R0 audit found 23 of 140 features become highly sensitive at a
    one-day offset, so a date-only event cannot be scored against them.
    """
    rule = InclusionRule(event_class="earthquake")

    result = apply_inclusion_rule(
        [
            _record("precise", precision=TimestampPrecision.SECOND),
            _record("vague", precision=TimestampPrecision.DAY),
        ],
        rule,
    )

    assert result["admitted_count"] == 1
    assert result["excluded"][0]["reason"] == "timestamp_precision"


def test_inclusion_rule_filters_by_class_and_window() -> None:
    """Class and date bounds are enforced."""
    rule = InclusionRule(
        event_class="earthquake",
        earliest=datetime(2000, 1, 1, tzinfo=UTC),
    )

    result = apply_inclusion_rule(
        [
            _record("wrong_class", event_class="launch"),
            _record(
                "too_early",
                instant=datetime(1950, 1, 1, tzinfo=UTC),
            ),
            _record("kept"),
        ],
        rule,
    )

    assert result["admitted_count"] == 1
    reasons = {row["reason"] for row in result["excluded"]}
    assert reasons == {"event_class", "earliest"}


def test_exclusions_are_reported_not_silently_dropped() -> None:
    """A reader must be able to see what the rule removed."""
    rule = InclusionRule(event_class="earthquake", minimum_magnitude=9.0)
    result = apply_inclusion_rule([_record(magnitude=7.0)], rule)

    assert result["excluded_count"] == 1
    assert result["rule"]["minimum_magnitude"] == 9.0


def test_precision_seconds_are_ordered() -> None:
    """Coarser precision implies a larger implied offset."""
    assert (
        PRECISION_SECONDS[TimestampPrecision.SECOND]
        < PRECISION_SECONDS[TimestampPrecision.MINUTE]
        < PRECISION_SECONDS[TimestampPrecision.HOUR]
        < PRECISION_SECONDS[TimestampPrecision.DAY]
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _write(path: Path, events: list[dict]) -> Path:
    """Write a catalogue file."""
    path.write_text(json.dumps({"events": events}), encoding="utf-8")
    return path


def test_load_requires_explicit_provenance(tmp_path: Path) -> None:
    """A row without provenance is refused, never defaulted.

    Defaulting would silently make an unlabelled record eligible for
    confirmatory inference.
    """
    path = _write(
        tmp_path / "c.json",
        [{"event_id": "e", "instant": "2011-03-11T05:46:24+00:00"}],
    )

    with pytest.raises(EventCatalogueError, match="provenance"):
        load_catalogue(path)


def test_load_refuses_naive_timestamps(tmp_path: Path) -> None:
    """A zoneless event time would shift the sky by the catalogue's offset."""
    path = _write(
        tmp_path / "c.json",
        [
            {
                "event_id": "e",
                "instant": "2011-03-11T05:46:24",
                "provenance": "catalogue_verified",
                "source": "USGS",
            }
        ],
    )

    with pytest.raises(EventCatalogueError, match="naive timestamp"):
        load_catalogue(path)


def test_load_normalizes_to_utc(tmp_path: Path) -> None:
    """A zoned timestamp is converted, not rejected."""
    path = _write(
        tmp_path / "c.json",
        [
            {
                "event_id": "e",
                "instant": "2011-03-11T14:46:24+09:00",
                "provenance": "catalogue_verified",
                "source": "USGS",
                "magnitude": 9.1,
            }
        ],
    )

    record = load_catalogue(path)[0]

    assert record.instant == datetime(2011, 3, 11, 5, 46, 24, tzinfo=UTC)
    assert record.confirmatory_eligible


def test_load_rejects_a_non_object_root(tmp_path: Path) -> None:
    """A bare list is not a catalogue."""
    path = tmp_path / "c.json"
    path.write_text(json.dumps([1, 2]), encoding="utf-8")

    with pytest.raises(EventCatalogueError, match="events"):
        load_catalogue(path)


def test_seed_catalogue_passes_a_magnitude_7_rule() -> None:
    """The shipped seed is usable end to end by the harness."""
    result = apply_inclusion_rule(
        seed_earthquake_catalogue(),
        InclusionRule(event_class="earthquake", minimum_magnitude=7.0),
    )

    assert result["admitted_count"] >= 15
    assert result["excluded_count"] == 0
