"""Population corpus builder.

Builds searchable population indexes from saved profile keys by routing each
profile through the canonical single-profile intelligence service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.fingerprint.builder import StructuralFingerprint
from atlas.population.index import PopulationIndex, build_population_index
from atlas.services.single_profile_intelligence_service import (
    build_single_profile_intelligence_payload,
)


POPULATION_CORPUS_VERSION = "0.1"


@dataclass(frozen=True)
class PopulationCorpusResult:
    """Result of building a population corpus."""

    index: PopulationIndex
    successes: tuple[str, ...]
    failures: dict[str, str]
    warnings: dict[str, list[str]]
    metadata: dict[str, Any]

    @property
    def success_count(self) -> int:
        """Return successful profile count."""
        return len(self.successes)

    @property
    def failure_count(self) -> int:
        """Return failed profile count."""
        return len(self.failures)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe corpus result."""
        return {
            "version": POPULATION_CORPUS_VERSION,
            "index": self.index.to_dict(),
            "successes": list(self.successes),
            "failures": self.failures,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "summary": {
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "index_count": self.index.count,
            },
        }


def build_population_corpus(
    profile_keys: list[str] | tuple[str, ...],
    *,
    evaluation_date: str | None = None,
    forecast_days: int = 7,
    limit: int | None = None,
) -> PopulationCorpusResult:
    """Build a population index from profile keys."""
    selected_keys = tuple(profile_keys[:limit] if limit is not None else profile_keys)

    fingerprints: list[StructuralFingerprint] = []
    successes: list[str] = []
    failures: dict[str, str] = {}
    warnings: dict[str, list[str]] = {}

    for profile_key in selected_keys:
        try:
            payload = build_single_profile_intelligence_payload(
                profile_key,
                evaluation_date=evaluation_date,
                forecast_days=forecast_days,
            )

            if not payload.get("success"):
                failures[profile_key] = "; ".join(payload.get("errors", [])) or "unknown failure"
                continue

            fingerprint_payload = payload.get("structural_fingerprint", {})
            if not fingerprint_payload:
                failures[profile_key] = "missing structural fingerprint"
                continue

            fingerprints.append(
                structural_fingerprint_from_payload(fingerprint_payload)
            )
            successes.append(profile_key)

            payload_warnings = payload.get("warnings", [])
            if payload_warnings:
                warnings[profile_key] = list(payload_warnings)

        except Exception as exc:  # noqa: BLE001
            failures[profile_key] = str(exc)

    index = build_population_index(fingerprints)

    return PopulationCorpusResult(
        index=index,
        successes=tuple(successes),
        failures=failures,
        warnings=warnings,
        metadata={
            "corpus_version": POPULATION_CORPUS_VERSION,
            "requested_count": len(selected_keys),
            "evaluation_date": evaluation_date,
            "forecast_days": forecast_days,
        },
    )


def structural_fingerprint_from_payload(
    payload: dict[str, Any],
) -> StructuralFingerprint:
    """Rehydrate StructuralFingerprint from payload dictionary."""
    return StructuralFingerprint(
        version=str(payload["version"]),
        profile_key=str(payload["profile_key"]),
        vector={
            key: float(value)
            for key, value in payload.get("vector", {}).items()
        },
        labels=dict(payload.get("labels", {})),
        structural_hash=str(payload["structural_hash"]),
        metadata=dict(payload.get("metadata", {})),
    )
