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


# 1E-V-SOURCE-A. The Lahiri (Chitra-paksa) ayanamsa is licensed by the
# Government of India's own standard: the Calendar Reform Committee fixed the
# sidereal zero-point, and N.C. Lahiri -- the committee's Secretary -- gives it
# its name. The copy hash is the Internet Archive page-image archive verified
# against; the locator names the committee's own recommendation, distinguished
# from the correspondents' letters elsewhere in the report.
LAHIRI_SOURCE_COPY_HASH = "a4a6e0753677eba7be774200a1cd0c85460b0252"
LAHIRI_SOURCE_LOCATOR = (
    "Report of the Calendar Reform Committee, Government of India, Council of "
    "Scientific and Industrial Research, New Delhi, 1955; Final "
    "Recommendations of the Committee, 'Recommendations for Religious "
    "Calendar', printed p. 7. Item (5): solar months 'start 23 deg 15' ahead "
    "of the vernal equinoctial point'. Item (7): 'we have adopted a variable "
    "ayanamsa ... The value of this ayanamsa would amount to 23 deg 15' 0\" on "
    "21st March, 1956. Thereafter it would gradually increase ... about "
    "50\".27' per year -- the Chitra-paksa zero-point, 180 deg from Spica "
    "(Citra). Verified against the page image (IA "
    "calendar_reform_comittee_report leaf n18) and OCR; this is the "
    "committee's own recommendation, not a correspondent's letter. Construct "
    "equivalence: Swiss Ephemeris SIDM_LAHIRI implements this official Indian "
    "ayanamsa, its J2000 offset (23.857092 deg) being the 1956 value advanced "
    "by precession."
)


# The three supported schemes, offsets computed via swisseph at J2000 and
# recorded here; a test recomputes and asserts these match. Lahiri is admitted
# (1E-V-SOURCE-A) against the Government of India standard; Raman and
# Krishnamurti remain unadmitted -- their offsets are reproducible, but no
# source licenses choosing them here.
LAHIRI = AyanamsaChoice(
    scheme_id="lahiri",
    provider=EPHEMERIS_PROVIDER,
    provider_constant="SIDM_LAHIRI",
    epoch_label=REFERENCE_EPOCH_LABEL,
    epoch_jd=REFERENCE_EPOCH_JD,
    computed_offset_degrees=23.857092,
    computation_library_version=EPHEMERIS_PROVIDER_VERSION,
    admitted=True,
    source_copy_hash=LAHIRI_SOURCE_COPY_HASH,
    source_locator=LAHIRI_SOURCE_LOCATOR,
)
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
