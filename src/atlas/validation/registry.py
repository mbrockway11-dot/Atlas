"""Atlas validation-domain registry.

The registry owns validation-domain discovery and execution.

Atlas services should depend on the registry instead of hard-coding individual
validation domains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from atlas.validation.domains.vedic import VedicValidationDomain
from atlas.validation.base import (
    Confidence,
    ValidationContext,
    ValidationDomain,
    ValidationResult,
    ValidationSignal,
    build_agreement_score,
    summarize_validation_results,
)


VALIDATION_REGISTRY_VERSION = "1.0"


@dataclass
class RegisteredValidationDomain:
    """Registered validation-domain metadata."""

    name: str
    domain: ValidationDomain
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize registry entry."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "version": getattr(self.domain, "version", "unknown"),
            "domain_type": getattr(self.domain, "domain_type", "unknown"),
            "metadata": self.metadata,
        }


class ValidationDomainRegistry:
    """Registry of Atlas validation domains."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._domains: dict[str, RegisteredValidationDomain] = {}

    def register(
        self,
        domain: ValidationDomain,
        *,
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a validation domain."""
        name = getattr(domain, "name", None)

        if not name:
            raise ValueError("Validation domain must define a name.")

        self._domains[name] = RegisteredValidationDomain(
            name=name,
            domain=domain,
            enabled=enabled,
            metadata=metadata or {},
        )

    def unregister(self, name: str) -> None:
        """Remove a validation domain."""
        self._domains.pop(name, None)

    def enable(self, name: str) -> None:
        """Enable a registered validation domain."""
        if name in self._domains:
            self._domains[name].enabled = True

    def disable(self, name: str) -> None:
        """Disable a registered validation domain."""
        if name in self._domains:
            self._domains[name].enabled = False

    def get(self, name: str) -> ValidationDomain | None:
        """Return one validation domain."""
        entry = self._domains.get(name)
        if not entry:
            return None

        return entry.domain

    def names(self, *, enabled_only: bool = True) -> list[str]:
        """Return registered domain names."""
        if enabled_only:
            return [
                name
                for name, entry in self._domains.items()
                if entry.enabled
            ]

        return list(self._domains.keys())

    def entries(self, *, enabled_only: bool = True) -> list[RegisteredValidationDomain]:
        """Return registered domain entries."""
        if enabled_only:
            return [
                entry
                for entry in self._domains.values()
                if entry.enabled
            ]

        return list(self._domains.values())

    def to_dict(self) -> dict[str, Any]:
        """Serialize registry."""
        return {
            "version": VALIDATION_REGISTRY_VERSION,
            "domain_count": len(self._domains),
            "enabled_domain_count": len(self.names(enabled_only=True)),
            "domains": [
                entry.to_dict()
                for entry in self.entries(enabled_only=False)
            ],
        }

    def validate(
        self,
        context: ValidationContext,
        *,
        domains: list[str] | None = None,
    ) -> list[ValidationResult]:
        """Run selected validation domains."""
        selected_names = domains or self.names(enabled_only=True)
        results: list[ValidationResult] = []

        for name in selected_names:
            entry = self._domains.get(name)

            if entry is None:
                results.append(unknown_domain_result(name, context))
                continue

            if not entry.enabled:
                results.append(disabled_domain_result(name, context))
                continue

            try:
                results.append(entry.domain.validate(context))
            except Exception as exc:  # noqa: BLE001
                results.append(exception_domain_result(name, context, exc))

        return results


def unknown_domain_result(
    name: str,
    context: ValidationContext,
) -> ValidationResult:
    """Build result for unknown domain."""
    signal = ValidationSignal(
        signal_type="unknown",
        message=f"Validation domain is not registered: {name}",
        source="validation_registry",
    )

    return ValidationResult(
        domain=name,
        domain_type="unknown_validation_domain",
        version=VALIDATION_REGISTRY_VERSION,
        success=False,
        agreement_signals=[],
        conflict_signals=[],
        unknown_signals=[signal],
        confidence=Confidence.from_score(0.0),
        agreement_score=Confidence.from_score(0.0),
        warnings=[f"Unknown validation domain requested: {name}"],
        errors=[],
        metrics={
            "profile_key": context.profile_key,
            "canonical_claim_count": len(
                context.canonical_summary.get("canonical_claims", [])
            ),
        },
        recommended_followup=[
            f"Register validation domain before requesting it: {name}"
        ],
        interpretation=(
            f"{name} could not be evaluated because it is not registered."
        ),
    )


def disabled_domain_result(
    name: str,
    context: ValidationContext,
) -> ValidationResult:
    """Build result for disabled domain."""
    signal = ValidationSignal(
        signal_type="unknown",
        message=f"Validation domain is disabled: {name}",
        source="validation_registry",
    )

    return ValidationResult(
        domain=name,
        domain_type="disabled_validation_domain",
        version=VALIDATION_REGISTRY_VERSION,
        success=False,
        agreement_signals=[],
        conflict_signals=[],
        unknown_signals=[signal],
        confidence=Confidence.from_score(0.0),
        agreement_score=Confidence.from_score(0.0),
        warnings=[f"Disabled validation domain requested: {name}"],
        errors=[],
        metrics={
            "profile_key": context.profile_key,
            "canonical_claim_count": len(
                context.canonical_summary.get("canonical_claims", [])
            ),
        },
        recommended_followup=[
            f"Enable validation domain before requesting it: {name}"
        ],
        interpretation=(
            f"{name} could not be evaluated because it is disabled."
        ),
    )


def exception_domain_result(
    name: str,
    context: ValidationContext,
    exc: Exception,
) -> ValidationResult:
    """Build result for validation-domain exception."""
    signal = ValidationSignal(
        signal_type="conflict",
        message=f"Validation domain failed during execution: {name}",
        source="validation_registry",
        metadata={"exception": str(exc)},
    )

    return ValidationResult(
        domain=name,
        domain_type="failed_validation_domain",
        version=VALIDATION_REGISTRY_VERSION,
        success=False,
        agreement_signals=[],
        conflict_signals=[signal],
        unknown_signals=[],
        confidence=Confidence.from_score(0.0),
        agreement_score=Confidence.from_score(0.0),
        warnings=[],
        errors=[f"{name} failed: {exc}"],
        metrics={
            "profile_key": context.profile_key,
            "canonical_claim_count": len(
                context.canonical_summary.get("canonical_claims", [])
            ),
        },
        recommended_followup=[
            f"Inspect validation domain failure: {name}"
        ],
        interpretation=(
            f"{name} failed during validation and produced no usable result."
        ),
    )


def build_registry_payload(
    registry: ValidationDomainRegistry,
) -> dict[str, Any]:
    """Build registry payload."""
    return {
        "success": True,
        "version": VALIDATION_REGISTRY_VERSION,
        "errors": [],
        "warnings": [],
        "data": {
            "registry": registry.to_dict(),
        },
        "metrics": {
            "domain_count": len(registry.names(enabled_only=False)),
            "enabled_domain_count": len(registry.names(enabled_only=True)),
        },
    }


DEFAULT_VALIDATION_REGISTRY = ValidationDomainRegistry()
DEFAULT_VALIDATION_REGISTRY.register(
    VedicValidationDomain(),
    metadata={
        "description": "Vedic Behavior validation domain adapter.",
        "status": "active",
    },
)


def get_default_validation_registry() -> ValidationDomainRegistry:
    """Return default validation-domain registry."""
    return DEFAULT_VALIDATION_REGISTRY


def validate_with_registry(
    context: ValidationContext,
    *,
    domains: list[str] | None = None,
    registry: ValidationDomainRegistry | None = None,
) -> dict[str, Any]:
    """Run validation through a registry and return a payload."""
    active_registry = registry or get_default_validation_registry()
    results = active_registry.validate(context, domains=domains)
    summary = summarize_validation_results(results)

    return {
        "success": all(result.success for result in results) if results else False,
        "version": VALIDATION_REGISTRY_VERSION,
        "errors": collect_result_errors(results),
        "warnings": collect_result_warnings(results),
        "data": {
            "results": [result.to_dict() for result in results],
            "summary": summary,
            "registry": active_registry.to_dict(),
        },
        "metrics": {
            "domain_count": summary.get("domain_count", 0),
            "successful_domains": summary.get("successful_domains", 0),
            "failed_domains": summary.get("failed_domains", 0),
            "agreement_signal_count": summary.get("agreement_signal_count", 0),
            "conflict_signal_count": summary.get("conflict_signal_count", 0),
            "unknown_signal_count": summary.get("unknown_signal_count", 0),
            "average_agreement": summary.get("average_agreement", {}),
            "validation_readiness": summary.get("validation_readiness", "unknown"),
        },
    }


def collect_result_errors(results: list[ValidationResult]) -> list[Any]:
    """Collect validation result errors."""
    errors: list[Any] = []

    for result in results:
        for error in result.errors:
            errors.append(
                {
                    "domain": result.domain,
                    "error": error,
                }
            )

    return errors


def collect_result_warnings(results: list[ValidationResult]) -> list[str]:
    """Collect validation result warnings."""
    warnings: list[str] = []

    for result in results:
        for warning in result.warnings:
            text = f"{result.domain}: {warning}"
            if text not in warnings:
                warnings.append(text)

    return warnings


__all__ = [
    "RegisteredValidationDomain",
    "ValidationDomainRegistry",
    "build_registry_payload",
    "get_default_validation_registry",
    "validate_with_registry",
]