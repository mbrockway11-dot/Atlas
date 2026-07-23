"""Determinism and missing-birth-data policy tests.

Compilation must not depend on when it runs. These tests pin that: wall-clock
time may appear only in provenance fields, never in anything that feeds a
vector, and missing birth data stays explicitly labelled rather than being
quietly replaced by a plausible-looking date.

The regression case uses ``Charlie Murphy`` -- one of the profiles whose
vector mismatch first exposed this area.
"""

from __future__ import annotations

import datetime as _dt
import json

import pytest

import atlas.temporal.transits as transits_module
from atlas.acf.builder import build_acf_profile
from atlas.birth import (
    UNKNOWN_BIRTH_EPOCH,
    UNKNOWN_BIRTH_POLICY,
    BirthData,
    resolve_birth_data,
)
from atlas.ive import build_raw_vectors_from_acf


KNOWN = BirthData(
    date="1993-08-16", time="17:30", location="Janesville, Wisconsin"
)
PARTIAL = BirthData(date="1993-08-16", time=None, location=None)
UNKNOWN = BirthData(date="", time="Unknown", location="")


def _semantic_acf(acf: dict) -> str:
    """Return the ACF minus volatile provenance, canonically encoded."""
    payload = json.loads(json.dumps(acf, sort_keys=True))
    payload.get("metadata", {}).pop("created_utc", None)
    return json.dumps(payload, sort_keys=True)


class _FakeDate(_dt.date):
    """A date class whose ``today()`` is whatever the test says it is."""

    _value = _dt.date(2026, 7, 23)

    @classmethod
    def today(cls) -> _dt.date:  # type: ignore[override]
        return cls._value


@pytest.fixture
def at_date(monkeypatch: pytest.MonkeyPatch):
    """Return a helper that pins the system date seen by analytical code."""

    def _set(day: _dt.date) -> None:
        _FakeDate._value = day
        monkeypatch.setattr(transits_module, "date", _FakeDate)

    return _set


# ---------------------------------------------------------------------------
# Status classification
# ---------------------------------------------------------------------------


def test_known_partial_and_unknown_are_distinguished() -> None:
    """The three states are separable, which cohort selection depends on."""
    assert resolve_birth_data(KNOWN).status == "known"
    assert resolve_birth_data(PARTIAL).status == "partial"
    assert resolve_birth_data(UNKNOWN).status == "unknown"
    assert resolve_birth_data(None).status == "unknown"


@pytest.mark.parametrize(
    "placeholder", ["", "  ", "Unknown", "unknown", "N/A", "none", "-", "?"]
)
def test_placeholders_are_not_mistaken_for_data(placeholder: str) -> None:
    """Corpus placeholder strings must not read as real birth data."""
    resolution = resolve_birth_data(
        BirthData(date=placeholder, time=placeholder, location=placeholder)
    )

    assert resolution.status == "unknown"
    assert resolution.has_date is False


def test_alternate_field_names_are_understood() -> None:
    """Both BirthData shapes in the codebase resolve identically."""
    mapping = {
        "birth_date": "1993-08-16",
        "birth_time": "17:30",
        "birth_place": "Janesville, Wisconsin",
    }

    assert resolve_birth_data(mapping).status == "known"


def test_only_a_date_supports_birth_features() -> None:
    """Birth-derived features need a date; time and place refine it."""
    assert resolve_birth_data(KNOWN).is_usable_for_birth_features is True
    assert resolve_birth_data(PARTIAL).is_usable_for_birth_features is True
    assert resolve_birth_data(UNKNOWN).is_usable_for_birth_features is False


# ---------------------------------------------------------------------------
# Fallback behaviour
# ---------------------------------------------------------------------------


def test_no_fallback_unless_a_datetime_is_required() -> None:
    """Resolution alone never invents a datetime."""
    resolution = resolve_birth_data(UNKNOWN)

    assert resolution.used_fallback is False
    assert resolution.effective_datetime is None


def test_unknown_birth_falls_back_to_the_fixed_epoch() -> None:
    """Callers needing a datetime get the epoch, clearly flagged."""
    resolution = resolve_birth_data(UNKNOWN, require_datetime=True)

    assert resolution.effective_datetime == UNKNOWN_BIRTH_EPOCH
    assert resolution.used_fallback is True
    assert resolution.fallback_policy == UNKNOWN_BIRTH_POLICY


def test_known_birth_never_uses_the_fallback() -> None:
    """Real data is used as-is, with no fallback flag."""
    resolution = resolve_birth_data(KNOWN, require_datetime=True)

    assert resolution.used_fallback is False
    assert resolution.fallback_policy is None
    assert resolution.effective_datetime == _dt.datetime(
        1993, 8, 16, 17, 30, tzinfo=_dt.UTC
    )


def test_fallback_is_never_written_into_birth_data() -> None:
    """The ACF must not present the epoch as a real birth date."""
    acf = build_acf_profile(name="Charlie Murphy", birth_data=UNKNOWN)
    birth_data = acf["identity"]["birth_data"]

    assert birth_data["date"] in (None, "")
    assert "2000-01-01" not in json.dumps(birth_data)


# ---------------------------------------------------------------------------
# The ACF records missingness
# ---------------------------------------------------------------------------


def test_acf_records_birth_status() -> None:
    """Status travels with the profile, for cohort filtering."""
    for birth_data, expected in (
        (KNOWN, "known"),
        (PARTIAL, "partial"),
        (UNKNOWN, "unknown"),
    ):
        acf = build_acf_profile(name="Test Person", birth_data=birth_data)
        resolution = acf["identity"]["birth_data_resolution"]

        assert resolution["status"] == expected
        assert resolution["resolution_version"]


def test_acf_status_is_machine_readable() -> None:
    """The recorded block carries the flags a filter needs."""
    acf = build_acf_profile(name="Charlie Murphy", birth_data=UNKNOWN)
    resolution = acf["identity"]["birth_data_resolution"]

    assert resolution["has_date"] is False
    assert resolution["has_time"] is False
    assert resolution["has_location"] is False
    assert resolution["fallback"]["used"] is False


# ---------------------------------------------------------------------------
# Cross-time determinism
# ---------------------------------------------------------------------------


def test_unknown_birth_acf_is_identical_across_dates(at_date) -> None:
    """The same unknown-birth profile compiles the same on any day."""
    at_date(_dt.date(1999, 1, 1))
    first = _semantic_acf(build_acf_profile(name="Charlie Murphy"))

    at_date(_dt.date(2040, 12, 31))
    second = _semantic_acf(build_acf_profile(name="Charlie Murphy"))

    assert first == second


def test_unknown_birth_vectors_are_identical_across_dates(at_date) -> None:
    """Vectors, the thing that actually matters, do not move with the clock."""
    at_date(_dt.date(1999, 1, 1))
    first = build_raw_vectors_from_acf(build_acf_profile(name="Charlie Murphy"))

    at_date(_dt.date(2040, 12, 31))
    second = build_raw_vectors_from_acf(
        build_acf_profile(name="Charlie Murphy")
    )

    assert first == second


def test_known_birth_vectors_are_identical_across_dates(at_date) -> None:
    """Known-birth profiles are equally stable."""
    at_date(_dt.date(1999, 1, 1))
    first = build_raw_vectors_from_acf(
        build_acf_profile(name="Test Person", birth_data=KNOWN)
    )

    at_date(_dt.date(2040, 12, 31))
    second = build_raw_vectors_from_acf(
        build_acf_profile(name="Test Person", birth_data=KNOWN)
    )

    assert first == second


def test_partial_birth_is_deterministic(at_date) -> None:
    """Partial data must not fall back to the clock for what is missing."""
    at_date(_dt.date(1999, 1, 1))
    first = build_raw_vectors_from_acf(
        build_acf_profile(name="Test Person", birth_data=PARTIAL)
    )

    at_date(_dt.date(2040, 12, 31))
    second = build_raw_vectors_from_acf(
        build_acf_profile(name="Test Person", birth_data=PARTIAL)
    )

    assert first == second


def test_repeated_builds_are_identical() -> None:
    """Two builds in one process agree on everything but provenance."""
    first = build_acf_profile(name="Charlie Murphy")
    second = build_acf_profile(name="Charlie Murphy")

    assert _semantic_acf(first) == _semantic_acf(second)
    assert build_raw_vectors_from_acf(first) == build_raw_vectors_from_acf(
        second
    )


def test_current_time_appears_only_in_provenance() -> None:
    """created_utc is the single volatile field, and it is metadata."""
    first = build_acf_profile(name="Charlie Murphy")
    second = build_acf_profile(name="Charlie Murphy")

    differing: list[str] = []

    def walk(a, b, path=""):
        if isinstance(a, dict) and isinstance(b, dict):
            for key in a.keys() | b.keys():
                walk(a.get(key), b.get(key), f"{path}.{key}")
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for index, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{index}]")
        elif a != b:
            differing.append(path)

    walk(first, second)

    assert differing == [".metadata.created_utc"]


# ---------------------------------------------------------------------------
# Transits must not silently use "today"
# ---------------------------------------------------------------------------


def test_transit_chart_requires_an_explicit_date() -> None:
    """Defaulting to today would make any derived artifact irreproducible."""
    with pytest.raises(ValueError, match="explicit transit_date"):
        transits_module.build_transit_chart(object())


# ---------------------------------------------------------------------------
# What identity vectors actually depend on
# ---------------------------------------------------------------------------


def test_identity_vectors_do_not_depend_on_birth_data() -> None:
    """Identity vectors are name-derived; birth data does not enter them.

    This is load-bearing in two directions:

    * it is why the birth-resolution policy is deliberately NOT part of the
      feature-schema hash -- hashing it would invalidate every artifact for a
      dependency that does not exist; and
    * it is why unknown-birth profiles are valid subjects for identity-vector
      work, while birth-permutation experiments cannot use identity vectors
      as their outcome measure.

    If this test ever fails, birth data has started feeding the vector path.
    In that case the policy version must be added to the feature-schema hash
    (``atlas.compiled.feature_schema``) so affected artifacts rebuild, and
    the validation cohort rules must be revisited.
    """
    name = "Test Person"

    with_birth = build_raw_vectors_from_acf(
        build_acf_profile(name=name, birth_data=KNOWN)
    )
    different_birth = build_raw_vectors_from_acf(
        build_acf_profile(
            name=name,
            birth_data=BirthData(
                date="1700-01-01", time="03:00", location="Tokyo, Japan"
            ),
        )
    )
    without_birth = build_raw_vectors_from_acf(build_acf_profile(name=name))

    assert with_birth == different_birth == without_birth


def test_identity_vectors_do_depend_on_the_name() -> None:
    """The complement: names carry the signal, so they must move vectors."""
    first = build_raw_vectors_from_acf(build_acf_profile(name="Nikola Tesla"))
    second = build_raw_vectors_from_acf(build_acf_profile(name="Isaac Newton"))

    assert first != second
