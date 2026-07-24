"""Gematria value methods — named precisely, and unadmitted.

Gematria has several computational methods, so the first admitted one must be
named exactly, never called simply "gematria". A :class:`ValueMethod` records
every choice that affects the number: the alphabet, the per-letter values, how
final forms are treated, normalization, word boundaries, and how multi-letter
sequences compose into a value.

Unicode sources letter *identity* but assigns Hebrew letters no numeric value,
so values are a **traditional claim** and need a traditional source. This
module supplies the machinery and the standard method's structure, but ships
**zero admitted methods**: admission requires a source copy hash and a
locator, which 1E-G-SOURCE-A does not have. The pipeline therefore emits
licensed letter identities today and fail-closes at the value stage -- the
same acquisition wall numerology hit, in a different layer.

Nothing here licenses equivalence, corpus selection, or symbolism. A source
that fixes letter values fixes letter values and nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from atlas.validation.denotation.gematria_transliteration import HebrewLetter


VALUE_METHOD_SCHEMA = "atlas.validation.denotation.gematria-method.v1"


class FinalLetterPolicy(str, Enum):
    """How a method values the five final forms.

    A real methodological fork: standard absolute value treats a final kaf as
    20, while some methods assign the finals 500-900. The policy is part of
    the method's identity, not an afterthought.
    """

    SAME_AS_BASE = "same_as_base"
    EXTENDED_500_900 = "extended_500_900"


class NumberComposition(str, Enum):
    """How per-letter values combine into a word value."""

    SUM = "sum"                    # absolute value: add the letters
    PRODUCT = "product"            # multiplicative methods
    ORDINAL_SUM = "ordinal_sum"    # each letter's ordinal position, summed


class ValueMethodError(ValueError):
    """A value method was constructed or used invalidly."""


@dataclass(frozen=True, slots=True)
class ValueMethod:
    """One precisely specified gematria value method."""

    method_id: str
    alphabet: str
    letter_values: Mapping[HebrewLetter, int]
    final_letter_policy: FinalLetterPolicy
    final_values: Mapping[HebrewLetter, int]
    normalization_policy: str
    word_boundary_policy: str
    number_composition: NumberComposition
    admitted: bool
    source_copy_hash: str
    source_locator: str

    def __post_init__(self) -> None:
        if self.admitted and not (
            self.source_copy_hash and self.source_locator
        ):
            raise ValueMethodError(
                f"{self.method_id} cannot be admitted without a source copy "
                "hash and a locator: letter values are a traditional claim "
                "and need a traditional source."
            )

        if (
            self.final_letter_policy is FinalLetterPolicy.EXTENDED_500_900
            and not self.final_values
        ):
            raise ValueMethodError(
                f"{self.method_id} declares extended finals but assigns no "
                "final values."
            )

    def value_of(self, letter: HebrewLetter, *, final: bool = False) -> int:
        """Return one letter's value under this method."""
        if (
            final
            and self.final_letter_policy is FinalLetterPolicy.EXTENDED_500_900
            and letter in self.final_values
        ):
            return self.final_values[letter]

        if letter not in self.letter_values:
            raise ValueMethodError(
                f"{self.method_id}: no value for {letter.value!r}."
            )

        return self.letter_values[letter]

    def method_hash(self) -> str:
        """Return a deterministic hash of every choice the method makes."""
        payload = {
            "schema": VALUE_METHOD_SCHEMA,
            "method_id": self.method_id,
            "alphabet": self.alphabet,
            "letter_values": {
                letter.value: value
                for letter, value in sorted(
                    self.letter_values.items(), key=lambda kv: kv[0].value
                )
            },
            "final_letter_policy": self.final_letter_policy.value,
            "final_values": {
                letter.value: value
                for letter, value in sorted(
                    self.final_values.items(), key=lambda kv: kv[0].value
                )
            },
            "normalization_policy": self.normalization_policy,
            "word_boundary_policy": self.word_boundary_policy,
            "number_composition": self.number_composition.value,
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def provenance(self) -> dict[str, Any]:
        """Return the method's provenance record."""
        return {
            "method_id": self.method_id,
            "method_hash": self.method_hash(),
            "admitted": self.admitted,
            "source_copy_hash": self.source_copy_hash,
            "source_locator": self.source_locator,
        }


# Standard absolute value (mispar hechrachi), structured but NOT admitted.
# The values are widely attested, but 1E requires a source copy and locator,
# and 1E-G-SOURCE-A has neither -- so this is a candidate, present to exercise
# the machinery, licensing nothing.
_ABSOLUTE_VALUES: dict[HebrewLetter, int] = {
    HebrewLetter.ALEPH: 1, HebrewLetter.BET: 2, HebrewLetter.GIMEL: 3,
    HebrewLetter.DALET: 4, HebrewLetter.HE: 5, HebrewLetter.VAV: 6,
    HebrewLetter.ZAYIN: 7, HebrewLetter.HET: 8, HebrewLetter.TET: 9,
    HebrewLetter.YOD: 10, HebrewLetter.KAF: 20, HebrewLetter.LAMED: 30,
    HebrewLetter.MEM: 40, HebrewLetter.NUN: 50, HebrewLetter.SAMEKH: 60,
    HebrewLetter.AYIN: 70, HebrewLetter.PE: 80, HebrewLetter.TSADI: 90,
    HebrewLetter.QOF: 100, HebrewLetter.RESH: 200, HebrewLetter.SHIN: 300,
    HebrewLetter.TAV: 400,
}


# What a normative Hebrew numeral-system authority must explicitly specify
# before it may license the value table. The P1 integration test reclassified
# the value table as a normative computation claim, but "standard Hebrew
# numerals" and "every gematria method" are not identical, so the gate stays
# closed until a source covers these. The first five are mandatory; the last
# is conditional on whether thousands/punctuation are in the method's scope.
NUMERAL_SYSTEM_REQUIREMENTS: dict[str, str] = {
    "units_1_9": "aleph-tet map to 1-9",
    "tens_10_90": "yod-tsadi map to 10-90",
    "hundreds_100_400": "qof-tav map to 100-400",
    "final_form_treatment": "how the five final forms are valued",
    "above_400_policy": (
        "whether values above 400 are compositional or use extended "
        "final-letter values (500-900)"
    ),
    "thousands_and_punctuation": (
        "thousands and punctuation conventions, if within the method's scope"
    ),
}

MANDATORY_NUMERAL_REQUIREMENTS: frozenset[str] = frozenset(
    {
        "units_1_9",
        "tens_10_90",
        "hundreds_100_400",
        "final_form_treatment",
        "above_400_policy",
    }
)

# The candidate normative authorities, in the order they are to be tested. A
# lower-priority candidate is considered only if the ones above it do not
# suffice. Unicode CLDR is last and conditional: it models Hebrew numerals as
# an algorithmic numbering system, but its exact rules must be inspected to
# confirm they expose the mapping and policies above before it is treated as
# sufficient.
NUMERAL_AUTHORITY_CANDIDATES: tuple[str, ...] = (
    "official_hebrew_or_governmental_numeral_standard",
    "scholarly_grammar_of_hebrew_numeration",
    "unicode_cldr_hebrew_algorithmic_numbering",
)


def numeral_source_sufficient(covered: frozenset[str]) -> bool:
    """Return whether a candidate covers every mandatory requirement.

    The acceptance gate for the value-table source. A source that does not
    explicitly specify the mapping, final-form treatment and above-400 policy
    is not sufficient, however standard its values look.
    """
    return MANDATORY_NUMERAL_REQUIREMENTS <= covered


MISPAR_HECHRACHI_CANDIDATE = ValueMethod(
    method_id="mispar-hechrachi-candidate-uncited",
    alphabet="hebrew-22",
    letter_values=_ABSOLUTE_VALUES,
    final_letter_policy=FinalLetterPolicy.SAME_AS_BASE,
    final_values={},
    normalization_policy="strip_niqqud_and_marks",
    word_boundary_policy="whitespace_separated",
    number_composition=NumberComposition.SUM,
    admitted=False,
    source_copy_hash="",
    source_locator="",
)


# Zero admitted methods. Admission is downstream work with a real source.
METHOD_REGISTRY: tuple[ValueMethod, ...] = (MISPAR_HECHRACHI_CANDIDATE,)


def admitted_methods() -> list[ValueMethod]:
    """Return the admitted value methods -- currently none."""
    return [method for method in METHOD_REGISTRY if method.admitted]
