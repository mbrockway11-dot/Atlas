"""The frozen tradition declaration for the numerology corpus.

"Pythagorean" in modern numerology is a **marketing lineage, not a historical
provenance claim**. Declaring that explicitly is what stops the corpus from
smuggling in an unsupported assertion about ancient Greek mathematics simply
by naming itself.

The declaration is frozen and hashed alongside the corpus and admissibility
rules, so a later change to what the tradition claims about itself invalidates
dictionaries built under the old claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any


TRADITION_SCHEMA = "atlas.validation.denotation.numerology-tradition.v1"

TRADITION_ID = "modern-american-pythagorean-numerology-v1"


class SourceRole(str, Enum):
    """What role an edition plays in the corpus.

    Strata are never merged. A historical precursor cannot join a canonical
    consensus, because shared marketing under the word "Pythagorean" is not
    evidence that two authors' constructs, reductions or semantic scopes
    agree.
    """

    CANONICAL = "canonical"
    HISTORICAL_PRECURSOR = "historical_precursor"


class VerificationStatus(str, Enum):
    """How far an edition's bibliography has been independently confirmed.

    Recorded because a provenance artifact that cannot distinguish a checked
    citation from an asserted one provides no provenance at all.
    """

    VERIFIED = "verified"
    DECLARED_UNVERIFIED = "declared_unverified"
    DISCREPANT = "discrepant"


@dataclass(frozen=True, slots=True)
class TraditionDeclaration:
    """What this tradition is, and explicitly what it is not."""

    tradition_id: str
    historical_claim: str
    scope: str
    not_equivalent_to: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": TRADITION_SCHEMA,
            "tradition_id": self.tradition_id,
            "historical_claim": self.historical_claim,
            "scope": self.scope,
            "not_equivalent_to": list(self.not_equivalent_to),
        }

    def declaration_hash(self) -> str:
        """Return a deterministic hash of the declaration."""
        return hashlib.sha256(
            json.dumps(
                self.to_dict(), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()


MODERN_AMERICAN_PYTHAGOREAN = TraditionDeclaration(
    tradition_id=TRADITION_ID,
    # The load-bearing field. "Pythagorean" here names a modern lineage of
    # practice, and asserts nothing about antiquity.
    historical_claim="none",
    scope=(
        "English-language name-and-birth-date numerology using the 1-9 "
        "alphabetic assignment convention"
    ),
    not_equivalent_to=(
        "ancient Pythagorean mathematics",
        "ancient Greek number symbolism",
        "Chaldean numerology",
    ),
)


# Source categories excluded from the first corpus entirely. Listed so an
# exclusion is a policy with a reason rather than an omission someone has to
# reconstruct later.
EXCLUDED_SOURCE_CATEGORIES: tuple[tuple[str, str], ...] = (
    (
        "unattributed_websites",
        "no identifiable author, edition or locator",
    ),
    (
        "meaning_of_number_lists",
        "contemporary listicles with no attributable tradition",
    ),
    (
        "multi_tradition_syntheses",
        "blend traditions, so a mapping cannot be attributed to one",
    ),
    (
        "correspondence_tables",
        "Kamea or astrological tables would import another system's reading, "
        "which is the cross-system inheritance 1E forbids",
    ),
    (
        "reprints_without_original_pagination",
        "a facsimile is an access route to a source, not an independent "
        "corroborating source; excluded when a stable historical scan exists",
    ),
    (
        "taught_by_pythagoras_claims",
        "a claim of ancient authority is not a denotation of a value",
    ),
)
