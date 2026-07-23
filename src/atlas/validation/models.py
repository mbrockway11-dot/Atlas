"""Experiment configuration and domain typing for Atlas validation.

Atlas is not one model. Identity vectors are derived from the name alone;
temporal/CSS outputs are the birth- and date-sensitive part. Proving that
separation is what made the *domain* field necessary: an experiment that
permutes birth dates and measures identity-vector similarity is not a weak
control, it is a no-op, because birth data provably never enters those
vectors.

So the domain is declared up front and the runner refuses combinations that
cannot answer their own question. The mistake is caught at configuration
time, before a run produces a confidently meaningless number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


VALIDATION_CONFIG_SCHEMA = "atlas.validation.experiment-config.v1"


class ExperimentDomain(str, Enum):
    """Which part of Atlas an experiment interrogates."""

    IDENTITY_VECTOR = "identity_vector"
    TEMPORAL_CSS = "temporal_css"
    RELATIONSHIP = "relationship"
    COMBINED = "combined"


class ExperimentKind(str, Enum):
    """The shape of the experiment, which decides what the runner does."""

    ALL_PAIRS_BASELINE = "all_pairs_baseline"
    COHORT_COMPARISON = "cohort_comparison"
    PERTURBATION = "perturbation"
    INVARIANCE = "invariance"
    COLLISION_SCAN = "collision_scan"


# Inputs that only make sense for some domains. Keyed by the config field
# that carries them; the value is the set of domains allowed to use it.
_DOMAIN_ONLY_INPUTS: dict[str, set[ExperimentDomain]] = {
    "birth_permutation": {
        ExperimentDomain.TEMPORAL_CSS,
        ExperimentDomain.COMBINED,
    },
    "evaluation_date": {
        ExperimentDomain.TEMPORAL_CSS,
        ExperimentDomain.COMBINED,
    },
    "name_perturbation": {
        ExperimentDomain.IDENTITY_VECTOR,
        ExperimentDomain.COMBINED,
    },
}

VALID_NORMALIZATION_MODES = frozenset(
    {"raw", "percentile", "minmax", "zscore"}
)
VALID_METRICS = frozenset({"cosine_similarity"})


class ExperimentConfigError(ValueError):
    """A configuration that cannot answer the question it poses."""


@dataclass(frozen=True, slots=True)
class ControlSpec:
    """How a control cohort is drawn."""

    strategy: str = "matched_random"
    match_on: tuple[str, ...] = ()
    ratio: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "strategy": self.strategy,
            "match_on": list(self.match_on),
            "ratio": self.ratio,
        }


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    """One reproducible experiment definition."""

    experiment_id: str
    domain: ExperimentDomain
    kind: ExperimentKind
    hypothesis: str
    normalization_mode: str = "raw"
    metric: str = "cosine_similarity"
    random_seed: int = 0
    bootstrap_iterations: int = 0
    permutation_iterations: int = 0
    dataset_path: str | None = None
    positive_cohort: dict[str, Any] = field(default_factory=dict)
    control: ControlSpec = field(default_factory=ControlSpec)
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema_version": VALIDATION_CONFIG_SCHEMA,
            "experiment_id": self.experiment_id,
            "domain": self.domain.value,
            "kind": self.kind.value,
            "hypothesis": self.hypothesis,
            "normalization_mode": self.normalization_mode,
            "metric": self.metric,
            "random_seed": self.random_seed,
            "bootstrap_iterations": self.bootstrap_iterations,
            "permutation_iterations": self.permutation_iterations,
            "dataset_path": self.dataset_path,
            "positive_cohort": dict(self.positive_cohort),
            "control": self.control.to_dict(),
            "options": dict(self.options),
        }


def validate_config(config: ExperimentConfig) -> None:
    """Raise when a configuration cannot answer its own question.

    The checks are deliberately blunt. Each one corresponds to a way of
    producing a number that looks like a result but is not one.
    """
    if not config.experiment_id.strip():
        raise ExperimentConfigError("experiment_id must not be empty.")

    if not config.hypothesis.strip():
        raise ExperimentConfigError(
            "hypothesis must be stated before the experiment runs; declaring "
            "it afterwards is not a hypothesis."
        )

    if config.normalization_mode not in VALID_NORMALIZATION_MODES:
        raise ExperimentConfigError(
            f"Unknown normalization_mode {config.normalization_mode!r}. "
            f"Expected one of {sorted(VALID_NORMALIZATION_MODES)}."
        )

    if config.metric not in VALID_METRICS:
        raise ExperimentConfigError(
            f"Unknown metric {config.metric!r}. "
            f"Expected one of {sorted(VALID_METRICS)}."
        )

    for option, allowed_domains in _DOMAIN_ONLY_INPUTS.items():
        if option not in config.options:
            continue

        if config.domain not in allowed_domains:
            raise ExperimentConfigError(
                f"Experiment {config.experiment_id!r} is domain "
                f"{config.domain.value!r} but supplies {option!r}, which "
                f"only applies to "
                f"{sorted(d.value for d in allowed_domains)}. "
                + _explain(option, config.domain)
            )

    if (
        config.domain is ExperimentDomain.TEMPORAL_CSS
        and "evaluation_date" not in config.options
    ):
        raise ExperimentConfigError(
            "temporal_css experiments require an explicit evaluation_date. "
            "Without one the result would depend on when it was run."
        )

    if config.kind is ExperimentKind.COHORT_COMPARISON and not (
        config.dataset_path or config.positive_cohort
    ):
        raise ExperimentConfigError(
            "cohort_comparison requires a dataset_path or positive_cohort."
        )

    if config.bootstrap_iterations < 0 or config.permutation_iterations < 0:
        raise ExperimentConfigError("Iteration counts cannot be negative.")


def _explain(option: str, domain: ExperimentDomain) -> str:
    """Return the reason a domain/input pairing is rejected."""
    if option == "birth_permutation" and domain is (
        ExperimentDomain.IDENTITY_VECTOR
    ):
        return (
            "Identity vectors are derived from the name alone -- birth data "
            "never enters them -- so permuting birth data would measure "
            "exactly zero by construction, not a null result. Measure a "
            "temporal_css outcome instead."
        )

    if option == "name_perturbation" and domain is (
        ExperimentDomain.TEMPORAL_CSS
    ):
        return (
            "Temporal/CSS outputs derive from birth and evaluation dates, "
            "not from name structure."
        )

    return ""


def config_from_dict(payload: dict[str, Any]) -> ExperimentConfig:
    """Build and validate a config from a decoded YAML/JSON mapping."""
    try:
        domain = ExperimentDomain(str(payload["domain"]))
    except KeyError:
        raise ExperimentConfigError(
            "Every experiment must declare a domain: "
            f"{sorted(d.value for d in ExperimentDomain)}."
        ) from None
    except ValueError:
        raise ExperimentConfigError(
            f"Unknown domain {payload.get('domain')!r}. Expected one of "
            f"{sorted(d.value for d in ExperimentDomain)}."
        ) from None

    try:
        kind = ExperimentKind(str(payload["kind"]))
    except KeyError:
        raise ExperimentConfigError("Every experiment must declare a kind.") from None
    except ValueError:
        raise ExperimentConfigError(
            f"Unknown kind {payload.get('kind')!r}. Expected one of "
            f"{sorted(k.value for k in ExperimentKind)}."
        ) from None

    dataset = payload.get("dataset") or {}
    control = payload.get("control") or {}

    config = ExperimentConfig(
        experiment_id=str(payload.get("experiment_id", "")),
        domain=domain,
        kind=kind,
        hypothesis=str(payload.get("hypothesis", "")),
        normalization_mode=str(payload.get("normalization_mode", "raw")),
        metric=str(payload.get("metric", "cosine_similarity")),
        random_seed=int(payload.get("random_seed", 0)),
        bootstrap_iterations=int(payload.get("bootstrap_iterations", 0)),
        permutation_iterations=int(payload.get("permutation_iterations", 0)),
        dataset_path=(
            str(dataset["path"]) if isinstance(dataset, dict) and dataset.get("path")
            else None
        ),
        positive_cohort=dict(payload.get("positive_cohort") or {}),
        control=ControlSpec(
            strategy=str(control.get("strategy", "matched_random")),
            match_on=tuple(str(m) for m in control.get("match_on", ())),
            ratio=int(control.get("ratio", 1)),
        ),
        options=dict(payload.get("options") or {}),
    )

    validate_config(config)

    return config


def load_config(path: str | Path) -> ExperimentConfig:
    """Load and validate an experiment config from YAML or JSON."""
    import json

    import yaml

    text = Path(path).read_text(encoding="utf-8")

    payload = (
        json.loads(text)
        if str(path).endswith(".json")
        else yaml.safe_load(text)
    )

    if not isinstance(payload, dict):
        raise ExperimentConfigError(
            f"Experiment config must be a mapping: {path}"
        )

    return config_from_dict(payload)
