"""Frozen candidate-gate evaluation."""

from __future__ import annotations

import re

import pandas as pd

from atlas.investment.research_experiment_execution.identity import (
    text,
)


EXCLUSION_PATTERN = re.compile(
    r"""
    ^ALLOW_SIGNAL\s*=\s*NOT\s*
    \(
        \s*(?P<feature>[A-Za-z0-9_]+)\s*
        ==\s*
        ['"](?P<condition>[^'"]+)['"]
        \s*
    \)\s*$
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


def parse_gate_expression(
    expression: str,
) -> dict:
    normalized = text(
        expression
    ).strip()

    match = EXCLUSION_PATTERN.match(
        normalized
    )

    if match:
        return {
            "supported": True,
            "gate_type": (
                "EXCLUDE_EQUALITY"
            ),
            "feature_name": (
                match.group(
                    "feature"
                )
            ),
            "condition_value": (
                match.group(
                    "condition"
                )
            ),
            "error": "",
        }

    return {
        "supported": False,
        "gate_type": "UNSUPPORTED",
        "feature_name": "",
        "condition_value": "",
        "error": (
            "Gate expression is outside the "
            "Research Execution Lab v1 safe grammar."
        ),
    }


def apply_frozen_gate(
    observations: pd.DataFrame,
    expression: str,
) -> tuple[
    pd.Series,
    dict,
]:
    parsed = parse_gate_expression(
        expression
    )

    if not parsed["supported"]:
        return (
            pd.Series(
                False,
                index=observations.index,
                dtype=bool,
            ),
            parsed,
        )

    feature = parsed[
        "feature_name"
    ]

    condition = parsed[
        "condition_value"
    ]

    if feature not in observations.columns:
        parsed["supported"] = False
        parsed["error"] = (
            f"Required point-in-time feature "
            f"column is missing: {feature}"
        )

        return (
            pd.Series(
                False,
                index=observations.index,
                dtype=bool,
            ),
            parsed,
        )

    observed = (
        observations[feature]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    target = (
        str(condition)
        .strip()
        .upper()
    )

    allowed = ~observed.eq(
        target
    )

    return (
        allowed.astype(bool),
        parsed,
    )
