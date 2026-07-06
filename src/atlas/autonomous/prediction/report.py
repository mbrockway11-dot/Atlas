
"""Autonomous Prediction Engine report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.prediction.benchmark import run_prediction_benchmark
from atlas.autonomous.prediction.evaluator import evaluate_prediction_readiness


PREDICTION_VERSION = "1.0.0"


def build_prediction_challenge_report(
    records: list[dict[str, Any]],
    *,
    holdout_ratio: float = 0.20,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    """Build prediction challenge report."""
    readiness = evaluate_prediction_readiness(records)

    if not readiness.get("can_run_prediction"):
        return {
            "success": False,
            "version": PREDICTION_VERSION,
            "readiness": readiness,
            "summary": "Prediction challenge requires at least 20 records.",
        }

    benchmark = run_prediction_benchmark(
        records,
        holdout_ratio=holdout_ratio,
        targets=targets,
    )

    return {
        "success": True,
        "version": PREDICTION_VERSION,
        "readiness": readiness,
        "benchmark": benchmark,
        "summary": benchmark.get("summary", ""),
    }
