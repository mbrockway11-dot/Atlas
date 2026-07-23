"""Residual similarity: score minus what name structure alone predicts.

The baseline established that name morphology drives a large share of
similarity. A residual score answers the question a raw score cannot:

    is this pair similar *beyond* what two names of this shape would score
    anyway?

The model is deliberately a plain linear regression on interpretable
structural terms. Something more flexible would fit better and explain less,
and the purpose here is attribution, not prediction.

This is explicitly experimental and does not replace the canonical score.
Reports carry raw score, global percentile, matched percentile, residual, and
residual percentile side by side, because collapsing them would hide exactly
the distinction the residual exists to expose.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np


RESIDUAL_MODEL_SCHEMA = "atlas.validation.residual-model.v1"

FEATURE_NAMES: tuple[str, ...] = (
    "intercept",
    "abs_length_difference",
    "abs_token_difference",
    "total_length",
    "min_length",
    "script_match",
)


def build_design_matrix(
    *,
    char_lengths: np.ndarray,
    token_counts: np.ndarray,
    is_ascii: np.ndarray,
    pair_indices: np.ndarray,
) -> np.ndarray:
    """Return the structural design matrix for a set of pairs."""
    left = pair_indices[:, 0]
    right = pair_indices[:, 1]

    lengths_left = char_lengths[left].astype(np.float64)
    lengths_right = char_lengths[right].astype(np.float64)
    tokens_left = token_counts[left].astype(np.float64)
    tokens_right = token_counts[right].astype(np.float64)

    return np.column_stack(
        (
            np.ones(pair_indices.shape[0], dtype=np.float64),
            np.abs(lengths_left - lengths_right),
            np.abs(tokens_left - tokens_right),
            lengths_left + lengths_right,
            np.minimum(lengths_left, lengths_right),
            (is_ascii[left] == is_ascii[right]).astype(np.float64),
        )
    )


@dataclass(frozen=True, slots=True)
class ResidualModel:
    """A fitted structural model of expected similarity."""

    schema_version: str
    feature_names: tuple[str, ...]
    coefficients: tuple[float, ...]
    r_squared: float
    residual_mean: float
    residual_stddev: float
    sample_size: int

    def predict(self, design: np.ndarray) -> np.ndarray:
        """Return expected similarity for each row of a design matrix."""
        return design @ np.asarray(self.coefficients, dtype=np.float64)

    def residuals(
        self,
        *,
        scores: np.ndarray,
        design: np.ndarray,
    ) -> np.ndarray:
        """Return observed minus expected similarity."""
        return np.asarray(scores, dtype=np.float64) - self.predict(design)

    def standardized_residuals(
        self,
        *,
        scores: np.ndarray,
        design: np.ndarray,
    ) -> np.ndarray:
        """Return residuals in units of residual standard deviation."""
        raw = self.residuals(scores=scores, design=design)

        if self.residual_stddev <= 0:
            return raw

        return raw / self.residual_stddev

    def coefficient_table(self) -> list[dict[str, Any]]:
        """Return coefficients paired with their feature names."""
        return [
            {"feature": name, "coefficient": float(value)}
            for name, value in zip(self.feature_names, self.coefficients)
        ]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema_version": self.schema_version,
            "feature_names": list(self.feature_names),
            "coefficients": list(self.coefficients),
            "coefficient_table": self.coefficient_table(),
            "r_squared": self.r_squared,
            "residual_mean": self.residual_mean,
            "residual_stddev": self.residual_stddev,
            "sample_size": self.sample_size,
            "note": (
                "Experimental. Does not replace the canonical similarity "
                "score; reports must show both."
            ),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ResidualModel":
        """Reconstruct and validate from decoded JSON."""
        schema_version = str(payload["schema_version"])

        if schema_version != RESIDUAL_MODEL_SCHEMA:
            raise ValueError(
                f"Unsupported residual model schema: {schema_version!r}"
            )

        return cls(
            schema_version=schema_version,
            feature_names=tuple(
                str(name) for name in payload["feature_names"]
            ),
            coefficients=tuple(
                float(value) for value in payload["coefficients"]
            ),
            r_squared=float(payload["r_squared"]),
            residual_mean=float(payload["residual_mean"]),
            residual_stddev=float(payload["residual_stddev"]),
            sample_size=int(payload["sample_size"]),
        )


def fit_residual_model(
    *,
    scores: np.ndarray,
    design: np.ndarray,
) -> ResidualModel:
    """Fit expected similarity from structural features by least squares."""
    values = np.asarray(scores, dtype=np.float64)

    coefficients, *_ = np.linalg.lstsq(design, values, rcond=None)

    predicted = design @ coefficients
    residuals = values - predicted

    total_variance = float(((values - values.mean()) ** 2).sum())
    residual_variance = float((residuals**2).sum())

    r_squared = (
        1.0 - residual_variance / total_variance
        if total_variance > 0
        else 0.0
    )

    return ResidualModel(
        schema_version=RESIDUAL_MODEL_SCHEMA,
        feature_names=FEATURE_NAMES,
        coefficients=tuple(float(value) for value in coefficients),
        r_squared=float(r_squared),
        residual_mean=float(residuals.mean()),
        residual_stddev=float(residuals.std()),
        sample_size=int(values.size),
    )


def partial_correlation(
    *,
    target: np.ndarray,
    predictor: np.ndarray,
    controls: np.ndarray,
) -> float:
    """Return the correlation of target and predictor, controlling for others.

    Both variables are regressed on the controls and their residuals
    correlated -- the standard construction, written out because it is short
    enough to audit and scipy is not available.
    """
    design = np.column_stack(
        (np.ones(controls.shape[0], dtype=np.float64), controls)
    )

    def residual(values: np.ndarray) -> np.ndarray:
        coefficients, *_ = np.linalg.lstsq(design, values, rcond=None)
        return values - design @ coefficients

    target_residual = residual(np.asarray(target, dtype=np.float64))
    predictor_residual = residual(np.asarray(predictor, dtype=np.float64))

    if target_residual.std() == 0 or predictor_residual.std() == 0:
        return 0.0

    return float(np.corrcoef(target_residual, predictor_residual)[0, 1])


def spearman_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Return the Spearman rank correlation.

    Computed as Pearson on ranks, with ties averaged. Reported alongside
    Pearson because a monotone-but-nonlinear relationship would otherwise be
    understated.
    """

    def ranks(values: np.ndarray) -> np.ndarray:
        order = np.argsort(values, kind="mergesort")
        result = np.empty(values.size, dtype=np.float64)
        result[order] = np.arange(1, values.size + 1, dtype=np.float64)

        # Average ranks within tied runs.
        sorted_values = values[order]
        start = 0

        for index in range(1, values.size + 1):
            if index == values.size or sorted_values[index] != sorted_values[start]:
                if index - start > 1:
                    result[order[start:index]] = result[
                        order[start:index]
                    ].mean()
                start = index

        return result

    a = ranks(np.asarray(x, dtype=np.float64))
    b = ranks(np.asarray(y, dtype=np.float64))

    if a.std() == 0 or b.std() == 0:
        return 0.0

    return float(np.corrcoef(a, b)[0, 1])


def save_residual_model(model: ResidualModel, path: Path) -> Path:
    """Write the model atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(model.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)

    return path


def load_residual_model(path: Path) -> ResidualModel:
    """Load and validate a residual model."""
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Residual model root must be an object.")

    return ResidualModel.from_dict(payload)
