
"""Portfolio confidence scoring for Investment Intelligence v1."""

from __future__ import annotations

import math

import pandas as pd


def build_confidence_assessment(inputs: dict) -> dict:
    ensemble_score = ensemble_confidence(
        inputs.get("alpha_ensemble_scores")
    )

    learning = inputs.get("learning", {}) or {}
    learning_confidence = finite(
        learning.get("learning_confidence"),
        0.0,
    )

    accounting_score = accounting_confidence(
        inputs.get("broker_ledger", {}) or {}
    )

    risk_score = risk_confidence(
        inputs.get("risk", {}) or {}
    )

    execution_score = execution_confidence(
        inputs.get("execution_engine", {}) or {},
        inputs.get("safety", {}) or {},
    )

    data_score = data_confidence(
        inputs.get("performance", {}) or {},
        learning,
    )

    components = {
        "ensemble": {
            "score": ensemble_score,
            "weight": 0.25,
        },
        "learning": {
            "score": learning_confidence,
            "weight": 0.20,
        },
        "accounting": {
            "score": accounting_score,
            "weight": 0.20,
        },
        "risk": {
            "score": risk_score,
            "weight": 0.15,
        },
        "execution": {
            "score": execution_score,
            "weight": 0.10,
        },
        "data": {
            "score": data_score,
            "weight": 0.10,
        },
    }

    overall = sum(
        block["score"] * block["weight"]
        for block in components.values()
    )

    overall = round(max(0.0, min(1.0, overall)), 6)

    limitations = []

    regime = (
        learning.get("learning_regime", {}) or {}
    ).get("learning_regime")

    if regime == "insufficient_history":
        limitations.append(
            "Learning confidence is constrained by insufficient "
            "broker-authoritative MTM history."
        )

    if ensemble_source_count(inputs) <= 1:
        limitations.append(
            "Alpha Ensemble currently has limited independent "
            "signal-source diversity."
        )

    return {
        "overall_confidence": overall,
        "confidence_label": confidence_label(overall),
        "components": components,
        "limitations": limitations,
        "source": "investment_intelligence_v1",
    }


def ensemble_confidence(scores: pd.DataFrame) -> float:
    if (
        scores is None
        or scores.empty
        or "ensemble_score" not in scores.columns
    ):
        return 0.0

    values = pd.to_numeric(
        scores["ensemble_score"],
        errors="coerce",
    ).dropna()

    if values.empty:
        return 0.0

    return round(
        max(0.0, min(1.0, float(values.mean()))),
        6,
    )


def accounting_confidence(ledger: dict) -> float:
    reconciliation = ledger.get("reconciliation", {}) or {}

    if reconciliation.get("balanced") is True:
        return 1.0

    return 0.0


def risk_confidence(risk: dict) -> float:
    aggregate = risk.get("aggregate", {}) or {}

    raw_risk = finite(
        aggregate.get("aggregate_risk_score"),
        1.0,
    )

    return round(max(0.0, min(1.0, 1.0 - raw_risk)), 6)


def execution_confidence(
    execution: dict,
    safety: dict,
) -> float:
    safety_status = str(
        safety.get("status") or ""
    ).upper()

    if safety_status == "REJECTED":
        return 0.25

    if safety_status == "APPROVED_WITH_WARNINGS":
        safety_component = 0.75
    elif safety_status == "APPROVED":
        safety_component = 1.0
    else:
        safety_component = 0.50

    if execution.get("success") is False:
        return 0.0

    return safety_component


def data_confidence(
    performance: dict,
    learning: dict,
) -> float:
    metrics = performance.get("equity_metrics", {}) or {}

    observations = int(
        finite(metrics.get("return_observations"), 0.0)
    )

    regime = (
        learning.get("learning_regime", {}) or {}
    ).get("learning_regime")

    if regime == "insufficient_history":
        return min(0.40, observations / 50.0)

    return min(1.0, observations / 100.0)


def ensemble_source_count(inputs: dict) -> int:
    report = inputs.get("alpha_ensemble", {}) or {}
    signals = report.get("signals", []) or []

    return len({
        str(row.get("signal_source"))
        for row in signals
        if isinstance(row, dict)
        and row.get("signal_source")
    })


def confidence_label(score: float) -> str:
    if score >= 0.80:
        return "HIGH"
    if score >= 0.60:
        return "MODERATE"
    if score >= 0.40:
        return "LIMITED"
    return "LOW"


def finite(value, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    return number if math.isfinite(number) else default
