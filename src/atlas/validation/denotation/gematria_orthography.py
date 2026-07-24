"""Gematria orthographic scope — explicit, fail-closed, auditable.

1E-G-CLASSIFY found that the legacy cipher accepts Hebrew characters
(``isalpha`` is true) and then drops every one at value lookup, returning an
empty sequence. That is silent truncation on in-domain input: a caller cannot
tell "the input was empty" from "the input was Hebrew and this scheme cannot
read it".

This module replaces the silent drop with a declared policy and a typed
result. Two states that the legacy code serialized identically are now
distinct:

    EMPTY_INPUT            the input had no characters
    NO_LICENSED_SYMBOLS    the input had characters, none in scope

The scope check never guesses. A scheme declares which scripts it accepts, and
anything outside them is reported as a rejected symbol rather than silently
skipped -- so the audit can see exactly what was refused and why.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata
from typing import Any


ORTHOGRAPHY_SCHEMA = "atlas.validation.denotation.gematria-orthography.v1"


class Script(str, Enum):
    """The scripts the scope check distinguishes."""

    LATIN = "latin"
    HEBREW = "hebrew"
    DIGIT = "digit"
    OTHER = "other"


class ScopeStatus(str, Enum):
    """The outcome of a scope check.

    Fail-closed: only ``OK`` permits downstream computation, and it requires
    at least one accepted symbol.
    """

    OK = "ok"
    EMPTY_INPUT = "empty_input"
    NO_LICENSED_SYMBOLS = "no_licensed_symbols"


class GematriaScopeError(ValueError):
    """Input fell outside a scheme's declared orthographic scope."""


def classify_char(char: str) -> Script:
    """Return the script of a single character.

    Uses the Unicode name rather than a codepoint range, so the classification
    is legible and does not silently miscategorise combining marks.
    """
    if char.isdigit():
        return Script.DIGIT

    try:
        name = unicodedata.name(char)
    except ValueError:
        return Script.OTHER

    if "HEBREW" in name:
        return Script.HEBREW

    if "LATIN" in name:
        return Script.LATIN

    return Script.OTHER


@dataclass(frozen=True, slots=True)
class ScopePolicy:
    """A scheme's declared orthographic scope.

    Every cipher must state these before it may run, so that out-of-scope
    behaviour is a decision on the record rather than an accident of which
    lookups happen to miss.
    """

    policy_id: str
    accepted_scripts: frozenset[Script]
    # Whether case is folded and combining marks stripped before scope check.
    normalization_policy: str = "casefold_and_strip_marks"

    def normalize(self, text: str) -> str:
        """Return the text under the declared normalization policy."""
        folded = text.casefold()
        decomposed = unicodedata.normalize("NFD", folded)

        return "".join(
            char
            for char in decomposed
            if not unicodedata.combining(char)
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "policy_id": self.policy_id,
            "accepted_scripts": sorted(s.value for s in self.accepted_scripts),
            "normalization_policy": self.normalization_policy,
        }


@dataclass(frozen=True, slots=True)
class OrthographyResult:
    """The audit record of one scope check.

    Carries enough to explain any downstream silence: how long the input was,
    how many symbols survived, and exactly which were rejected.
    """

    policy_id: str
    input_length: int
    accepted_symbols: tuple[str, ...]
    rejected_symbols: tuple[tuple[str, str], ...]
    scope_status: ScopeStatus

    @property
    def accepted_symbol_count(self) -> int:
        """Return how many symbols were in scope."""
        return len(self.accepted_symbols)

    @property
    def usable(self) -> bool:
        """Return whether downstream computation may proceed."""
        return self.scope_status is ScopeStatus.OK

    def require_usable(self) -> None:
        """Raise unless the input is usable, naming the reason.

        The fail-closed gate: a caller that forgets to check ``usable`` gets
        an exception, not an empty result that looks like a legitimate zero.
        """
        if self.scope_status is ScopeStatus.EMPTY_INPUT:
            raise GematriaScopeError(
                f"{self.policy_id}: input was empty; nothing to compute."
            )

        if self.scope_status is ScopeStatus.NO_LICENSED_SYMBOLS:
            rejected = ", ".join(
                f"{char!r}({script})"
                for char, script in self.rejected_symbols[:8]
            )
            raise GematriaScopeError(
                f"{self.policy_id}: input had {self.input_length} characters, "
                f"none within scope. Rejected: {rejected}. This is the "
                "silent-truncation defect refusing to be silent."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": ORTHOGRAPHY_SCHEMA,
            "policy_id": self.policy_id,
            "input_length": self.input_length,
            "accepted_symbol_count": self.accepted_symbol_count,
            "accepted_symbols": list(self.accepted_symbols),
            "rejected_symbols": [
                {"symbol": char, "script": script}
                for char, script in self.rejected_symbols
            ],
            "scope_status": self.scope_status.value,
            "usable": self.usable,
        }


def check_scope(text: str, policy: ScopePolicy) -> OrthographyResult:
    """Return the scope audit for one input under one policy.

    Never raises on out-of-scope input; it records the rejection. Callers
    raise via :meth:`OrthographyResult.require_usable` when they need to
    proceed, so the refusal is explicit at the point of use.
    """
    normalized = policy.normalize(text)

    accepted: list[str] = []
    rejected: list[tuple[str, str]] = []

    for char in normalized:
        script = classify_char(char)

        if script in policy.accepted_scripts:
            accepted.append(char)
        else:
            rejected.append((char, script.value))

    if not normalized:
        status = ScopeStatus.EMPTY_INPUT
    elif not accepted:
        status = ScopeStatus.NO_LICENSED_SYMBOLS
    else:
        status = ScopeStatus.OK

    return OrthographyResult(
        policy_id=policy.policy_id,
        input_length=len(normalized),
        accepted_symbols=tuple(accepted),
        rejected_symbols=tuple(rejected),
        scope_status=status,
    )


# The two declared policies. Latin-only is honest about what the legacy tables
# actually process; Hebrew-only is declared now so that a future sourced
# Hebrew scheme has a scope to attach to, even though no such scheme is
# admitted yet.
LATIN_ONLY = ScopePolicy(
    policy_id="latin-only-v1",
    accepted_scripts=frozenset({Script.LATIN}),
)

HEBREW_ONLY = ScopePolicy(
    policy_id="hebrew-only-v1",
    accepted_scripts=frozenset({Script.HEBREW}),
)
