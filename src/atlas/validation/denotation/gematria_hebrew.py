"""Direct Hebrew orthography — letter identity from a normative standard.

1E-G-SOURCE-A begins with **direct Hebrew**, not transliteration, so the first
admitted path does not rest on an editorial Latin-to-Hebrew convention. A
Hebrew character maps to a Hebrew letter identity, and that mapping is sourced
to the Unicode Standard's Hebrew block -- a normative, machine-readable
standard whose claims are verified at runtime by :mod:`unicodedata`, not
transcribed from a book.

This is the one place a "source" is stronger than a paginated copy: the
letter-identity claim is executable. A test asserts every entry against
``unicodedata.name``, so the provenance cannot silently drift from the
standard it cites.

**Identity is not value.** Unicode assigns each letter a name but no numeric
value (`unicodedata.numeric` returns nothing for Hebrew letters), so this
module stops at identity. What a letter is *worth* is a traditional claim that
lives in :mod:`gematria_value_method` and is not sourced here.

Final forms (sofit) resolve to their base letter's identity -- a final kaf
*is* a kaf. Whether a final form carries a different *value* is a value-method
policy, kept separate on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from atlas.validation.denotation.gematria_orthography import (
    HEBREW_ONLY,
    OrthographyResult,
    ScopeStatus,
    check_scope,
)
from atlas.validation.denotation.gematria_transliteration import HebrewLetter


HEBREW_ORTHOGRAPHY_SCHEMA = "atlas.validation.denotation.gematria-hebrew.v1"

# The Unicode Standard, Hebrew block (U+0590–U+05FF). Cited as the source of
# letter identity; verifiable, versioned, and normative rather than
# interpretive.
UNICODE_SOURCE = {
    "standard": "The Unicode Standard",
    "block": "Hebrew (U+0590-U+05FF)",
    "verified_by": "unicodedata.name at runtime",
    "licenses": "letter identity only, never numeric value",
}


# Code point -> letter identity. Base letters are direct; final forms resolve
# to their base letter, since a final kaf is orthographically a kaf. Every
# entry is checked against unicodedata.name by the test suite, so this table
# cannot drift from the standard it claims.
HEBREW_LETTER_IDENTITY: dict[str, HebrewLetter] = {
    "א": HebrewLetter.ALEPH,
    "ב": HebrewLetter.BET,
    "ג": HebrewLetter.GIMEL,
    "ד": HebrewLetter.DALET,
    "ה": HebrewLetter.HE,
    "ו": HebrewLetter.VAV,
    "ז": HebrewLetter.ZAYIN,
    "ח": HebrewLetter.HET,
    "ט": HebrewLetter.TET,
    "י": HebrewLetter.YOD,
    "ך": HebrewLetter.KAF,     # final kaf
    "כ": HebrewLetter.KAF,
    "ל": HebrewLetter.LAMED,
    "ם": HebrewLetter.MEM,     # final mem
    "מ": HebrewLetter.MEM,
    "ן": HebrewLetter.NUN,     # final nun
    "נ": HebrewLetter.NUN,
    "ס": HebrewLetter.SAMEKH,
    "ע": HebrewLetter.AYIN,
    "ף": HebrewLetter.PE,      # final pe
    "פ": HebrewLetter.PE,
    "ץ": HebrewLetter.TSADI,   # final tsadi
    "צ": HebrewLetter.TSADI,
    "ק": HebrewLetter.QOF,
    "ר": HebrewLetter.RESH,
    "ש": HebrewLetter.SHIN,
    "ת": HebrewLetter.TAV,
}

# The five letters with distinct final forms, by code point. A value method
# that treats finals differently keys on these; identity does not.
FINAL_FORM_CODEPOINTS: frozenset[str] = frozenset(
    {"ך", "ם", "ן", "ף", "ץ"}
)


def orthography_standard_hash() -> str:
    """Return a deterministic hash of the letter-identity standard.

    Accompanies any numeric result so a total can be traced to the exact
    identity source that produced its letters -- and, paired with the value
    method hash, so a total can never be presented without naming *both* the
    standard that identified the letters and the tradition that valued them.
    """
    payload = {
        "schema": HEBREW_ORTHOGRAPHY_SCHEMA,
        "source": UNICODE_SOURCE,
        "identity": {
            char: letter.value
            for char, letter in sorted(HEBREW_LETTER_IDENTITY.items())
        },
    }

    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


class HebrewOrthographyError(ValueError):
    """Hebrew input could not be resolved to letter identities."""


def hebrew_letter_identity(char: str) -> HebrewLetter | None:
    """Return the letter identity of a Hebrew character, or None."""
    return HEBREW_LETTER_IDENTITY.get(char)


@dataclass(frozen=True, slots=True)
class HebrewReading:
    """The letter identities read from Hebrew input, with its scope audit."""

    orthography: OrthographyResult
    letters: tuple[HebrewLetter, ...]
    final_forms: tuple[bool, ...]

    @property
    def usable(self) -> bool:
        """Return whether identity resolution succeeded for every symbol."""
        return (
            self.orthography.usable
            and len(self.letters) == self.orthography.accepted_symbol_count
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": HEBREW_ORTHOGRAPHY_SCHEMA,
            "source": UNICODE_SOURCE,
            "orthography": self.orthography.to_dict(),
            "letters": [letter.value for letter in self.letters],
            "final_forms": list(self.final_forms),
            "usable": self.usable,
        }


def read_hebrew(text: str) -> HebrewReading:
    """Read Hebrew text into letter identities, fail-closed on scope.

    Latin input is blocked in this path: the scope policy accepts Hebrew
    script only, so the first admitted Hebrew path cannot be fed transliterated
    Latin by accident. Niqqud (combining vowel points) are stripped by the
    scope normalization, since they carry no letter identity.
    """
    scope = check_scope(text, HEBREW_ONLY)

    if scope.scope_status is not ScopeStatus.OK:
        return HebrewReading(orthography=scope, letters=(), final_forms=())

    letters: list[HebrewLetter] = []
    finals: list[bool] = []

    for char in scope.accepted_symbols:
        identity = hebrew_letter_identity(char)

        if identity is None:
            # In scope (Hebrew script) but not a letter -- e.g. a punctuation
            # mark in the Hebrew block. Refuse rather than skip.
            raise HebrewOrthographyError(
                f"Hebrew-script character {char!r} (U+{ord(char):04X}) has no "
                "letter identity; it is not one of the 22 letters."
            )

        letters.append(identity)
        finals.append(char in FINAL_FORM_CODEPOINTS)

    return HebrewReading(
        orthography=scope,
        letters=tuple(letters),
        final_forms=tuple(finals),
    )
