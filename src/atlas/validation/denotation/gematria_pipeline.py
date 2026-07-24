"""The explicit, fail-closed gematria computation pipeline.

Replaces the legacy one-shot ``run_all_ciphers`` with staged computation whose
every step is auditable:

    input
      ↓ orthographic validation   scope, fail-closed
      ↓ transliteration           Latin token -> Hebrew letter, ambiguity-aware
      ↓ letter identities
      ↓ value assignment          Hebrew letter -> value
      ↓ numeric result

English ordinal takes a shorter, self-contained path: it needs no
transliteration and no external authority, so it is admitted as computation
outright. The Hebrew path is fully implemented but produces a numeric result
only when handed an admitted transliteration and value scheme -- and none is
admitted, so today it fail-closes at that gate rather than returning a number
nobody licensed.

Legacy ``atlas.ciphers`` is quarantined from 1E for the same reason
``evidence_from_number`` is: its names assert Hebrew provenance its behaviour
does not have.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import string
from typing import Any

from atlas.validation.denotation.gematria_orthography import (
    LATIN_ONLY,
    OrthographyResult,
    ScopeStatus,
    check_scope,
)
from atlas.validation.denotation.gematria_transliteration import (
    HebrewLetter,
    TransliterationError,
    TransliterationScheme,
    ValueAssignment,
)
from atlas.validation.denotation.gematria_value_method import ValueMethod


PIPELINE_SCHEMA = "atlas.validation.denotation.gematria-pipeline.v1"

# English ordinal is self-contained: a fixed rule over the Latin alphabet with
# no transliteration and no external authority.
ENGLISH_ORDINAL = {
    letter: index + 1 for index, letter in enumerate(string.ascii_lowercase)
}


class StageStatus(str, Enum):
    """The outcome of one pipeline stage."""

    OK = "ok"
    BLOCKED_SCOPE = "blocked_scope"
    BLOCKED_NO_ADMITTED_SCHEME = "blocked_no_admitted_scheme"
    BLOCKED_AMBIGUOUS = "blocked_ambiguous"
    BLOCKED_UNASSIGNED_VALUE = "blocked_unassigned_value"


class GematriaPipelineError(ValueError):
    """The pipeline could not produce a result and says why."""


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """The audit record of one computation, complete or blocked."""

    system: str
    orthography: OrthographyResult
    stage_status: StageStatus
    letters: tuple[str, ...]
    values: tuple[int, ...]
    total: int | None
    detail: str = ""

    @property
    def complete(self) -> bool:
        """Return whether a numeric total was produced."""
        return self.stage_status is StageStatus.OK and self.total is not None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": PIPELINE_SCHEMA,
            "system": self.system,
            "orthography": self.orthography.to_dict(),
            "stage_status": self.stage_status.value,
            "letters": list(self.letters),
            "values": list(self.values),
            "total": self.total,
            "complete": self.complete,
            "detail": self.detail,
        }


def english_ordinal(text: str) -> PipelineResult:
    """Compute the English ordinal sum, fail-closed on scope.

    Admitted as self-contained computation. The scope check still runs, so
    Hebrew or punctuation-only input fail-closes rather than silently
    returning zero.
    """
    scope = check_scope(text, LATIN_ONLY)

    if scope.scope_status is not ScopeStatus.OK:
        return PipelineResult(
            system="english_ordinal",
            orthography=scope,
            stage_status=StageStatus.BLOCKED_SCOPE,
            letters=(),
            values=(),
            total=None,
            detail=f"scope: {scope.scope_status.value}",
        )

    values = tuple(ENGLISH_ORDINAL[char] for char in scope.accepted_symbols)

    return PipelineResult(
        system="english_ordinal",
        orthography=scope,
        stage_status=StageStatus.OK,
        letters=scope.accepted_symbols,
        values=values,
        total=sum(values),
    )


def hebrew_gematria(
    text: str,
    transliteration: TransliterationScheme | None,
    value_assignment: ValueAssignment | None,
) -> PipelineResult:
    """Compute a Hebrew gematria value, fail-closed at every stage.

    Requires an **admitted** transliteration scheme and an **admitted** value
    assignment. Passing an unadmitted scheme (or none) blocks with a typed
    status instead of computing a number no source licenses. That is why the
    default pipeline produces no Hebrew total today: the registries are empty
    of admitted schemes.
    """
    scope = check_scope(text, LATIN_ONLY)

    if scope.scope_status is not ScopeStatus.OK:
        return _blocked(scope, StageStatus.BLOCKED_SCOPE,
                        f"scope: {scope.scope_status.value}")

    if transliteration is None or not transliteration.admitted:
        return _blocked(
            scope,
            StageStatus.BLOCKED_NO_ADMITTED_SCHEME,
            "no admitted transliteration scheme; Latin->Hebrew identity is "
            "an editorial convention awaiting a citation (1E-G-SOURCE)",
        )

    if value_assignment is None or not value_assignment.admitted:
        return _blocked(
            scope,
            StageStatus.BLOCKED_NO_ADMITTED_SCHEME,
            "no admitted value assignment; Hebrew letter values await a "
            "citation (1E-G-SOURCE)",
        )

    letters: list[HebrewLetter] = []

    for token in scope.accepted_symbols:
        try:
            letters.append(transliteration.resolve(token))
        except TransliterationError as error:
            return _blocked(
                scope, StageStatus.BLOCKED_AMBIGUOUS, str(error)
            )

    try:
        values = tuple(value_assignment.value_of(letter) for letter in letters)
    except TransliterationError as error:
        return _blocked(
            scope, StageStatus.BLOCKED_UNASSIGNED_VALUE, str(error)
        )

    return PipelineResult(
        system="gematria",
        orthography=scope,
        stage_status=StageStatus.OK,
        letters=tuple(letter.value for letter in letters),
        values=values,
        total=sum(values),
    )


def _blocked(
    scope: OrthographyResult, status: StageStatus, detail: str
) -> PipelineResult:
    """Return a blocked Hebrew result carrying its reason."""
    return PipelineResult(
        system="gematria",
        orthography=scope,
        stage_status=status,
        letters=(),
        values=(),
        total=None,
        detail=detail,
    )


def direct_hebrew_value(text: str, method: "ValueMethod | None") -> dict:
    """Compute a Hebrew gematria value directly, no transliteration.

    The 1E-G-SOURCE-A path: Hebrew script in, letter identity from Unicode,
    value from an **admitted** method. Letter identity is licensed today; the
    numeric value is not, because no method is admitted, so this fail-closes
    at the value stage with the identities still reported. The returned record
    carries everything the acceptance test needs -- identities, values, total,
    method hash and provenance -- so a licensed run is fully reproducible.
    """
    from atlas.validation.denotation.gematria_hebrew import (
        UNICODE_SOURCE,
        orthography_standard_hash,
        read_hebrew,
    )

    reading = read_hebrew(text)

    base = {
        "schema": PIPELINE_SCHEMA,
        "system": "gematria",
        "path": "direct_hebrew",
        "identity_source": UNICODE_SOURCE,
        # The identity standard hash travels with every result. A total may
        # only appear alongside BOTH this and a value method hash, so a
        # Unicode-only result can never serialize a number.
        "orthography_standard_hash": orthography_standard_hash(),
        "orthography": reading.orthography.to_dict(),
        "letters": [letter.value for letter in reading.letters],
    }

    if not reading.usable:
        return {
            **base,
            "stage_status": StageStatus.BLOCKED_SCOPE.value,
            "values": [],
            "total": None,
            "complete": False,
            "detail": (
                f"scope: {reading.orthography.scope_status.value}"
            ),
        }

    if method is None or not method.admitted:
        return {
            **base,
            # Letter identity IS licensed; only the value is blocked.
            "stage_status": (
                StageStatus.BLOCKED_NO_ADMITTED_SCHEME.value
            ),
            "letter_identity_licensed": True,
            "values": [],
            "total": None,
            "complete": False,
            "detail": (
                "letter identities licensed by Unicode; no admitted value "
                "method, so the numeric value is not licensed (1E-G-SOURCE-A "
                "has no traditional value source)"
            ),
        }

    values = [
        method.value_of(letter, final=final)
        for letter, final in zip(reading.letters, reading.final_forms)
    ]

    result = {
        **base,
        "stage_status": StageStatus.OK.value,
        "values": values,
        "total": sum(values),
        "complete": True,
        "value_method_hash": method.method_hash(),
        "method_provenance": method.provenance(),
    }

    # Structural guarantee, asserted at the one place a total is produced: a
    # numeric total is serialized only when both the identity standard and the
    # value method are named. A result carrying a total must carry both
    # hashes, always.
    _assert_dual_provenance(result)

    return result


def _assert_dual_provenance(result: dict) -> None:
    """Raise if a total appears without both provenance hashes.

    Enforces the rule that a result backed only by the Unicode identity source
    must never carry a number. The check is on the serialized result, so it
    catches a total introduced by any future edit, not only this path.
    """
    if result.get("total") is None:
        return

    if not result.get("orthography_standard_hash"):
        raise GematriaPipelineError(
            "a numeric total was produced without an orthography standard "
            "hash; a value cannot be presented without naming the identity "
            "source."
        )

    if not result.get("value_method_hash"):
        raise GematriaPipelineError(
            "a numeric total was produced without a value method hash; a "
            "value cannot be presented without naming the tradition that "
            "licensed it."
        )


# The legacy cipher module, quarantined from 1E. Its function names --
# hebrew_literal_sequence, hebrew_phonetic_sequence -- are provenance claims
# the behaviour does not honour: neither reads Hebrew text, and the phonetic
# scheme is unsourced. Other callers of atlas.ciphers keep it; 1E does not
# touch it, and a test enforces that.
LEGACY_CIPHER_QUARANTINE: dict[str, Any] = {
    "module": "atlas.ciphers",
    "symbols": [
        "hebrew_literal_sequence",
        "hebrew_phonetic_sequence",
        "run_all_ciphers",
    ],
    "present": True,
    "permitted_in_1E": False,
    "reason": (
        "names assert Hebrew provenance the behaviour lacks: the tables are "
        "Latin-keyed, Hebrew input yields an empty sequence, and the "
        "phonetic scheme is uncited. Use gematria_pipeline instead."
    ),
}
