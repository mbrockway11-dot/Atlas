"""Atlas Research Experiment Execution Lab v1 engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_experiment_execution.acceptance import (
    evaluate_acceptance_criteria,
)
from atlas.investment.research_experiment_execution.config import (
    ELIGIBLE_PROGRAM_STATUS,
    MINIMUM_OBSERVATION_COUNT,
    REQUIRED_DESIGN_CHECKS,
)
from atlas.investment.research_experiment_execution.folds import (
    assign_walk_forward_folds,
)
from atlas.investment.research_experiment_execution.gates import (
    apply_frozen_gate,
    parse_gate_expression,
)
from atlas.investment.research_experiment_execution.identity import (
    boolean,
    integer,
    number,
    stable_id,
    text,
)
from atlas.investment.research_experiment_execution.metrics import (
    calculate_metrics,
)


def execute_experiment_bundle(
    sources: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    programs = sources.get(
        "program_registry",
        pd.DataFrame(),
    )

    designs = sources.get(
        "designs",
        pd.DataFrame(),
    )

    variants = sources.get(
        "variants",
        pd.DataFrame(),
    )

    criteria = sources.get(
        "acceptance_criteria",
        pd.DataFrame(),
    )

    design_validation = sources.get(
        "design_validation",
        pd.DataFrame(),
    )

    observations = sources.get(
        "observations",
        pd.DataFrame(),
    )

    state_hash = text(
        sources.get(
            "compiler_report",
            {},
        ).get(
            "state_hash",
            "",
        )
    )

    observation_source_path = text(
        sources.get(
            "observation_source_path"
        )
    )

    runs = []
    fold_results = []
    variant_results = []
    trade_comparison = []
    acceptance_results = []
    exclusions = []
    validations = []
    evidence_summaries = []

    if programs is None or programs.empty:
        return empty_bundle()

    eligible_programs = programs[
        programs[
            "current_status"
        ].astype(str).eq(
            ELIGIBLE_PROGRAM_STATUS
        )
        & ~programs[
            "is_blocked"
        ].astype(bool)
    ].copy()

    for _, program in (
        eligible_programs.iterrows()
    ):
        program_id = text(
            program.get(
                "research_program_id"
            )
        )

        program_designs = filter_frame(
            designs,
            "research_program_id",
            program_id,
        )

        if program_designs.empty:
            exclusions.append(
                exclusion_row(
                    program_id=program_id,
                    experiment_id="",
                    reason_code=(
                        "DESIGN_NOT_FOUND"
                    ),
                    reason=(
                        "No frozen experiment design "
                        "was found for the eligible program."
                    ),
                )
            )

            continue

        design = (
            program_designs.iloc[0]
        )

        experiment_id = text(
            design.get(
                "experiment_id"
            )
        )

        engine_id = text(
            design.get(
                "parent_engine_id"
            )
        )

        run_id = stable_id(
            "REXRUN",
            {
                "experiment_id": experiment_id,
                "state_hash": state_hash,
                "execution_version": "v1",
            },
        )

        design_is_valid = (
            validate_frozen_design(
                experiment_id=experiment_id,
                validation=design_validation,
            )
        )

        validations.append({
            "run_id": run_id,
            "experiment_id": (
                experiment_id
            ),
            "check_id": (
                "FROZEN_DESIGN_VALID"
            ),
            "passed": bool(
                design_is_valid
            ),
            "status": (
                "PASS"
                if design_is_valid
                else "FAIL"
            ),
            "detail": "",
            "execution_instruction": False,
        })

        if not design_is_valid:
            exclusions.append(
                exclusion_row(
                    program_id=program_id,
                    experiment_id=experiment_id,
                    reason_code=(
                        "DESIGN_VALIDATION_FAILED"
                    ),
                    reason=(
                        "One or more required frozen-design "
                        "validation checks did not pass."
                    ),
                )
            )

            continue

        engine_observations = (
            observations[
                observations[
                    "engine_id"
                ].astype(str).eq(
                    engine_id
                )
            ].copy()
            if (
                observations is not None
                and not observations.empty
            )
            else pd.DataFrame()
        )

        enough_observations = (
            len(engine_observations)
            >= MINIMUM_OBSERVATION_COUNT
        )

        validations.append({
            "run_id": run_id,
            "experiment_id": (
                experiment_id
            ),
            "check_id": (
                "MINIMUM_OBSERVATIONS_AVAILABLE"
            ),
            "passed": bool(
                enough_observations
            ),
            "status": (
                "PASS"
                if enough_observations
                else "FAIL"
            ),
            "detail": (
                f"{len(engine_observations)} "
                "observation(s) available."
            ),
            "execution_instruction": False,
        })

        if not enough_observations:
            exclusions.append(
                exclusion_row(
                    program_id=program_id,
                    experiment_id=experiment_id,
                    reason_code=(
                        "INSUFFICIENT_OBSERVATIONS"
                    ),
                    reason=(
                        f"Only {len(engine_observations)} "
                        "compatible observation(s) were found."
                    ),
                )
            )

            continue

        fold_count = integer(
            design.get(
                "fold_count"
            ),
            default=6,
        )

        embargo_days = integer(
            design.get(
                "embargo_days"
            ),
            default=7,
        )

        (
            assigned_observations,
            fold_plan,
        ) = assign_walk_forward_folds(
            engine_observations,
            fold_count=fold_count,
            embargo_days=embargo_days,
        )

        folds_valid = bool(
            not fold_plan.empty
            and not fold_plan[
                "overlap_detected"
            ].astype(bool).any()
            and not fold_plan[
                "uses_future_data"
            ].astype(bool).any()
        )

        validations.append({
            "run_id": run_id,
            "experiment_id": (
                experiment_id
            ),
            "check_id": (
                "NON_OVERLAPPING_FOLDS"
            ),
            "passed": folds_valid,
            "status": (
                "PASS"
                if folds_valid
                else "FAIL"
            ),
            "detail": (
                f"{len(fold_plan)} fold(s) created."
            ),
            "execution_instruction": False,
        })

        if not folds_valid:
            exclusions.append(
                exclusion_row(
                    program_id=program_id,
                    experiment_id=experiment_id,
                    reason_code=(
                        "INVALID_FOLD_PLAN"
                    ),
                    reason=(
                        "The non-overlapping walk-forward "
                        "fold plan could not be constructed."
                    ),
                )
            )

            continue

        experiment_variants = filter_frame(
            variants,
            "experiment_id",
            experiment_id,
        )

        if experiment_variants.empty:
            exclusions.append(
                exclusion_row(
                    program_id=program_id,
                    experiment_id=experiment_id,
                    reason_code=(
                        "NO_CANDIDATE_VARIANTS"
                    ),
                    reason=(
                        "The frozen design contains no "
                        "candidate variant definitions."
                    ),
                )
            )

            continue

        baseline_metrics = calculate_metrics(
            assigned_observations[
                "trade_return"
            ]
        )

        successful_variant_count = 0

        for _, variant in (
            experiment_variants.iterrows()
        ):
            variant_id = text(
                variant.get(
                    "experiment_variant_id"
                )
            )

            gate_expression = text(
                variant.get(
                    "gate_expression"
                )
            )

            gate_mask, gate_details = (
                apply_frozen_gate(
                    assigned_observations,
                    gate_expression,
                )
            )

            if not gate_details[
                "supported"
            ]:
                exclusions.append({
                    **exclusion_row(
                        program_id=program_id,
                        experiment_id=experiment_id,
                        reason_code=(
                            "UNSUPPORTED_OR_MISSING_GATE"
                        ),
                        reason=gate_details[
                            "error"
                        ],
                    ),
                    "experiment_variant_id": (
                        variant_id
                    ),
                })

                continue

            successful_variant_count += 1

            candidate_observations = (
                assigned_observations[
                    gate_mask
                ].copy()
            )

            candidate_metrics = (
                calculate_metrics(
                    candidate_observations[
                        "trade_return"
                    ]
                )
            )

            fold_wins = 0
            completed_fold_count = 0

            for _, fold in (
                fold_plan.iterrows()
            ):
                fold_number = integer(
                    fold.get(
                        "fold_number"
                    )
                )

                baseline_fold = (
                    assigned_observations[
                        assigned_observations[
                            "fold_number"
                        ].eq(
                            fold_number
                        )
                    ]
                )

                candidate_fold = (
                    candidate_observations[
                        candidate_observations[
                            "fold_number"
                        ].eq(
                            fold_number
                        )
                    ]
                )

                baseline_fold_metrics = (
                    calculate_metrics(
                        baseline_fold[
                            "trade_return"
                        ]
                    )
                )

                candidate_fold_metrics = (
                    calculate_metrics(
                        candidate_fold[
                            "trade_return"
                        ]
                    )
                )

                mean_advantage = (
                    candidate_fold_metrics[
                        "mean_return"
                    ]
                    - baseline_fold_metrics[
                        "mean_return"
                    ]
                )

                sharpe_advantage = (
                    candidate_fold_metrics[
                        "sharpe_ratio"
                    ]
                    - baseline_fold_metrics[
                        "sharpe_ratio"
                    ]
                )

                drawdown_improvement = (
                    candidate_fold_metrics[
                        "max_drawdown"
                    ]
                    - baseline_fold_metrics[
                        "max_drawdown"
                    ]
                )

                fold_passed = bool(
                    candidate_fold_metrics[
                        "trade_count"
                    ] > 0
                    and mean_advantage > 0
                )

                completed_fold_count += 1

                if fold_passed:
                    fold_wins += 1

                fold_results.append({
                    "run_id": run_id,
                    "experiment_id": (
                        experiment_id
                    ),
                    "experiment_variant_id": (
                        variant_id
                    ),
                    "fold_number": (
                        fold_number
                    ),
                    "test_start": fold.get(
                        "test_start"
                    ),
                    "test_end": fold.get(
                        "test_end"
                    ),
                    "baseline_trade_count": (
                        baseline_fold_metrics[
                            "trade_count"
                        ]
                    ),
                    "candidate_trade_count": (
                        candidate_fold_metrics[
                            "trade_count"
                        ]
                    ),
                    "baseline_mean_return": (
                        baseline_fold_metrics[
                            "mean_return"
                        ]
                    ),
                    "candidate_mean_return": (
                        candidate_fold_metrics[
                            "mean_return"
                        ]
                    ),
                    "mean_return_advantage": (
                        mean_advantage
                    ),
                    "baseline_sharpe": (
                        baseline_fold_metrics[
                            "sharpe_ratio"
                        ]
                    ),
                    "candidate_sharpe": (
                        candidate_fold_metrics[
                            "sharpe_ratio"
                        ]
                    ),
                    "sharpe_advantage": (
                        sharpe_advantage
                    ),
                    "baseline_max_drawdown": (
                        baseline_fold_metrics[
                            "max_drawdown"
                        ]
                    ),
                    "candidate_max_drawdown": (
                        candidate_fold_metrics[
                            "max_drawdown"
                        ]
                    ),
                    "drawdown_improvement": (
                        drawdown_improvement
                    ),
                    "fold_passed": (
                        fold_passed
                    ),
                    "execution_instruction": False,
                })

            fold_win_rate = (
                fold_wins
                / completed_fold_count
                if completed_fold_count > 0
                else 0.0
            )

            retention_ratio = (
                candidate_metrics[
                    "trade_count"
                ]
                / baseline_metrics[
                    "trade_count"
                ]
                if baseline_metrics[
                    "trade_count"
                ] > 0
                else 0.0
            )

            evidence = {
                "minimum_candidate_trades": (
                    candidate_metrics[
                        "trade_count"
                    ]
                ),
                "fold_win_rate": (
                    fold_win_rate
                ),
                "mean_return_advantage": (
                    candidate_metrics[
                        "mean_return"
                    ]
                    - baseline_metrics[
                        "mean_return"
                    ]
                ),
                "sharpe_advantage": (
                    candidate_metrics[
                        "sharpe_ratio"
                    ]
                    - baseline_metrics[
                        "sharpe_ratio"
                    ]
                ),
                "drawdown_improvement": (
                    candidate_metrics[
                        "max_drawdown"
                    ]
                    - baseline_metrics[
                        "max_drawdown"
                    ]
                ),
                "retention_ratio": (
                    retention_ratio
                ),
                "future_data_used": False,
                "overlapping_test_trades": False,
            }

            variant_acceptance = (
                evaluate_acceptance_criteria(
                    experiment_id=experiment_id,
                    criteria=criteria,
                    evidence=evidence,
                )
            )

            if not variant_acceptance.empty:
                variant_acceptance[
                    "run_id"
                ] = run_id

                variant_acceptance[
                    "experiment_variant_id"
                ] = variant_id

                acceptance_results.extend(
                    variant_acceptance.to_dict(
                        orient="records"
                    )
                )

            all_criteria_passed = bool(
                not variant_acceptance.empty
                and variant_acceptance[
                    "passed"
                ].astype(bool).all()
            )

            variant_results.append({
                "run_id": run_id,
                "experiment_id": (
                    experiment_id
                ),
                "research_program_id": (
                    program_id
                ),
                "experiment_variant_id": (
                    variant_id
                ),
                "source_candidate_id": text(
                    variant.get(
                        "source_candidate_id"
                    )
                ),
                "gate_expression": (
                    gate_expression
                ),
                "baseline_trade_count": (
                    baseline_metrics[
                        "trade_count"
                    ]
                ),
                "candidate_trade_count": (
                    candidate_metrics[
                        "trade_count"
                    ]
                ),
                "retention_ratio": (
                    retention_ratio
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
                "mean_return_advantage": (
                    evidence[
                        "mean_return_advantage"
                    ]
                ),
                "baseline_expectancy": (
                    baseline_metrics[
                        "expectancy"
                    ]
                ),
                "candidate_expectancy": (
                    candidate_metrics[
                        "expectancy"
                    ]
                ),
                "baseline_sharpe": (
                    baseline_metrics[
                        "sharpe_ratio"
                    ]
                ),
                "candidate_sharpe": (
                    candidate_metrics[
                        "sharpe_ratio"
                    ]
                ),
                "sharpe_advantage": (
                    evidence[
                        "sharpe_advantage"
                    ]
                ),
                "baseline_max_drawdown": (
                    baseline_metrics[
                        "max_drawdown"
                    ]
                ),
                "candidate_max_drawdown": (
                    candidate_metrics[
                        "max_drawdown"
                    ]
                ),
                "drawdown_improvement": (
                    evidence[
                        "drawdown_improvement"
                    ]
                ),
                "fold_count": (
                    completed_fold_count
                ),
                "fold_win_rate": (
                    fold_win_rate
                ),
                "acceptance_passed": (
                    all_criteria_passed
                ),
                "result_status": (
                    "PASS"
                    if all_criteria_passed
                    else "FAIL"
                ),
                "execution_instruction": False,
                "implementation_authorized": False,
                "production_eligible": False,
            })

            allowed_trade_ids = set(
                candidate_observations[
                    "trade_id"
                ].astype(str)
            )

            for _, observation in (
                assigned_observations.iterrows()
            ):
                trade_id = text(
                    observation.get(
                        "trade_id"
                    )
                )

                retained = (
                    trade_id
                    in allowed_trade_ids
                )

                trade_comparison.append({
                    "run_id": run_id,
                    "experiment_id": (
                        experiment_id
                    ),
                    "experiment_variant_id": (
                        variant_id
                    ),
                    "trade_id": trade_id,
                    "timestamp": (
                        observation[
                            "timestamp"
                        ].isoformat()
                    ),
                    "fold_number": integer(
                        observation.get(
                            "fold_number"
                        )
                    ),
                    "trade_return": number(
                        observation.get(
                            "trade_return"
                        )
                    ),
                    "baseline_included": True,
                    "candidate_included": (
                        retained
                    ),
                    "exclusion_reason": (
                        ""
                        if retained
                        else gate_expression
                    ),
                    "execution_instruction": False,
                })

        run_status = (
            "COMPLETED"
            if successful_variant_count > 0
            else "FAILED"
        )

        runs.append({
            "run_id": run_id,
            "experiment_id": experiment_id,
            "research_program_id": (
                program_id
            ),
            "parent_engine_id": (
                engine_id
            ),
            "run_status": run_status,
            "started_at": datetime.now(
                UTC
            ).isoformat(),
            "completed_at": datetime.now(
                UTC
            ).isoformat(),
            "observation_source_path": (
                observation_source_path
            ),
            "baseline_observation_count": (
                len(
                    assigned_observations
                )
            ),
            "declared_variant_count": (
                len(
                    experiment_variants
                )
            ),
            "executed_variant_count": (
                successful_variant_count
            ),
            "fold_count": len(
                fold_plan
            ),
            "uses_future_data": False,
            "overlapping_test_trades": False,
            "changes_engine_code": False,
            "changes_portfolio": False,
            "changes_program_status": False,
            "execution_instruction": False,
            "implementation_authorized": False,
            "production_eligible": False,
            "state_hash": state_hash,
        })

        completed_results = [
            row
            for row in variant_results
            if row[
                "run_id"
            ] == run_id
        ]

        passing_variants = sum(
            bool(
                row[
                    "acceptance_passed"
                ]
            )
            for row in completed_results
        )

        evidence_summaries.append({
            "run_id": run_id,
            "experiment_id": (
                experiment_id
            ),
            "research_program_id": (
                program_id
            ),
            "executed_variant_count": (
                successful_variant_count
            ),
            "passing_variant_count": (
                passing_variants
            ),
            "best_variant_id": (
                best_variant_id(
                    completed_results
                )
            ),
            "evidence_status": (
                "CANDIDATE_PASSING"
                if passing_variants > 0
                else "NO_CANDIDATE_PASSED"
            ),
            "program_transition_recommended": (
                "VALIDATING"
                if successful_variant_count > 0
                else "NO_TRANSITION"
            ),
            "program_transition_authorized": False,
            "execution_instruction": False,
        })

    return {
        "runs": pd.DataFrame(
            runs
        ),
        "fold_results": pd.DataFrame(
            fold_results
        ),
        "variant_results": pd.DataFrame(
            variant_results
        ),
        "trade_comparison": pd.DataFrame(
            trade_comparison
        ),
        "acceptance_results": pd.DataFrame(
            acceptance_results
        ),
        "exclusions": pd.DataFrame(
            exclusions
        ),
        "validation": pd.DataFrame(
            validations
        ),
        "evidence_summary": pd.DataFrame(
            evidence_summaries
        ),
    }


def validate_frozen_design(
    *,
    experiment_id: str,
    validation: pd.DataFrame,
) -> bool:
    applicable = filter_frame(
        validation,
        "experiment_id",
        experiment_id,
    )

    if applicable.empty:
        return False

    required = applicable[
        applicable[
            "check_id"
        ].astype(str).isin(
            REQUIRED_DESIGN_CHECKS
        )
    ]

    if (
        set(
            required[
                "check_id"
            ].astype(str)
        )
        != REQUIRED_DESIGN_CHECKS
    ):
        return False

    return bool(
        required[
            "passed"
        ].astype(bool).all()
    )


def best_variant_id(
    rows: list[dict],
) -> str:
    if not rows:
        return ""

    ordered = sorted(
        rows,
        key=lambda row: (
            bool(
                row.get(
                    "acceptance_passed"
                )
            ),
            number(
                row.get(
                    "mean_return_advantage"
                )
            ),
            number(
                row.get(
                    "sharpe_advantage"
                )
            ),
        ),
        reverse=True,
    )

    return text(
        ordered[0].get(
            "experiment_variant_id"
        )
    )


def exclusion_row(
    *,
    program_id: str,
    experiment_id: str,
    reason_code: str,
    reason: str,
) -> dict:
    return {
        "exclusion_id": stable_id(
            "REXEXC",
            {
                "program_id": program_id,
                "experiment_id": experiment_id,
                "reason_code": reason_code,
                "reason": reason,
            },
        ),
        "research_program_id": (
            program_id
        ),
        "experiment_id": (
            experiment_id
        ),
        "experiment_variant_id": "",
        "reason_code": reason_code,
        "reason": reason,
        "execution_instruction": False,
    }


def filter_frame(
    frame: pd.DataFrame,
    column: str,
    value: str,
) -> pd.DataFrame:
    if (
        frame is None
        or frame.empty
        or column not in frame.columns
    ):
        return pd.DataFrame()

    return frame[
        frame[
            column
        ].astype(str).eq(
            value
        )
    ].copy()


def empty_bundle() -> dict[str, pd.DataFrame]:
    return {
        "runs": pd.DataFrame(),
        "fold_results": pd.DataFrame(),
        "variant_results": pd.DataFrame(),
        "trade_comparison": pd.DataFrame(),
        "acceptance_results": pd.DataFrame(),
        "exclusions": pd.DataFrame(),
        "validation": pd.DataFrame(),
        "evidence_summary": pd.DataFrame(),
    }
