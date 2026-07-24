"""Layered bibliographic identity: work, manifestation, source copy.

"Edition" is too coarse for provenance. A passage locator belongs to a
particular *copy* -- two scans catalogued under one work can differ in front
matter, pagination, OCR quality, omitted pages, printing date and publisher
statement. So identity is resolved at four levels, and each carries its own
verdict::

    Work           Jordan, "Numerology: The Romance in Your Name"
    Edition stmt   "first paperback" / "New Ed" / other catalog wording
    Manifestation  publisher, date, ISBN/OCLC, pagination, format
    Source copy    scan id, file hash, scan-page -> printed-page mapping

The distinction is load-bearing. A work can be verified to exist while its
manifestation and pagination remain unresolved -- which is exactly Balliett's
state -- and collapsing those into one "unconfirmed" verdict throws away the
part that *is* settled.

Catalog facts are also kept apart from copy-verified facts. A catalog
assertion, however many catalogs repeat it, is not a title page. Conflicts
between catalogs are never resolved by choosing one as authoritative; they are
resolved from the copy eventually transcribed, or they stay unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Mapping

from atlas.validation.denotation.numerology_tradition import SourceRole


BIBLIOGRAPHY_SCHEMA = "atlas.validation.denotation.numerology-biblio.v1"


class SourceType(str, Enum):
    """How close a source sits to the tradition it reports.

    A property of the printing, not of a sentence transcribed from it.
    """

    PRIMARY = "primary"
    TRADITIONAL_COMMENTARY = "traditional_commentary"
    MODERN_COMMENTARY = "modern_commentary"
    SECONDARY_SYNTHESIS = "secondary_synthesis"


class AuthorityScope(str, Enum):
    """How far a manifestation's authority is claimed to reach."""

    TRADITION_WIDE = "tradition_wide"
    SCHOOL_SPECIFIC = "school_specific"
    AUTHOR_SPECIFIC = "author_specific"


class IdentityStatus(str, Enum):
    """How settled one level of bibliographic identity is."""

    VERIFIED = "verified"
    UNRESOLVED = "unresolved"
    DISCREPANT = "discrepant"


class ProvenanceLevel(str, Enum):
    """How a bibliographic fact came to be believed.

    Ordered by strength. Only the copy-level entries involve looking at the
    physical text; the first two are catalog claims, and repeating a claim
    across catalogs does not turn it into an inspection.
    """

    CATALOG_ASSERTED = "catalog_asserted"
    CROSS_CATALOG_CORRELATED = "cross_catalog_correlated"
    COPY_TITLE_PAGE_VERIFIED = "copy_title_page_verified"
    COPY_COPYRIGHT_PAGE_VERIFIED = "copy_copyright_page_verified"
    COPY_PAGINATION_VERIFIED = "copy_pagination_verified"


# The levels a manifestation must reach before any passage transcribed from it
# may license a denotation. All three are copy-level: a citation whose page
# numbers were never checked against the printed page cannot be reproduced.
REQUIRED_FOR_TRANSCRIPTION: frozenset[ProvenanceLevel] = frozenset(
    {
        ProvenanceLevel.COPY_TITLE_PAGE_VERIFIED,
        ProvenanceLevel.COPY_COPYRIGHT_PAGE_VERIFIED,
        ProvenanceLevel.COPY_PAGINATION_VERIFIED,
    }
)


class BibliographyError(ValueError):
    """A bibliographic record was constructed invalidly."""


@dataclass(frozen=True, slots=True)
class Work:
    """An abstract work, independent of any printing."""

    work_id: str
    author: str
    title: str
    work_identity: IdentityStatus
    identity_note: str = ""

    def __post_init__(self) -> None:
        if not (self.work_id and self.author and self.title):
            raise BibliographyError(
                "a work needs an id, an author and a title."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "work_id": self.work_id,
            "author": self.author,
            "title": self.title,
            "work_identity": self.work_identity.value,
            "identity_note": self.identity_note,
        }


@dataclass(frozen=True, slots=True)
class Manifestation:
    """One printing of a work: publisher, date, identifiers, pagination."""

    manifestation_id: str
    work_id: str
    edition_statement: str
    publisher: str
    publication_year: int | None
    copyright_year: int | None
    isbn: str
    oclc: str
    pagination: str
    fmt: str
    role: SourceRole
    source_type: SourceType
    authority_scope: AuthorityScope
    edition_identity: IdentityStatus
    pagination_identity: IdentityStatus
    provenance_levels: frozenset[ProvenanceLevel] = frozenset()
    identity_note: str = ""

    def __post_init__(self) -> None:
        if not (self.manifestation_id and self.work_id):
            raise BibliographyError(
                "a manifestation needs an id and a work id."
            )

    @property
    def copy_verified(self) -> bool:
        """Return whether the copy-level checks have all been made."""
        return REQUIRED_FOR_TRANSCRIPTION <= self.provenance_levels

    @property
    def transcription_eligible(self) -> bool:
        """Return whether passages from this manifestation may be admitted.

        Requires both settled identity and copy-level verification. A
        manifestation whose pagination is unresolved cannot anchor a page
        locator, however confident the catalog is about the rest.
        """
        return (
            self.copy_verified
            and self.edition_identity is IdentityStatus.VERIFIED
            and self.pagination_identity is IdentityStatus.VERIFIED
        )

    def blocking_reasons(self) -> list[str]:
        """Return why this manifestation is not transcription-eligible."""
        reasons: list[str] = []

        missing = sorted(
            level.value
            for level in REQUIRED_FOR_TRANSCRIPTION - self.provenance_levels
        )

        if missing:
            reasons.append(f"missing copy verification: {', '.join(missing)}")

        if self.edition_identity is not IdentityStatus.VERIFIED:
            reasons.append(
                f"edition identity {self.edition_identity.value}"
            )

        if self.pagination_identity is not IdentityStatus.VERIFIED:
            reasons.append(
                f"pagination identity {self.pagination_identity.value}"
            )

        return reasons

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "manifestation_id": self.manifestation_id,
            "work_id": self.work_id,
            "edition_statement": self.edition_statement,
            "publisher": self.publisher,
            "publication_year": self.publication_year,
            "copyright_year": self.copyright_year,
            "isbn": self.isbn,
            "oclc": self.oclc,
            "pagination": self.pagination,
            "format": self.fmt,
            "role": self.role.value,
            "source_type": self.source_type.value,
            "authority_scope": self.authority_scope.value,
            "edition_identity": self.edition_identity.value,
            "pagination_identity": self.pagination_identity.value,
            "provenance_levels": sorted(
                level.value for level in self.provenance_levels
            ),
            "copy_verified": self.copy_verified,
            "transcription_eligible": self.transcription_eligible,
            "blocking_reasons": self.blocking_reasons(),
            "identity_note": self.identity_note,
        }


@dataclass(frozen=True, slots=True)
class SourceCopy:
    """A specific scan or physical copy a passage was transcribed from.

    The page map is what makes a citation reproducible: a scan's own page
    numbering rarely matches the printed page, and a locator that conflates
    them cannot be checked by anyone holding a different scan.
    """

    copy_id: str
    manifestation_id: str
    scan_identifier: str
    file_hash: str
    # scan page -> printed page, as read off the page images.
    page_map: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (self.copy_id and self.manifestation_id):
            raise BibliographyError(
                "a source copy needs an id and a manifestation id."
            )

        if not self.file_hash:
            raise BibliographyError(
                "a source copy needs a file hash; without it a later "
                "transcription cannot be shown to come from the same text."
            )

    def printed_page_for(self, scan_page: str) -> str | None:
        """Return the printed page for a scan page, if mapped."""
        return self.page_map.get(scan_page)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "copy_id": self.copy_id,
            "manifestation_id": self.manifestation_id,
            "scan_identifier": self.scan_identifier,
            "file_hash": self.file_hash,
            "page_map_entries": len(self.page_map),
        }


def excerpt_hash(text: str) -> str:
    """Return a stable hash of transcribed text.

    Normalizes whitespace only. Two transcribers who disagree about line
    breaks agree here; two who disagree about a word do not, which is the
    distinction double transcription exists to make.
    """
    normalized = " ".join(text.split())

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
