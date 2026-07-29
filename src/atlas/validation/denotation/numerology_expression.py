"""Numerology computation — the expression layer, and only that.

This module knows nothing about the shared ontology. It computes numbers from
a name and a date by frozen arithmetic and records how it reduced them. It does
not import :mod:`atlas.validation.denotation.ontology`, and a test enforces
that it never will: the moment computation can see the vocabulary it feeds, the
independence the audit rests on is gone.

Reduction is part of the expression, not incidental preprocessing. Two
policies that treat 11/22/33 differently produce different expressions, so the
policy identifier and the full reduction trace travel with every value. A
dictionary entry keyed to one policy cannot silently apply to another.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from typing import Any


NUMEROLOGY_EXPRESSION_VERSION = "1.0.0"

# Pythagorean letter values, the most widely documented Western mapping. Named
# so a later Chaldean version is a different, non-blended policy rather than an
# edit to this one.
PYTHAGOREAN = {
    "a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9,
    "j": 1, "k": 2, "l": 3, "m": 4, "n": 5, "o": 6, "p": 7, "q": 8, "r": 9,
    "s": 1, "t": 2, "u": 3, "v": 4, "w": 5, "x": 6, "y": 7, "z": 8,
}

VOWELS = frozenset("aeiou")

# Values left unreduced by this arithmetic. Part of the reduction identifier:
# a version that reduces these is a different policy.
#
# Preserving them is a *computational* choice and carries no claim that any
# source licenses meanings for them. The identifier is named for what the
# arithmetic does rather than for a tradition, so that it cannot be read as
# an assertion that Jordan or the wider tradition endorses all three -- a
# value can be preserved here and still compile to silence for want of a
# passage that denotes it.
MASTER_VALUES = frozenset({11, 22, 33})

REDUCTION_POLICY = "alphabetic-1to9-preserve-11-22-33-v1"


class NumerologyExpressionError(ValueError):
    """A numerology expression could not be computed as specified."""


@dataclass(frozen=True, slots=True)
class NumerologyExpression:
    """One computed numerological quantity, with its reduction trace.

    ``raw_value`` is the pre-reduction sum; ``reduced_value`` is the result
    under the frozen policy; ``reduction_trace`` is every intermediate sum, so
    the computation is auditable and policy-distinguishable.
    """

    quantity: str
    raw_value: int
    reduced_value: int
    reduction_trace: tuple[int, ...]
    reduction_policy: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "quantity": self.quantity,
            "raw_value": self.raw_value,
            "reduced_value": self.reduced_value,
            "reduction_trace": list(self.reduction_trace),
            "reduction_policy": self.reduction_policy,
            "version": self.version,
        }


def _reduce(value: int) -> tuple[int, tuple[int, ...]]:
    """Reduce a value under the master-number policy, tracing each step."""
    trace = [value]

    while value > 9 and value not in MASTER_VALUES:
        value = sum(int(digit) for digit in str(value))
        trace.append(value)

    return value, tuple(trace)


def _letters(name: str) -> str:
    """Return the lowercase A-Z letters of a name, dropping everything else.

    The drop is the frozen transliteration rule: punctuation, whitespace and
    non-Latin characters carry no Pythagorean value. Recorded here because it
    is part of the expression, and a name reaching this function is assumed to
    already be the canonical form the policy names.
    """
    return "".join(char for char in name.lower() if char in PYTHAGOREAN)


def _named_sum(name: str, letters_allowed: frozenset[str] | None) -> int:
    """Sum a name's letter values, optionally restricted to a letter set."""
    return sum(
        PYTHAGOREAN[char]
        for char in _letters(name)
        if letters_allowed is None or char in letters_allowed
    )


def _expression(quantity: str, raw_value: int) -> NumerologyExpression:
    """Build one expression from a raw sum."""
    reduced, trace = _reduce(raw_value)

    return NumerologyExpression(
        quantity=quantity,
        raw_value=raw_value,
        reduced_value=reduced,
        reduction_trace=trace,
        reduction_policy=REDUCTION_POLICY,
        version=NUMEROLOGY_EXPRESSION_VERSION,
    )


def life_path(birth_date: date) -> NumerologyExpression:
    """Return the life-path number: reduced sum of the full birth date."""
    digits = sum(
        int(char)
        for char in f"{birth_date.year:04d}{birth_date.month:02d}"
        f"{birth_date.day:02d}"
    )

    return _expression("life_path", digits)


def expression_number(name: str) -> NumerologyExpression:
    """Return the expression number: reduced sum of all name letters."""
    return _expression("expression_number", _named_sum(name, None))


def soul_urge(name: str) -> NumerologyExpression:
    """Return the soul-urge number: reduced sum of vowels only."""
    return _expression("soul_urge", _named_sum(name, VOWELS))


def personality_number(name: str) -> NumerologyExpression:
    """Return the personality number: reduced sum of consonants only."""
    consonants = frozenset(PYTHAGOREAN) - VOWELS

    return _expression("personality_number", _named_sum(name, consonants))


def birthday_number(birth_date: date) -> NumerologyExpression:
    """Return the birthday number: reduced day of month."""
    return _expression("birthday_number", birth_date.day)


# The frozen, complete set of computable quantities. A dictionary entry keyed
# to anything outside this set addresses a construct the code does not produce,
# and the claim assembler must reject it.
COMPUTABLE_QUANTITIES: tuple[str, ...] = (
    "life_path",
    "expression_number",
    "soul_urge",
    "personality_number",
    "birthday_number",
)


# A denotation of the reduced value itself, independent of which quantity
# produced it. A source's general statement -- Jordan's "Significance and
# Meaning of Numbers" says what a number *is*, not what one computed quantity
# means -- keys to this sentinel and applies to every quantity that reduces to
# the value. It is not a computable quantity: nothing is computed *as* the
# value itself, so an entry carrying it must declare its citation
# quantity-independent, and lookup falls back to it only when no quantity-
# specific entry exists.
VALUE_ITSELF = "value_itself"


def build_expressions(
    name: str, birth_date: date
) -> dict[str, NumerologyExpression]:
    """Compute every supported quantity for one subject."""
    return {
        "life_path": life_path(birth_date),
        "expression_number": expression_number(name),
        "soul_urge": soul_urge(name),
        "personality_number": personality_number(name),
        "birthday_number": birthday_number(birth_date),
    }


def expression_set_hash() -> str:
    """Return a hash of the computable-quantity set and reduction policy.

    Enters the artifact hash so a change to what numerology computes, or to
    how it reduces, invalidates concordance built against the old behaviour.
    """
    payload = {
        "version": NUMEROLOGY_EXPRESSION_VERSION,
        "reduction_policy": REDUCTION_POLICY,
        "quantities": list(COMPUTABLE_QUANTITIES),
        "master_values": sorted(MASTER_VALUES),
    }

    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
