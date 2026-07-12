"""Walk-forward validation for Meta Research hypotheses."""

from __future__ import annotations

import pandas as pd

from atlas.investment.hypothesis_validation.config import (
    MINIMUM_BASELINE_TEST_TRADES,
    MINIMUM_TRAINING_DAYS,
    STEP_DAYS,
    SUPPORTED_HYPOTHESIS_TYPES,
    TEST_WINDOW_DAYS,
)
from atlas.investment.hypothesis_validation.metrics import (
    compare_metrics,
    summarize_trade_returns,
)
from atlas.investment.hypothesis_validation.states import (
    apply_state_definition,
    build_gate_mask,
    fit_state_definition,
)


def validate_hypothesis(
    hypothesis: dict,
    evidence: pd.DataFrame,
) -> dict:
    """Validate one hypothesis using expanding walk-forward folds."""
    hypothesis_type = str(
        hypothesis.get(
            "hypothesis_type",
            ""
        )
    ).upper()

    if (
        hypothesis_type
        not in SUPPORTED_HYPOTHESIS_TYPES
    ):
        return empty_validation(
            hypothesis,
            reason=(
                "Unsupported hypothesis type."
            ),
        )

    engine_id = str(
        hypothesis.get(
            "engine_id",
            ""
        )
    )

    feature = str(
        hypothesis.get(
            "feature",
            ""
        )
    )

    target_state = str(
        hypothesis.get(
            "state",
            ""
        )
    ).upper()

    engine = evidence[
        evidence["engine_id"]
        .astype(str)
        .eq(engine_id)
    ].copy()

    if (
        engine.empty
        or feature not in engine.columns
    ):
        return empty_validation(
            hypothesis,
            reason=(
                "Engine evidence or feature "
                "is unavailable."
            ),
        )

    engine = engine.sort_values(
        "timestamp",
        kind="stable",
    ).reset_index(drop=True)

    fold_windows = build_fold_windows(
        engine["timestamp"]
    )

    fold_rows = []
    ledger_rows = []

    for fold_number, (
        training_end,
        test_end,
    ) in enumerate(
        fold_windows,
        start=1,
    ):
        training = engine[
            engine["timestamp"]
            <= training_end
        ].copy()

        test = engine[
            (
                engine["timestamp"]
                > training_end
            )
            & (
                engine["timestamp"]
                <= test_end
            )
        ].copy()

        if (
            len(test)
            < MINIMUM_BASELINE_TEST_TRADES
        ):
            continue

        definition = fit_state_definition(
            training,
            feature=feature,
        )

        if definition is None:
            continue

        test_states = (
            apply_state_definition(
                test,
                definition,
            )
        )

        candidate_mask = build_gate_mask(
            test_states,
            hypothesis_type=(
                hypothesis_type
            ),
            target_state=target_state,
        )

        candidate = test.loc[
            candidate_mask
        ].copy()

        baseline_metrics = (
            summarize_trade_returns(
                test
            )
        )

        candidate_metrics = (
            summarize_trade_returns(
                candidate
            )
        )

        advantages = compare_metrics(
            baseline_metrics,
            candidate_metrics,
        )

        fold_winner = (
            advantages[
                "mean_return_advantage"
            ] > 0
            and advantages[
                "profit_factor_advantage"
            ] >= 0
            and advantages[
                "drawdown_improvement"
            ] >= 0
        )

        retention_ratio = (
            len(candidate)
            / len(test)
            if len(test) > 0
            else 0.0
        )

        fold_rows.append({
            "hypothesis_id": hypothesis.get(
                "hypothesis_id"
            ),
            "hypothesis_type": (
                hypothesis_type
            ),
            "engine_id": engine_id,
            "feature": feature,
            "target_state": (
                target_state
            ),
            "fold_number": fold_number,
            "training_start": (
                training[
                    "timestamp"
                ].min()
            ),
            "training_end": training_end,
            "test_start": (
                test[
                    "timestamp"
                ].min()
            ),
            "test_end": test_end,
            "feature_type": (
                definition.feature_type
            ),
            "low_threshold": (
                definition.low_threshold
            ),
            "high_threshold": (
                definition.high_threshold
            ),
            "baseline_trade_count": int(
                len(test)
            ),
            "candidate_trade_count": int(
                len(candidate)
            ),
            "retention_ratio": round(
                retention_ratio,
                8,
            ),
            "baseline_mean_return": (
                baseline_metrics[
                    "mean_return"
                ]
            ),
            "candidate_mean_return": (
                candidate_metrics[
                    "mean_return"
                ]
            ),
            "baseline_profit_factor": (
                baseline_metrics[
                    "profit_factor"
                ]
            ),
            "candidate_profit_factor": (
                candidate_metrics[
                    "profit_factor"
                ]
            ),
            "baseline_sharpe": (
                baseline_metrics[
                    "trade_sharpe"
                ]
            ),
            "candidate_sharpe": (
                candidate_metrics[
                    "trade_sharpe"
                ]
            ),
            "baseline_drawdown": (
                baseline_metrics[
                    "maximum_drawdown"
                ]
            ),
            "candidate_drawdown": (
                candidate_metrics[
                    "maximum_drawdown"
                ]
            ),
            **advantages,
            "fold_winner": bool(
                fold_winner
            ),
        })

        test_ledger = test.copy()

        test_ledger[
            "hypothesis_id"
        ] = hypothesis.get(
            "hypothesis_id"
        )

        test_ledger[
            "hypothesis_type"
        ] = hypothesis_type

        test_ledger["feature"] = feature
        test_ledger[
            "target_state"
        ] = target_state

        test_ledger[
            "observed_state"
        ] = test_states

        test_ledger[
            "candidate_selected"
        ] = candidate_mask

        test_ledger[
            "fold_number"
        ] = fold_number

        ledger_columns = [
            "hypothesis_id",
            "hypothesis_type",
            "engine_id",
            "asset",
            "timestamp",
            "fold_number",
            "feature",
            "target_state",
            "observed_state",
            "candidate_selected",
            "strategy_return",
            "direction",
            "regime",
        ]

        for column in ledger_columns:
            if column not in (
                test_ledger.columns
            ):
                test_ledger[column] = None

        ledger_rows.extend(
            test_ledger[
                ledger_columns
            ].to_dict(
                orient="records"
            )
        )

    folds = pd.DataFrame(
        fold_rows
    )

    ledger = pd.DataFrame(
        ledger_rows
    )

    return {
        "hypothesis": hypothesis,
        "folds": folds,
        "ledger": ledger,
    }


def build_fold_windows(
    timestamps: pd.Series,
) -> list[tuple]:
    """Build expanding-training walk-forward windows."""
    values = pd.to_datetime(
        timestamps,
        errors="coerce",
        utc=True,
    ).dropna().sort_values()

    if values.empty:
        return []

    start = values.min()
    end = values.max()

    training_end = (
        start
        + pd.Timedelta(
            days=MINIMUM_TRAINING_DAYS
        )
    )

    windows = []

    while training_end < end:
        test_end = min(
            training_end
            + pd.Timedelta(
                days=TEST_WINDOW_DAYS
            ),
            end,
        )

        windows.append(
            (
                training_end,
                test_end,
            )
        )

        training_end = (
            training_end
            + pd.Timedelta(
                days=STEP_DAYS
            )
        )

    return windows


def empty_validation(
    hypothesis: dict,
    *,
    reason: str,
) -> dict:
    return {
        "hypothesis": hypothesis,
        "folds": pd.DataFrame(),
        "ledger": pd.DataFrame(),
        "reason": reason,
    }
