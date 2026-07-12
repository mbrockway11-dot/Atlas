"""Research evidence quality analysis."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_evidence_accumulator.config import (
    MAXIMUM_CONTRADICTION_RATE,
    MAXIMUM_DECAY_RATE,
    MINIMUM_COMPLETED_RUNS,
    MINIMUM_DISTINCT_STATE_HASHES,
    MINIMUM_TOTAL_CANDIDATE_TRADES,
    MINIMUM_TOTAL_FOLD_COUNT,
)
from atlas.investment.research_evidence_accumulator.identity import (
    boolean,
    clamp,
    number,
    safe_mean,
    text,
)


def calculate_consistency(
    variant_history: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    if (
        variant_history is None
        or variant_history.empty
    ):
        return pd.DataFrame()

    grouped = variant_history.groupby(
        [
            "research_program_id",
            "experiment_variant_id",
        ],
        dropna=False,
    )

    for (
        program_id,
        variant_id,
    ), group in grouped:
        pass_rate = float(
            group[
                "acceptance_passed"
            ].map(boolean).mean()
        )

        mean_values = group[
            "mean_return_advantage"
        ].map(number)

        sharpe_values = group[
            "sharpe_advantage"
        ].map(number)

        drawdown_values = group[
            "drawdown_improvement"
        ].map(number)

        fold_values = group[
            "fold_win_rate"
        ].map(number)

        positive_mean_rate = float(
            mean_values.gt(0).mean()
        )

        positive_sharpe_rate = float(
            sharpe_values.gt(0).mean()
        )

        nonnegative_drawdown_rate = float(
            drawdown_values.ge(0).mean()
        )

        fold_consistency = float(
            fold_values.ge(0.60).mean()
        )

        consistency_score = clamp(
            pass_rate * 0.30
            + positive_mean_rate * 0.25
            + positive_sharpe_rate * 0.20
            + nonnegative_drawdown_rate * 0.15
            + fold_consistency * 0.10
        )

        rows.append({
            "research_program_id": text(
                program_id
            ),
            "experiment_variant_id": text(
                variant_id
            ),
            "run_count": int(
                len(group)
            ),
            "run_pass_rate": pass_rate,
            "positive_mean_return_rate": (
                positive_mean_rate
            ),
            "positive_sharpe_rate": (
                positive_sharpe_rate
            ),
            "nonnegative_drawdown_rate": (
                nonnegative_drawdown_rate
            ),
            "fold_consistency_rate": (
                fold_consistency
            ),
            "consistency_score": (
                consistency_score
            ),
            "execution_instruction": False,
        })

    return pd.DataFrame(rows)


def calculate_contradictions(
    variant_history: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    if (
        variant_history is None
        or variant_history.empty
    ):
        return pd.DataFrame()

    grouped = variant_history.groupby(
        [
            "research_program_id",
            "experiment_variant_id",
        ],
        dropna=False,
    )

    for (
        program_id,
        variant_id,
    ), group in grouped:
        mean_signs = group[
            "mean_return_advantage"
        ].map(number).map(
            sign
        )

        sharpe_signs = group[
            "sharpe_advantage"
        ].map(number).map(
            sign
        )

        drawdown_signs = group[
            "drawdown_improvement"
        ].map(number).map(
            sign
        )

        contradiction_events = int(
            count_sign_contradictions(
                mean_signs
            )
            + count_sign_contradictions(
                sharpe_signs
            )
            + count_sign_contradictions(
                drawdown_signs
            )
        )

        possible_events = max(
            1,
            3 * (
                len(group) - 1
            ),
        )

        contradiction_rate = clamp(
            contradiction_events
            / possible_events
        )

        rows.append({
            "research_program_id": text(
                program_id
            ),
            "experiment_variant_id": text(
                variant_id
            ),
            "run_count": int(
                len(group)
            ),
            "contradiction_events": (
                contradiction_events
            ),
            "possible_contradiction_events": (
                possible_events
            ),
            "contradiction_rate": (
                contradiction_rate
            ),
            "contradiction_status": (
                "HIGH"
                if contradiction_rate
                > MAXIMUM_CONTRADICTION_RATE
                else "ACCEPTABLE"
            ),
            "execution_instruction": False,
        })

    return pd.DataFrame(rows)


def calculate_decay(
    variant_history: pd.DataFrame,
    run_history: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    if (
        variant_history is None
        or variant_history.empty
    ):
        return pd.DataFrame()

    merged = variant_history.copy()

    if (
        run_history is not None
        and not run_history.empty
        and "run_id" in run_history.columns
    ):
        time_columns = [
            column
            for column in (
                "run_id",
                "completed_at",
                "state_hash",
            )
            if column in run_history.columns
        ]

        merged = merged.merge(
            run_history[
                time_columns
            ],
            on="run_id",
            how="left",
            suffixes=(
                "",
                "_run",
            ),
        )

    if "completed_at" not in merged.columns:
        merged["completed_at"] = ""

    merged[
        "completed_at_parsed"
    ] = pd.to_datetime(
        merged["completed_at"],
        utc=True,
        errors="coerce",
    )

    grouped = merged.groupby(
        [
            "research_program_id",
            "experiment_variant_id",
        ],
        dropna=False,
    )

    for (
        program_id,
        variant_id,
    ), group in grouped:
        ordered = group.sort_values(
            "completed_at_parsed",
            kind="stable",
        )

        split_index = max(
            1,
            len(ordered) // 2,
        )

        early = ordered.iloc[
            :split_index
        ]

        recent = ordered.iloc[
            split_index:
        ]

        if recent.empty:
            recent = early

        early_score = safe_mean([
            safe_mean(
                early[
                    "mean_return_advantage"
                ].map(number).tolist()
            ),
            safe_mean(
                early[
                    "sharpe_advantage"
                ].map(number).tolist()
            ),
            safe_mean(
                early[
                    "fold_win_rate"
                ].map(number).tolist()
            ),
        ])

        recent_score = safe_mean([
            safe_mean(
                recent[
                    "mean_return_advantage"
                ].map(number).tolist()
            ),
            safe_mean(
                recent[
                    "sharpe_advantage"
                ].map(number).tolist()
            ),
            safe_mean(
                recent[
                    "fold_win_rate"
                ].map(number).tolist()
            ),
        ])

        denominator = max(
            abs(early_score),
            1e-9,
        )

        decay_rate = max(
            0.0,
            (
                early_score
                - recent_score
            )
            / denominator,
        )

        rows.append({
            "research_program_id": text(
                program_id
            ),
            "experiment_variant_id": text(
                variant_id
            ),
            "run_count": int(
                len(group)
            ),
            "early_evidence_score": (
                early_score
            ),
            "recent_evidence_score": (
                recent_score
            ),
            "decay_rate": decay_rate,
            "decay_status": (
                "MATERIAL_DECAY"
                if decay_rate
                > MAXIMUM_DECAY_RATE
                else "STABLE"
            ),
            "execution_instruction": False,
        })

    return pd.DataFrame(rows)


def calculate_sufficiency(
    variant_history: pd.DataFrame,
    run_history: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    if (
        variant_history is None
        or variant_history.empty
    ):
        return pd.DataFrame()

    grouped = variant_history.groupby(
        [
            "research_program_id",
            "experiment_variant_id",
        ],
        dropna=False,
    )

    for (
        program_id,
        variant_id,
    ), group in grouped:
        run_ids = set(
            group[
                "run_id"
            ].astype(str)
        )

        matching_runs = (
            run_history[
                run_history[
                    "run_id"
                ].astype(str).isin(
                    run_ids
                )
            ].copy()
            if (
                run_history is not None
                and not run_history.empty
            )
            else pd.DataFrame()
        )

        completed_run_count = int(
            matching_runs[
                "run_status"
            ].astype(str).eq(
                "COMPLETED"
            ).sum()
        ) if not matching_runs.empty else int(
            len(group)
        )

        distinct_state_hashes = int(
            matching_runs[
                "state_hash"
            ].astype(str).nunique()
        ) if (
            not matching_runs.empty
            and "state_hash"
            in matching_runs.columns
        ) else 0

        total_candidate_trades = int(
            group[
                "candidate_trade_count"
            ].map(number).sum()
        )

        total_fold_count = int(
            group[
                "fold_count"
            ].map(number).sum()
        )

        checks = {
            "completed_runs_sufficient": (
                completed_run_count
                >= MINIMUM_COMPLETED_RUNS
            ),
            "state_diversity_sufficient": (
                distinct_state_hashes
                >= MINIMUM_DISTINCT_STATE_HASHES
            ),
            "candidate_trades_sufficient": (
                total_candidate_trades
                >= MINIMUM_TOTAL_CANDIDATE_TRADES
            ),
            "folds_sufficient": (
                total_fold_count
                >= MINIMUM_TOTAL_FOLD_COUNT
            ),
        }

        passed_count = sum(
            checks.values()
        )

        sufficiency_score = (
            passed_count
            / len(checks)
        )

        rows.append({
            "research_program_id": text(
                program_id
            ),
            "experiment_variant_id": text(
                variant_id
            ),
            "completed_run_count": (
                completed_run_count
            ),
            "distinct_state_hashes": (
                distinct_state_hashes
            ),
            "total_candidate_trades": (
                total_candidate_trades
            ),
            "total_fold_count": (
                total_fold_count
            ),
            **checks,
            "sufficiency_score": (
                sufficiency_score
            ),
            "evidence_sufficient": (
                all(
                    checks.values()
                )
            ),
            "execution_instruction": False,
        })

    return pd.DataFrame(rows)


def sign(
    value: float,
) -> int:
    if value > 0:
        return 1

    if value < 0:
        return -1

    return 0


def count_sign_contradictions(
    values: pd.Series,
) -> int:
    sequence = [
        int(value)
        for value in values
        if int(value) != 0
    ]

    if len(sequence) < 2:
        return 0

    return sum(
        1
        for left, right in zip(
            sequence,
            sequence[1:],
        )
        if left != right
    )
