"""Detailed engineering artifacts for implementation plans."""

from __future__ import annotations

import pandas as pd


def build_target_files(
    plans: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for _, plan in plans.iterrows():
        plan_id = plan["plan_id"]

        files = [
            {
                "file_role": (
                    "PARENT_ENGINE_REFERENCE"
                ),
                "path": plan[
                    "parent_engine_file"
                ],
                "action": "READ_ONLY_REFERENCE",
                "required": True,
            },
            {
                "file_role": (
                    "VARIANT_IMPLEMENTATION"
                ),
                "path": plan[
                    "variant_module_file"
                ],
                "action": "CREATE",
                "required": True,
            },
            {
                "file_role": (
                    "VARIANT_TEST"
                ),
                "path": plan[
                    "variant_test_file"
                ],
                "action": "CREATE",
                "required": True,
            },
            {
                "file_role": (
                    "VARIANT_REGISTRY"
                ),
                "path": (
                    "src/atlas/investment/"
                    "alpha/engine_variants/"
                    "registry.py"
                ),
                "action": (
                    "UPDATE_RESEARCH_ONLY"
                ),
                "required": True,
            },
            {
                "file_role": (
                    "STABILIZATION_TEST"
                ),
                "path": (
                    "scripts/"
                    "stabilize_atlas_v4.py"
                ),
                "action": "UPDATE",
                "required": True,
            },
        ]

        for file_row in files:
            rows.append({
                "plan_id": plan_id,
                "variant_id": plan[
                    "variant_id"
                ],
                **file_row,
                "automatic_change_allowed": (
                    False
                ),
                "execution_instruction": False,
            })

    return pd.DataFrame(rows)


def build_test_plan(
    plans: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for _, plan in plans.iterrows():
        tests = [
            (
                "PARENT_PARITY",
                "Parent engine outputs remain unchanged.",
            ),
            (
                "GATE_TRUE",
                "Variant allows signals when the gate evaluates true.",
            ),
            (
                "GATE_FALSE",
                "Variant suppresses signals when the gate evaluates false.",
            ),
            (
                "CANONICAL_SCHEMA",
                "Variant emits the canonical alpha signal columns.",
            ),
            (
                "DETERMINISM",
                "Identical inputs produce identical outputs.",
            ),
            (
                "NO_LOOKAHEAD",
                "Variant uses only features available at signal time.",
            ),
            (
                "HISTORICAL_REPRODUCTION",
                "Variant reproduces the validated walk-forward gate.",
            ),
            (
                "NON_OVERLAPPING_TRADES",
                "Historical evaluation remains non-overlapping.",
            ),
            (
                "RESEARCH_ONLY_REGISTRY",
                "Variant cannot enter production registry.",
            ),
            (
                "FULL_STABILIZATION",
                "Atlas stabilization remains green.",
            ),
        ]

        for order, (
            test_type,
            requirement,
        ) in enumerate(
            tests,
            start=1,
        ):
            rows.append({
                "plan_id": plan[
                    "plan_id"
                ],
                "variant_id": plan[
                    "variant_id"
                ],
                "test_order": order,
                "test_type": test_type,
                "requirement": requirement,
                "required": True,
                "status": "NOT_RUN",
                "execution_instruction": False,
            })

    return pd.DataFrame(rows)


def build_acceptance_criteria(
    plans: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for _, plan in plans.iterrows():
        criteria = [
            (
                "SOURCE_ISOLATION",
                "Parent engine source remains unchanged.",
            ),
            (
                "GATE_MATCH",
                "Implemented gate exactly matches the immutable specification.",
            ),
            (
                "SCHEMA_PARITY",
                "Output schema matches canonical alpha-engine schema.",
            ),
            (
                "WALK_FORWARD_PARITY",
                "Implementation reproduces validated fold membership.",
            ),
            (
                "EXPECTANCY_FLOOR",
                "Net mean-return advantage remains positive.",
            ),
            (
                "SHARPE_FLOOR",
                "Net Sharpe advantage remains positive.",
            ),
            (
                "DRAWDOWN_FLOOR",
                "Candidate drawdown is not worse than baseline.",
            ),
            (
                "SAMPLE_RETENTION",
                "Trade retention remains within 5 percentage points of validation.",
            ),
            (
                "NO_PRODUCTION_REGISTRATION",
                "Variant remains excluded from production engine registry.",
            ),
            (
                "MANUAL_RELEASE",
                "A new human approval is required after implementation validation.",
            ),
        ]

        for order, (
            criterion_id,
            criterion,
        ) in enumerate(
            criteria,
            start=1,
        ):
            rows.append({
                "plan_id": plan[
                    "plan_id"
                ],
                "variant_id": plan[
                    "variant_id"
                ],
                "criterion_order": order,
                "criterion_id": (
                    criterion_id
                ),
                "criterion": criterion,
                "required": True,
                "status": "NOT_EVALUATED",
                "execution_instruction": False,
            })

    return pd.DataFrame(rows)


def build_rollback_plan(
    plans: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for _, plan in plans.iterrows():
        steps = [
            (
                "DISABLE_VARIANT",
                "Remove the variant from the research-only variant registry.",
            ),
            (
                "REVERT_VARIANT_COMMIT",
                "Revert the implementation commit without touching the parent engine.",
            ),
            (
                "REMOVE_VARIANT_TEST",
                "Remove only variant-specific tests if the variant is retired.",
            ),
            (
                "RESTORE_STABILIZATION",
                "Confirm the baseline Atlas stabilization suite passes.",
            ),
            (
                "ARCHIVE_PLAN",
                "Mark the implementation plan RETIRED and preserve all evidence.",
            ),
            (
                "RECORD_DECISION",
                "Append a retirement or rejection decision to the manual ledger.",
            ),
        ]

        for order, (
            step_id,
            instruction,
        ) in enumerate(
            steps,
            start=1,
        ):
            rows.append({
                "plan_id": plan[
                    "plan_id"
                ],
                "variant_id": plan[
                    "variant_id"
                ],
                "rollback_order": order,
                "rollback_step": (
                    step_id
                ),
                "instruction": instruction,
                "automatic_execution_allowed": (
                    False
                ),
                "status": "NOT_REQUIRED",
                "execution_instruction": False,
            })

    return pd.DataFrame(rows)


def build_engineering_backlog(
    plans: pd.DataFrame,
) -> pd.DataFrame:
    if plans.empty:
        return pd.DataFrame()

    backlog = plans[
        [
            "plan_id",
            "variant_id",
            "variant_name",
            "parent_engine_id",
            "board_rank",
            "board_score",
            "validation_score",
            "fold_win_rate",
            "candidate_trade_count",
            "gate_expression",
            "parent_engine_file",
            "variant_module_file",
            "variant_test_file",
            "plan_status",
            "engineering_owner",
            "engineering_branch",
            "engineering_commit",
        ]
    ].copy()

    backlog = backlog.sort_values(
        [
            "board_rank",
            "board_score",
            "variant_id",
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)

    backlog.insert(
        0,
        "engineering_rank",
        range(
            1,
            len(backlog) + 1,
        ),
    )

    backlog["engineering_status"] = (
        "AWAITING_ENGINEERING_ASSIGNMENT"
    )

    backlog[
        "implementation_authorized"
    ] = False

    backlog[
        "production_eligible"
    ] = False

    backlog[
        "execution_instruction"
    ] = False

    return backlog
