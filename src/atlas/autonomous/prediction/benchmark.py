
"""Prediction benchmark runner."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.prediction.predictor import build_baseline_model, predict_holdout
from atlas.autonomous.prediction.scoring import score_predictions
from atlas.autonomous.prediction.splitter import split_records


def run_prediction_benchmark(
    records: list[dict[str, Any]],
    *,
    holdout_ratio: float = 0.20,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    """Run prediction benchmark."""
    split = split_records(records, holdout_ratio=holdout_ratio)

    model = build_baseline_model(
        split.get("train", []),
        targets=targets,
    )

    predictions = predict_holdout(
        model,
        split.get("holdout", []),
    )

    scores = score_predictions(predictions)

    return {
        "success": True,
        "split": split,
        "model": model,
        "predictions": predictions,
        "scores": scores,
        "summary": build_summary(split, scores),
    }


def build_summary(split: dict[str, Any], scores: dict[str, Any]) -> str:
    """Build benchmark summary."""
    return (
        f"Prediction benchmark trained on {split.get('train_count', 0)} record(s) "
        f"and evaluated {split.get('holdout_count', 0)} holdout record(s). "
        f"Mean absolute error: {scores.get('mean_absolute_error')} "
        f"({scores.get('accuracy_label')})."
    )
