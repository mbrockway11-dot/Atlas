
"""Autonomous prediction baseline models."""

from __future__ import annotations

from typing import Any


DEFAULT_TARGETS = [
    "dynamics.prediction.recovery_probability",
    "dynamics.prediction.perturbation_sensitivity",
    "dynamics.dynamic_profile.recurrence",
]


def build_baseline_model(
    train_records: list[dict[str, Any]],
    *,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    """Build simple mean baseline prediction model."""
    selected_targets = targets or DEFAULT_TARGETS
    target_means = {}

    for target in selected_targets:
        values = []

        for record in train_records:
            value = read_path(record, target)
            try:
                values.append(float(value))
            except Exception:
                pass

        target_means[target] = round(sum(values) / len(values), 6) if values else 0.0

    return {
        "success": True,
        "model_type": "mean_baseline",
        "train_count": len(train_records),
        "targets": selected_targets,
        "target_means": target_means,
    }


def predict_holdout(
    model: dict[str, Any],
    holdout_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Predict target values for holdout records."""
    predictions = []

    for record in holdout_records:
        profile_key = record.get("profile_key")

        for target in model.get("targets", []) or []:
            predicted = model.get("target_means", {}).get(target, 0.0)
            actual_raw = read_path(record, target)

            try:
                actual = float(actual_raw)
            except Exception:
                actual = None

            predictions.append(
                {
                    "profile_key": profile_key,
                    "target": target,
                    "predicted": predicted,
                    "actual": actual,
                    "absolute_error": abs(predicted - actual) if actual is not None else None,
                }
            )

    return predictions


def read_path(source: dict[str, Any], path: str) -> Any:
    """Read dotted path."""
    value: Any = source

    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)

    return value
