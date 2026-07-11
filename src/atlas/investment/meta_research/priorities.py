"""Meta Research Engine v1 research-priority ranking."""

from __future__ import annotations

import pandas as pd


PRIORITY_COLUMNS = [
    "research_rank",
    "research_target",
    "target_type",
    "priority_score",
    "confidence",
    "expected_value",
    "risk_reduction_value",
    "coverage_value",
    "recommended_next_step",
    "source_id",
]


def build_research_priorities(
    hypotheses: pd.DataFrame,
) -> pd.DataFrame:
    if (
        hypotheses is None
        or hypotheses.empty
    ):
        return pd.DataFrame(
            columns=PRIORITY_COLUMNS
        )

    rows = []

    for _, row in hypotheses.iterrows():
        hypothesis_type = str(
            row[
                "hypothesis_type"
            ]
        )

        priority = float(
            row["priority"]
        )

        confidence = float(
            row["confidence"]
        )

        if hypothesis_type == (
            "FAILURE_MODE_GATE"
        ):
            risk_value = priority
            expected_value = max(
                0.0,
                abs(
                    float(
                        row[
                            "return_lift"
                        ]
                    )
                ),
            )
            coverage_value = 0.50

        elif hypothesis_type == (
            "CONDITIONAL_OPPORTUNITY"
        ):
            risk_value = 0.30
            expected_value = max(
                0.0,
                float(
                    row[
                        "return_lift"
                    ]
                ),
            )
            coverage_value = 0.60

        else:
            risk_value = 0.40
            expected_value = 0.25
            coverage_value = (
                priority
            )

        combined = (
            priority * 0.40
            + confidence * 0.25
            + min(
                1.0,
                expected_value / 0.04,
            ) * 0.20
            + coverage_value * 0.15
        )

        target = (
            str(
                row["engine_id"]
            )
            if str(
                row["engine_id"]
            )
            else str(
                row["family"]
            )
        )

        rows.append({
            "research_target": target,
            "target_type": (
                hypothesis_type
            ),
            "priority_score": round(
                combined,
                8,
            ),
            "confidence": confidence,
            "expected_value": round(
                expected_value,
                8,
            ),
            "risk_reduction_value": round(
                risk_value,
                8,
            ),
            "coverage_value": round(
                coverage_value,
                8,
            ),
            "recommended_next_step": str(
                row[
                    "proposed_test"
                ]
            ),
            "source_id": str(
                row["hypothesis_id"]
            ),
        })

    result = pd.DataFrame(rows)

    result = result.sort_values(
        [
            "priority_score",
            "confidence",
            "source_id",
        ],
        ascending=[
            False,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)

    result.insert(
        0,
        "research_rank",
        range(
            1,
            len(result) + 1,
        ),
    )

    return result[
        PRIORITY_COLUMNS
    ]
