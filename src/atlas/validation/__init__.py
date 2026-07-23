"""Atlas Validation Framework v1.

Answers one question at a time, about one model at a time. Experiments are
domain-typed because Atlas is not a single model: identity vectors are
name-derived, temporal/CSS outputs are birth- and date-sensitive, and an
experiment that confuses the two produces a confident number about nothing.
"""

from atlas.validation.models import (
    VALIDATION_CONFIG_SCHEMA,
    ControlSpec,
    ExperimentConfig,
    ExperimentConfigError,
    ExperimentDomain,
    ExperimentKind,
    config_from_dict,
    load_config,
    validate_config,
)

__all__ = [
    "VALIDATION_CONFIG_SCHEMA",
    "ControlSpec",
    "ExperimentConfig",
    "ExperimentConfigError",
    "ExperimentDomain",
    "ExperimentKind",
    "config_from_dict",
    "load_config",
    "validate_config",
]
