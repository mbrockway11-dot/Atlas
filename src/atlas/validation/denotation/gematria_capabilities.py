"""Gematria capability flags — identity separated from evaluability.

A single "gematria available" flag would hide the result 1E-G-SOURCE-A
established: a symbol can be *identified* by a normative standard without its
*value* being licensed by a tradition. So the flags separate the two, and
every stage downstream of value inherits value's blocked state.

Derived from the admitted schemes and methods, never set by hand. Each flag is
false unless its own evidence exists, and later flags require earlier ones --
equivalence cannot be searched without numeric evaluation, which cannot run
without an admitted value method.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.validation.denotation.gematria_hebrew import (
    HEBREW_LETTER_IDENTITY,
    orthography_standard_hash,
)
from atlas.validation.denotation.gematria_value_method import admitted_methods


GEMATRIA_CAPABILITIES_SCHEMA = (
    "atlas.validation.denotation.gematria-caps.v1"
)


@dataclass(frozen=True, slots=True)
class GematriaCapabilities:
    """What the gematria branch is currently permitted to do."""

    hebrew_letter_identity_available: bool
    value_method_available: bool
    numeric_evaluation_available: bool
    equivalence_search_available: bool
    denotation_available: bool
    orthography_standard_hash: str
    admitted_value_method_count: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": GEMATRIA_CAPABILITIES_SCHEMA,
            "hebrew_letter_identity_available": (
                self.hebrew_letter_identity_available
            ),
            "value_method_available": self.value_method_available,
            "numeric_evaluation_available": (
                self.numeric_evaluation_available
            ),
            "equivalence_search_available": (
                self.equivalence_search_available
            ),
            "denotation_available": self.denotation_available,
            "orthography_standard_hash": self.orthography_standard_hash,
            "admitted_value_method_count": self.admitted_value_method_count,
            "boundary": (
                "A normative standard establishes what a symbol is; it does "
                "not establish what a tradition says that symbol is worth. "
                "Identity is available, value is not."
            ),
        }


def derive_gematria_capabilities() -> GematriaCapabilities:
    """Derive gematria capability flags from admitted evidence."""
    # Identity is licensed by the Unicode standard, verified at runtime, so it
    # is available whenever the identity table is present.
    identity_available = len(HEBREW_LETTER_IDENTITY) == 27

    # Value requires an admitted, source-backed method. None is admitted.
    methods = admitted_methods()
    value_available = bool(methods)

    # Everything below value is gated on it. Numeric evaluation needs a value
    # method; equivalence search needs numeric evaluation and a comparison
    # corpus (not yet defined); denotation needs a citation corpus.
    numeric_available = identity_available and value_available
    equivalence_available = False  # 1E-G-SOURCE-B, blocked on value
    denotation_available = False  # 1E-G-SOURCE-C

    return GematriaCapabilities(
        hebrew_letter_identity_available=identity_available,
        value_method_available=value_available,
        numeric_evaluation_available=numeric_available,
        equivalence_search_available=equivalence_available,
        denotation_available=denotation_available,
        orthography_standard_hash=orthography_standard_hash(),
        admitted_value_method_count=len(methods),
    )
