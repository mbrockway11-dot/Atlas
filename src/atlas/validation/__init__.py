"""Atlas validation-domain framework."""

from atlas.validation.base import (
    Confidence,
    ValidationContext,
    ValidationDomain,
    ValidationResult,
    ValidationSignal,
    build_agreement_score,
    summarize_validation_results,
)
from atlas.validation.registry import (
    RegisteredValidationDomain,
    ValidationDomainRegistry,
    build_registry_payload,
    get_default_validation_registry,
    validate_with_registry,
)

__all__ = [
    "Confidence",
    "ValidationContext",
    "ValidationDomain",
    "ValidationResult",
    "ValidationSignal",
    "build_agreement_score",
    "summarize_validation_results",
    "RegisteredValidationDomain",
    "ValidationDomainRegistry",
    "build_registry_payload",
    "get_default_validation_registry",
    "validate_with_registry",
]