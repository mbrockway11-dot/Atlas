"""Predeclared acceptance-criterion evaluation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.research_experiment_execution.identity import (
    boolean,
    number,
    text,
)


def evaluate_acceptance_criteria(
    *,
    experiment_id: str,
    criteria: pd.DataFrame,
    evidence: dict[str, Any],
) -> pd.DataFrame:
    rows = []

    if criteria is None or criteria.empty:
        return pd.DataFrame()

    applicable = criteria[
        criteria[
            "experiment_id"
        ].astype(str).eq(
            experiment_id
        )
    ].copy()

    for _, criterion in (
        applicable.iterrows()
    ):
        name = text(
            criterion.get(
                "criterion_name"
            )
        )

        operator = text(
            criterion.get(
                "operator"
            )
        )

        threshold = criterion.get(
            "threshold_value"
        )

        observed = evidence.get(
            name
        )

        passed = compare(
            observed,
            operator,
            threshold,
        )

        rows.append({
            "criterion_id": text(
                criterion.get(
                    "criterion_id"
                )
            ),
            "experiment_id": (
                experiment_id
            ),
            "criterion_name": name,
            "operator": operator,
            "threshold_value": (
                threshold
            ),
            "observed_value": (
                observed
            ),
            "passed": bool(
                passed
            ),
            "status": (
                "PASS"
                if passed
                else "FAIL"
            ),
            "failure_action": text(
                criterion.get(
                    "failure_action"
                )
            ),
            "execution_instruction": False,
        })

    return pd.DataFrame(rows)


def compare(
    observed: Any,
    operator: str,
    threshold: Any,
) -> bool:
    if operator == "==":
        if isinstance(
            threshold,
            bool,
        ) or text(
            threshold
        ).strip().lower() in {
            "true",
            "false",
        }:
            return (
                boolean(observed)
                == boolean(threshold)
            )

        return text(
            observed
        ) == text(
            threshold
        )

    observed_number = number(
        observed,
        default=float("nan"),
    )

    threshold_number = number(
        threshold,
        default=float("nan"),
    )

    if (
        pd.isna(
            observed_number
        )
        or pd.isna(
            threshold_number
        )
    ):
        return False

    if operator == ">":
        return (
            observed_number
            > threshold_number
        )

    if operator == ">=":
        return (
            observed_number
            >= threshold_number
        )

    if operator == "<":
        return (
            observed_number
            < threshold_number
        )

    if operator == "<=":
        return (
            observed_number
            <= threshold_number
        )

    return False
