"""Name transformations for invariance and perturbation experiments.

Two catalogues live here, and the distinction between them is the point.

*Invariance* transformations are things a name-handling system might
plausibly be expected to shrug off -- case, whitespace, punctuation. Each one
carries its expected behaviour **declared in advance**, so the experiment
tests a prediction rather than describing whatever happened.

*Perturbations* are graded corruptions used to trace how similarity decays as
a name is damaged. Because the baseline showed name length drives 30% of
score variance, each perturbation records whether it preserves length: a
length-preserving edit and a length-changing edit of the same severity are
not comparable, and mixing them would re-measure the confounder.

Every transformation is deterministic given its seed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata
from typing import Callable

import numpy as np


class Expectation(str, Enum):
    """What a transformation is predicted to do to the vector."""

    INVARIANT = "expected_invariant"
    NEAR_INVARIANT = "expected_near_invariant"
    VARIANT = "expected_variant"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class Transformation:
    """One named transformation with its declared expectation."""

    name: str
    expectation: Expectation
    rationale: str
    apply: Callable[[str], str]
    preserves_length: bool = False


# ---------------------------------------------------------------------------
# Invariance catalogue
# ---------------------------------------------------------------------------


def _strip_accents(value: str) -> str:
    """Return the string with combining marks removed."""
    decomposed = unicodedata.normalize("NFD", value)

    return unicodedata.normalize(
        "NFC",
        "".join(ch for ch in decomposed if not unicodedata.combining(ch)),
    )


def _remove_suffix(value: str) -> str:
    """Drop a trailing generational or honorific suffix."""
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "phd", "md"}
    tokens = value.split()

    if len(tokens) > 1 and tokens[-1].lower().strip(".,") in suffixes:
        return " ".join(tokens[:-1])

    return value


def _remove_middle(value: str) -> str:
    """Drop middle tokens, keeping first and last."""
    tokens = value.split()

    return " ".join([tokens[0], tokens[-1]]) if len(tokens) > 2 else value


def _initialize_middle(value: str) -> str:
    """Reduce middle tokens to initials."""
    tokens = value.split()

    if len(tokens) < 3:
        return value

    middle = [f"{token[0]}." for token in tokens[1:-1] if token]

    return " ".join([tokens[0], *middle, tokens[-1]])


def _reverse_tokens(value: str) -> str:
    """Reverse token order, e.g. 'Ada Lovelace' -> 'Lovelace Ada'."""
    return " ".join(reversed(value.split()))


def _swap_first_last(value: str) -> str:
    """Swap the first and last tokens, keeping the middle in place."""
    tokens = value.split()

    if len(tokens) < 2:
        return value

    tokens[0], tokens[-1] = tokens[-1], tokens[0]

    return " ".join(tokens)


INVARIANCE_TRANSFORMATIONS: tuple[Transformation, ...] = (
    Transformation(
        "lowercase",
        Expectation.AMBIGUOUS,
        "Ciphers may or may not fold case; the answer is a property of the "
        "encoding, not something to assume either way.",
        str.lower,
        preserves_length=True,
    ),
    Transformation(
        "uppercase",
        Expectation.AMBIGUOUS,
        "As lowercase; tested separately in case folding is asymmetric.",
        str.upper,
        preserves_length=True,
    ),
    Transformation(
        "surrounding_whitespace",
        Expectation.INVARIANT,
        "Leading and trailing whitespace carries no information about a "
        "name and should never reach the encoder.",
        lambda value: f"  {value}  ",
    ),
    Transformation(
        "repeated_internal_whitespace",
        Expectation.INVARIANT,
        "Double spacing between tokens is a typing artefact, not a "
        "different name.",
        lambda value: value.replace(" ", "  "),
    ),
    Transformation(
        "punctuation_removed",
        Expectation.NEAR_INVARIANT,
        "Removing periods and commas usually preserves the name, but "
        "changes character count, which the baseline showed matters.",
        lambda value: "".join(
            ch for ch in value if ch not in ".,'’-"
        ).replace("  ", " "),
    ),
    Transformation(
        "hyphen_to_space",
        Expectation.NEAR_INVARIANT,
        "Hyphenated surnames are commonly written either way; token count "
        "changes, so exact invariance is not expected.",
        lambda value: value.replace("-", " "),
        preserves_length=True,
    ),
    Transformation(
        "apostrophe_removed",
        Expectation.NEAR_INVARIANT,
        "O'Brien and OBrien refer to the same person; length changes.",
        lambda value: value.replace("'", "").replace("’", ""),
    ),
    Transformation(
        "diacritics_stripped",
        Expectation.VARIANT,
        "Stripping accents changes the characters the cipher sees. Treated "
        "as variant rather than invariant precisely because the corpus "
        "contains transliteration families that must not be conflated.",
        _strip_accents,
        preserves_length=True,
    ),
    Transformation(
        "suffix_removed",
        Expectation.VARIANT,
        "Dropping 'Jr' removes real tokens and characters.",
        _remove_suffix,
    ),
    Transformation(
        "middle_name_removed",
        Expectation.VARIANT,
        "A substantial deletion; expected to move the vector.",
        _remove_middle,
    ),
    Transformation(
        "middle_initialized",
        Expectation.VARIANT,
        "Initialisation preserves the token but replaces its characters.",
        _initialize_middle,
    ),
    Transformation(
        "token_order_reversed",
        Expectation.AMBIGUOUS,
        "Whether order matters is a property of the encoding. If reversal "
        "is invariant, the model is a bag of characters.",
        _reverse_tokens,
        preserves_length=True,
    ),
    Transformation(
        "first_last_swapped",
        Expectation.AMBIGUOUS,
        "As above, but preserving any middle tokens in place.",
        _swap_first_last,
        preserves_length=True,
    ),
)


# ---------------------------------------------------------------------------
# Perturbation catalogue
# ---------------------------------------------------------------------------


_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def _letter_positions(value: str) -> list[int]:
    """Return indices of alphabetic characters."""
    return [index for index, ch in enumerate(value) if ch.isalpha()]


def substitute(value: str, *, count: int, rng: np.random.Generator) -> str:
    """Replace `count` letters with different letters, preserving length."""
    positions = _letter_positions(value)

    if not positions:
        return value

    chars = list(value)
    chosen = rng.choice(
        len(positions), size=min(count, len(positions)), replace=False
    )

    for index in chosen:
        position = positions[int(index)]
        original = chars[position].lower()
        options = [ch for ch in _ALPHABET if ch != original]
        replacement = options[int(rng.integers(0, len(options)))]

        chars[position] = (
            replacement.upper() if chars[position].isupper() else replacement
        )

    return "".join(chars)


def delete_characters(
    value: str, *, count: int, rng: np.random.Generator
) -> str:
    """Delete `count` letters."""
    positions = _letter_positions(value)

    if not positions:
        return value

    chosen = {
        positions[int(index)]
        for index in rng.choice(
            len(positions), size=min(count, len(positions)), replace=False
        )
    }

    return "".join(
        ch for index, ch in enumerate(value) if index not in chosen
    )


def insert_characters(
    value: str, *, count: int, rng: np.random.Generator
) -> str:
    """Insert `count` random letters at random positions."""
    chars = list(value)

    for _ in range(count):
        position = int(rng.integers(0, len(chars) + 1))
        chars.insert(position, _ALPHABET[int(rng.integers(0, 26))])

    return "".join(chars)


def transpose_adjacent(
    value: str, *, count: int, rng: np.random.Generator
) -> str:
    """Swap `count` adjacent letter pairs, preserving length."""
    chars = list(value)
    positions = [
        index
        for index in _letter_positions(value)
        if index + 1 < len(chars) and chars[index + 1].isalpha()
    ]

    if not positions:
        return value

    chosen = rng.choice(
        len(positions), size=min(count, len(positions)), replace=False
    )

    for index in chosen:
        position = positions[int(index)]
        chars[position], chars[position + 1] = (
            chars[position + 1],
            chars[position],
        )

    return "".join(chars)


def delete_token(value: str, *, rng: np.random.Generator) -> str:
    """Delete one whole token."""
    tokens = value.split()

    if len(tokens) < 2:
        return value

    index = int(rng.integers(0, len(tokens)))

    return " ".join(tokens[:index] + tokens[index + 1 :])


def shuffle_characters(value: str, *, rng: np.random.Generator) -> str:
    """Shuffle all letters, preserving length and letter multiset.

    The strongest degeneracy probe available: if a full shuffle stays close
    to the original, the encoding is order-insensitive and is effectively
    measuring letter composition.
    """
    positions = _letter_positions(value)
    letters = [value[index] for index in positions]
    rng.shuffle(letters)

    chars = list(value)

    for position, letter in zip(positions, letters):
        chars[position] = letter

    return "".join(chars)


def length_matched_random(value: str, *, rng: np.random.Generator) -> str:
    """Return an unrelated name with the same length and token shape.

    The critical control given the length confounder: any residual
    similarity here is attributable to shape alone.
    """
    tokens = value.split()

    return " ".join(
        "".join(_ALPHABET[int(rng.integers(0, 26))] for _ in token)
        for token in tokens
    )


@dataclass(frozen=True, slots=True)
class Perturbation:
    """One graded perturbation."""

    name: str
    severity: int
    preserves_length: bool
    apply: Callable[[str, np.random.Generator], str]


def build_perturbations(
    *,
    max_severity: int = 4,
) -> tuple[Perturbation, ...]:
    """Return the graded perturbation catalogue."""
    perturbations: list[Perturbation] = []

    for severity in range(1, max_severity + 1):
        perturbations.extend(
            (
                Perturbation(
                    "substitution",
                    severity,
                    True,
                    lambda v, r, n=severity: substitute(v, count=n, rng=r),
                ),
                Perturbation(
                    "deletion",
                    severity,
                    False,
                    lambda v, r, n=severity: delete_characters(
                        v, count=n, rng=r
                    ),
                ),
                Perturbation(
                    "insertion",
                    severity,
                    False,
                    lambda v, r, n=severity: insert_characters(
                        v, count=n, rng=r
                    ),
                ),
                Perturbation(
                    "transposition",
                    severity,
                    True,
                    lambda v, r, n=severity: transpose_adjacent(
                        v, count=n, rng=r
                    ),
                ),
            )
        )

    perturbations.extend(
        (
            Perturbation(
                "token_deletion", 1, False,
                lambda v, r: delete_token(v, rng=r),
            ),
            Perturbation(
                "character_shuffle", 99, True,
                lambda v, r: shuffle_characters(v, rng=r),
            ),
            Perturbation(
                "length_matched_random", 99, True,
                lambda v, r: length_matched_random(v, rng=r),
            ),
        )
    )

    return tuple(perturbations)
