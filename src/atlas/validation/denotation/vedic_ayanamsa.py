"""The ayanamsa choice, made explicit — computed, but not licensed.

1E-V-CLASSIFY found the ayanamsa to be Vedic's load-bearing choice: Vedic is
sidereal, so tropical positions are offset before any sign, nakshatra or house
is assigned, and Lahiri, Raman and Krishnamurti disagree by more than a
nakshatra pada. This module makes that choice explicit configuration and draws
the line the whole milestone turns on:

    "Swiss Ephemeris computed this offset"        reproducible computation
    "this tradition licenses this ayanamsa"       acquisition-blocked

The first is recorded and verifiable -- a test recomputes every offset via
swisseph, the same executable-source pattern the Hebrew identity table uses.
The second is a school-specific claim needing a source, so **every choice
ships not admitted**. A computed offset is data; a licensed choice is
evidence, and this phase has only the former.

The data-level laundering rule for Vedic lives here too: a result carrying any
sidereal quantity must name the ayanamsa choice that produced it, or it may
not be serialized.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


AYANAMSA_SCHEMA = "atlas.validation.denotation.vedic-ayanamsa.v1"

# The reference epoch at which recorded offsets are anchored. J2000.0, as a
# Julian day; a fixed anchor so the recorded value is a single reproducible
# number rather than a date-dependent range.
REFERENCE_EPOCH_JD = 2451545.0
REFERENCE_EPOCH_LABEL = "J2000.0 (2000-01-01 12:00 TT)"

# The pinned computation provider. Recorded so a recomputation can be shown to
# have used the same engine.
EPHEMERIS_PROVIDER = "swiss_ephemeris"
EPHEMERIS_PROVIDER_VERSION = "2.10.03"

# Sidereal quantities that may not be serialized without an ayanamsa choice
# hash. All of them depend on the offset, so none is reproducible from the
# ephemeris alone.
SIDEREAL_QUANTITY_KEYS: frozenset[str] = frozenset(
    {
        "sidereal_longitude",
        "nakshatra",
        "sidereal_sign",
        "divisional_placement",
        "dasha",
    }
)


class AyanamsaError(ValueError):
    """An ayanamsa choice or sidereal result was handled invalidly."""


@dataclass(frozen=True, slots=True)
class AyanamsaChoice:
    """One ayanamsa scheme, its computed offset, and its licensing state."""

    scheme_id: str
    provider: str
    provider_constant: str
    epoch_label: str
    epoch_jd: float
    computed_offset_degrees: float
    computation_library_version: str
    admitted: bool
    source_copy_hash: str
    source_locator: str

    def __post_init__(self) -> None:
        if self.admitted and not (
            self.source_copy_hash and self.source_locator
        ):
            raise AyanamsaError(
                f"{self.scheme_id} cannot be admitted without a source: a "
                "computed offset is reproducible, but choosing this ayanamsa "
                "is a school-specific claim that needs one."
            )

    def choice_hash(self) -> str:
        """Return a deterministic hash of the choice.

        Excludes the licensing fields: two builds that computed the same
        offset from the same provider describe the same *choice*, whether or
        not a source has since licensed it. Licensing is tracked by
        ``admitted``, not by the identity of the offset.
        """
        payload = {
            "schema": AYANAMSA_SCHEMA,
            "scheme_id": self.scheme_id,
            "provider": self.provider,
            "provider_constant": self.provider_constant,
            "epoch_jd": self.epoch_jd,
            "computed_offset_degrees": round(
                self.computed_offset_degrees, 9
            ),
            "computation_library_version": (
                self.computation_library_version
            ),
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "scheme_id": self.scheme_id,
            "provider": self.provider,
            "provider_constant": self.provider_constant,
            "epoch_label": self.epoch_label,
            "epoch_jd": self.epoch_jd,
            "computed_offset_degrees": self.computed_offset_degrees,
            "computation_library_version": self.computation_library_version,
            "choice_hash": self.choice_hash(),
            "admitted": self.admitted,
            "source_copy_hash": self.source_copy_hash,
            "source_locator": self.source_locator,
            "distinction": (
                "the offset is computed and reproducible; selecting this "
                "ayanamsa is a school claim and is not admitted"
            ),
        }


def _choice(
    scheme_id: str, provider_constant: str, offset: float
) -> AyanamsaChoice:
    """Build an unadmitted choice with its recorded J2000 offset."""
    return AyanamsaChoice(
        scheme_id=scheme_id,
        provider=EPHEMERIS_PROVIDER,
        provider_constant=provider_constant,
        epoch_label=REFERENCE_EPOCH_LABEL,
        epoch_jd=REFERENCE_EPOCH_JD,
        computed_offset_degrees=offset,
        computation_library_version=EPHEMERIS_PROVIDER_VERSION,
        admitted=False,
        source_copy_hash="",
        source_locator="",
    )


# The three supported schemes, offsets computed via swisseph at J2000 and
# recorded here; a test recomputes and asserts these match. All unadmitted:
# the offsets are reproducible, the choice among them is not licensed.
LAHIRI = _choice("lahiri", "SIDM_LAHIRI", 23.857092)
RAMAN = _choice("raman", "SIDM_RAMAN", 22.410791)
KRISHNAMURTI = _choice("krishnamurti", "SIDM_KRISHNAMURTI", 23.760240)

AYANAMSA_REGISTRY: tuple[AyanamsaChoice, ...] = (LAHIRI, RAMAN, KRISHNAMURTI)


def admitted_ayanamsa_choices() -> list[AyanamsaChoice]:
    """Return the admitted ayanamsa choices -- currently none."""
    return [choice for choice in AYANAMSA_REGISTRY if choice.admitted]


def require_sidereal_provenance(result: Mapping[str, Any]) -> None:
    """Raise if a sidereal quantity appears without ayanamsa provenance.

    The Vedic data-level laundering rule. A sidereal longitude, nakshatra,
    sign, divisional placement or dasha is a function of the ayanamsa, so a
    result carrying one must name the choice, the ephemeris input and the
    provider version. A result reproducible from the ephemeris alone -- a
    tropical position -- is unaffected.
    """
    carries_sidereal = any(
        key in result for key in SIDEREAL_QUANTITY_KEYS
    )

    if not carries_sidereal:
        return

    for required in (
        "ayanamsa_choice_hash",
        "ephemeris_input_hash",
        "ephemeris_provider_version",
    ):
        if not result.get(required):
            raise AyanamsaError(
                f"a sidereal result was serialized without {required!r}; a "
                "sidereal quantity cannot be presented without naming the "
                "ayanamsa choice that produced it."
            )
