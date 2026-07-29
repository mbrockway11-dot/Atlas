"""Gematria transliteration and value assignment — split, and unsourced.

1E-G-CLASSIFY found these two decisions welded into one uncited constant:

    which Hebrew letter does this Latin token represent?   editorial convention
    what value does that Hebrew letter carry?              attested tradition

Welded, neither can be checked against a source, and the mapping is
non-injective so it cannot even be inverted. This module splits them into two
separately versioned, separately hashed artifacts, so each can later be cited
under 1E-G-SOURCE independently.

**Repair is not licensing.** The goal here is that the pipeline can *represent*
a scheme correctly, not that any scheme is authoritative. So both registries
ship with **zero admitted schemes**. The legacy fused table is registered as a
candidate, explicitly not admitted, so tests can assert it cannot present
itself as literal or authoritative Hebrew.

Transliteration is candidate-valued: a token may resolve to one Hebrew letter,
several, or none. Ambiguity stops computation unless the scheme declares a
deterministic resolution -- hiding it behind a silent first-match is how the
legacy code turned a convention into an apparent fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


TRANSLITERATION_SCHEMA = "atlas.validation.denotation.gematria-translit.v1"
VALUE_SCHEMA = "atlas.validation.denotation.gematria-value.v1"


class HebrewLetter(str, Enum):
    """The 22 Hebrew letters, as identities rather than values.

    An identity carries no number; the value scheme assigns that separately.
    Keeping them distinct is the whole point of the split.
    """

    ALEPH = "aleph"
    BET = "bet"
    GIMEL = "gimel"
    DALET = "dalet"
    HE = "he"
    VAV = "vav"
    ZAYIN = "zayin"
    HET = "het"
    TET = "tet"
    YOD = "yod"
    KAF = "kaf"
    LAMED = "lamed"
    MEM = "mem"
    NUN = "nun"
    SAMEKH = "samekh"
    AYIN = "ayin"
    PE = "pe"
    TSADI = "tsadi"
    QOF = "qof"
    RESH = "resh"
    SHIN = "shin"
    TAV = "tav"


class Resolution(str, Enum):
    """How a scheme resolves a token that has several candidate letters."""

    # No resolution declared: ambiguity stops computation.
    NONE = "none"
    # The scheme names one canonical letter per ambiguous token.
    DECLARED_CANONICAL = "declared_canonical"


class TransliterationError(ValueError):
    """A transliteration scheme or lookup was constructed invalidly."""


@dataclass(frozen=True, slots=True)
class TransliterationScheme:
    """Latin token -> candidate Hebrew letters.

    ``token_map`` values are tuples, because a token legitimately may have
    zero, one, or several candidates. ``canonical`` supplies a deterministic
    choice only where the scheme explicitly declares one.
    """

    scheme_id: str
    version: str
    admitted: bool
    token_map: Mapping[str, tuple[HebrewLetter, ...]]
    canonical: Mapping[str, HebrewLetter]
    resolution: Resolution
    note: str = ""

    def __post_init__(self) -> None:
        for token, letter in self.canonical.items():
            if token not in self.token_map:
                raise TransliterationError(
                    f"canonical token {token!r} is not in the token map."
                )

            if letter not in self.token_map[token]:
                raise TransliterationError(
                    f"canonical letter for {token!r} is not among its "
                    "candidates."
                )

    def candidates(self, token: str) -> tuple[HebrewLetter, ...]:
        """Return the candidate letters for a token."""
        return self.token_map.get(token, ())

    def resolve(self, token: str) -> HebrewLetter:
        """Return the single letter for a token, or raise on ambiguity.

        The fail-closed core: a token with several candidates and no declared
        canonical resolution stops here rather than silently taking the
        first, which is exactly how the legacy code manufactured certainty.
        """
        candidates = self.candidates(token)

        if not candidates:
            raise TransliterationError(
                f"{self.scheme_id}: token {token!r} has no candidate letter."
            )

        if len(candidates) == 1:
            return candidates[0]

        if (
            self.resolution is Resolution.DECLARED_CANONICAL
            and token in self.canonical
        ):
            return self.canonical[token]

        raise TransliterationError(
            f"{self.scheme_id}: token {token!r} is ambiguous "
            f"({', '.join(c.value for c in candidates)}) and the scheme "
            "declares no resolution. Ambiguity stops computation."
        )

    def scheme_hash(self) -> str:
        """Return a deterministic hash of the scheme."""
        payload = {
            "schema": TRANSLITERATION_SCHEMA,
            "scheme_id": self.scheme_id,
            "version": self.version,
            "token_map": {
                token: [letter.value for letter in letters]
                for token, letters in sorted(self.token_map.items())
            },
            "canonical": {
                token: letter.value
                for token, letter in sorted(self.canonical.items())
            },
            "resolution": self.resolution.value,
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class ValueAssignment:
    """Hebrew letter identity -> numeric value.

    Separate from transliteration, so the attested part (values) is not held
    hostage to the editorial part (which Latin letter maps to which Hebrew
    one).
    """

    scheme_id: str
    version: str
    admitted: bool
    values: Mapping[HebrewLetter, int]
    note: str = ""
    source_copy_hash: str = ""
    source_locator: str = ""

    def __post_init__(self) -> None:
        if self.admitted and not (self.source_copy_hash and self.source_locator):
            raise TransliterationError(
                f"{self.scheme_id} cannot be admitted without a source copy "
                "hash and a locator: a value assignment is a licensed claim and "
                "needs a verified normative source."
            )

    def value_of(self, letter: HebrewLetter) -> int:
        """Return the value of a letter, or raise if unassigned."""
        if letter not in self.values:
            raise TransliterationError(
                f"{self.scheme_id}: no value assigned to {letter.value!r}."
            )

        return self.values[letter]

    def scheme_hash(self) -> str:
        """Return a deterministic hash of the assignment."""
        payload = {
            "schema": VALUE_SCHEMA,
            "scheme_id": self.scheme_id,
            "version": self.version,
            "values": {
                letter.value: value
                for letter, value in sorted(
                    self.values.items(), key=lambda kv: kv[0].value
                )
            },
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()


# The legacy fused table, recovered into the split representation and marked
# NOT admitted. Its Latin->Hebrew choices are the uncited editorial
# conventions 1E-G-CLASSIFY flagged; representing them here lets a test assert
# they cannot pass as authoritative, without deleting the behaviour other
# callers of atlas.ciphers still depend on.
_LEGACY_TOKENS: dict[str, tuple[HebrewLetter, ...]] = {
    "a": (HebrewLetter.ALEPH,),
    "b": (HebrewLetter.BET,),
    "g": (HebrewLetter.GIMEL,),
    "d": (HebrewLetter.DALET,),
    "e": (HebrewLetter.HE,),
    "u": (HebrewLetter.VAV,),
    "v": (HebrewLetter.VAV,),
    "w": (HebrewLetter.VAV,),
    "z": (HebrewLetter.ZAYIN,),
    "h": (HebrewLetter.HET,),
    "i": (HebrewLetter.YOD,),
    "j": (HebrewLetter.YOD,),
    "y": (HebrewLetter.YOD,),
    "c": (HebrewLetter.KAF,),
    "k": (HebrewLetter.KAF,),
    "l": (HebrewLetter.LAMED,),
    "m": (HebrewLetter.MEM,),
    "n": (HebrewLetter.NUN,),
    "s": (HebrewLetter.SAMEKH,),
    "x": (HebrewLetter.SAMEKH,),
    "o": (HebrewLetter.AYIN,),
    "p": (HebrewLetter.PE,),
    "f": (HebrewLetter.PE,),
    "q": (HebrewLetter.QOF,),
    "r": (HebrewLetter.RESH,),
    "t": (HebrewLetter.TAV,),
}


LEGACY_LATIN_TRANSLITERATION = TransliterationScheme(
    scheme_id="legacy-latin-fused-unsourced",
    version="0.0.0",
    admitted=False,
    token_map=_LEGACY_TOKENS,
    canonical={},
    resolution=Resolution.NONE,
    note=(
        "The legacy atlas.ciphers Latin->value table, split back into its "
        "transliteration half. Not admitted: the Latin->Hebrew choices are "
        "uncited editorial conventions, and several Latin letters share one "
        "Hebrew letter (U/V/W->vav, I/J/Y->yod, C/K->kaf, S/X->samekh, "
        "F/P->pe), so the mapping is non-injective. Present for auditing, "
        "not for use."
    ),
)


# Standard Hebrew letter values (mispar hechrachi). The single source of truth
# for the aleph=1..tav=400 map -- gematria_value_method imports this rather than
# keeping a second copy. Recovered as a candidate value assignment and marked
# NOT admitted: the values are widely attested, but 1E requires a citation, and
# REPAIR does not supply one -- that is 1E-G-SOURCE's job.
STANDARD_HEBREW_LETTER_VALUES: dict[HebrewLetter, int] = {
    HebrewLetter.ALEPH: 1, HebrewLetter.BET: 2, HebrewLetter.GIMEL: 3,
    HebrewLetter.DALET: 4, HebrewLetter.HE: 5, HebrewLetter.VAV: 6,
    HebrewLetter.ZAYIN: 7, HebrewLetter.HET: 8, HebrewLetter.TET: 9,
    HebrewLetter.YOD: 10, HebrewLetter.KAF: 20, HebrewLetter.LAMED: 30,
    HebrewLetter.MEM: 40, HebrewLetter.NUN: 50, HebrewLetter.SAMEKH: 60,
    HebrewLetter.AYIN: 70, HebrewLetter.PE: 80, HebrewLetter.TSADI: 90,
    HebrewLetter.QOF: 100, HebrewLetter.RESH: 200, HebrewLetter.SHIN: 300,
    HebrewLetter.TAV: 400,
}


# ADMITTED under 1E-G-SOURCE-A: the base 22-letter identity->value map is
# licensed by a normative standard (Unicode CLDR's %hebrew RBNF ruleset), which
# fixes exactly this encoding. Admission followed a human define-vs-presuppose
# judgment (2026-07-27: DEFINES) plus first-hand copy verification -- see
# docs/GEMATRIA_P1_CLDR_INSPECTION.md. This admits only the base VALUE
# ASSIGNMENT. It does NOT admit a value METHOD: the final-form *reading* value
# (a sofit letter's worth inside a word) is outside any numeral-writing
# standard's scope and remains a primary_traditional acquisition, so
# value_method_available and numeric_evaluation stay gated.
CANDIDATE_STANDARD_VALUES = ValueAssignment(
    scheme_id="standard-hebrew-values-cldr",
    version="1.0.0",
    admitted=True,
    values=STANDARD_HEBREW_LETTER_VALUES,
    source_copy_hash=(
        "7aaf40e62de1c1a6d8a6e4958528024a10ad270cf27e1aa1481e7aee4d0d8668"
    ),
    source_locator=(
        "Unicode CLDR release-46, common/rbnf/root.xml, ruleset type=\"hebrew\": "
        "letters map to 1-400 (20=כ ... 400=ת), 500-900 additive "
        "(500=ת″ק), 1000 spelled; no sofit letters used. Base "
        "22-letter identity->value only. sha256 over the pinned file."
    ),
    note=(
        "The standard Hebrew letter values (mispar hechrachi base), now "
        "licensed by CLDR (normative_standard -> computation). Only the base "
        "assignment is admitted; the final-form reading value is not covered "
        "by a writing standard and stays a primary_traditional acquisition."
    ),
)


# Both registries ship with zero admitted schemes. Admission is 1E-G-SOURCE's
# job; REPAIR only proves the machinery can hold a scheme correctly.
TRANSLITERATION_REGISTRY: tuple[TransliterationScheme, ...] = (
    LEGACY_LATIN_TRANSLITERATION,
)

VALUE_REGISTRY: tuple[ValueAssignment, ...] = (CANDIDATE_STANDARD_VALUES,)


def admitted_transliteration_schemes() -> list[TransliterationScheme]:
    """Return the admitted transliteration schemes -- currently none."""
    return [scheme for scheme in TRANSLITERATION_REGISTRY if scheme.admitted]


def admitted_value_schemes() -> list[ValueAssignment]:
    """Return the admitted value schemes -- currently none."""
    return [scheme for scheme in VALUE_REGISTRY if scheme.admitted]
