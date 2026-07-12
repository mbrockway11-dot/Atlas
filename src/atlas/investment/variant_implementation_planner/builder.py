"""Research variant implementation-plan construction."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime

import pandas as pd

from atlas.investment.variant_implementation_planner.config import (
    DEFAULT_PLAN_STATUS,
    SCHEMA_VERSION,
    SOURCE,
    VERSION,
)
from atlas.investment.variant_implementation_planner.paths import (
    resolve_parent_engine_file,
    resolve_parent_test_file,
)


PLAN_COLUMNS = [
    "plan_id",
    "specification_hash",
    "variant_id",
    "variant_name",
    "hypothesis_id",
    "parent_engine_id",
    "parent_engine_family",
    "gate_mode",
    "feature",
    "target_state",
    "gate_expression",
    "manual_decision",
    "manual_reviewer",
    "manual_rationale",
    "approval_version",
    "board_rank",
    "board_score",
    "validation_score",
    "fold_win_rate",
    "candidate_trade_count",
    "retention_ratio",
    "mean_return_advantage",
    "sharpe_advantage",
    "drawdown_improvement",
    "implementation_strategy",
    "parent_engine_file",
    "variant_module_file",
    "variant_test_file",
    "plan_status",
    "engineering_owner",
    "engineering_branch",
    "engineering_commit",
    "created_at",
    "last_synchronized_at",
    "manual_implementation_required",
    "implementation_authorized",
    "production_eligible",
    "execution_instruction",
    "schema_version",
    "source",
]


def build_implementation_plans(
    implementation_queue: pd.DataFrame,
    decision_ledger: pd.DataFrame,
    variant_registry: pd.DataFrame,
) -> pd.DataFrame:
    """Build one non-executable engineering plan per approved variant."""
    if (
        implementation_queue is None
        or implementation_queue.empty
        or "variant_id"
        not in implementation_queue.columns
    ):
        return pd.DataFrame(
            columns=PLAN_COLUMNS
        )

    ledger_map = index_by_variant(
        decision_ledger
    )

    registry_map = index_by_variant(
        variant_registry
    )

    now = datetime.now(
        UTC
    ).isoformat()

    rows = []

    for _, queue_row in (
        implementation_queue.iterrows()
    ):
        variant_id = text(
            queue_row.get(
                "variant_id"
            )
        )

        ledger_row = ledger_map.get(
            variant_id,
            {},
        )

        registry_row = registry_map.get(
            variant_id,
            {},
        )

        manual_decision = text(
            ledger_row.get(
                "manual_decision",
                "",
            )
        ).upper()

        if manual_decision != "APPROVED":
            continue

        parent_engine_id = text(
            queue_row.get(
                "parent_engine_id",
                registry_row.get(
                    "parent_engine_id",
                    "",
                ),
            )
        )

        variant_name = text(
            queue_row.get(
                "variant_name",
                registry_row.get(
                    "variant_name",
                    "",
                ),
            )
        )

        parent_file = (
            resolve_parent_engine_file(
                parent_engine_id
            )
        )

        variant_module_file = str(
            (
                __import__(
                    "pathlib"
                ).Path(
                    "src/atlas/investment/"
                    "alpha/engine_variants"
                )
                / f"{variant_name}.py"
            )
        )

        variant_test_file = (
            resolve_parent_test_file(
                variant_name
            )
        )

        core = {
            "variant_id": variant_id,
            "variant_name": variant_name,
            "hypothesis_id": text(
                registry_row.get(
                    "hypothesis_id",
                    "",
                )
            ),
            "parent_engine_id": (
                parent_engine_id
            ),
            "parent_engine_family": text(
                registry_row.get(
                    "parent_engine_family",
                    "",
                )
            ),
            "gate_mode": text(
                registry_row.get(
                    "gate_mode",
                    "",
                )
            ),
            "feature": text(
                registry_row.get(
                    "feature",
                    "",
                )
            ),
            "target_state": text(
                registry_row.get(
                    "target_state",
                    "",
                )
            ),
            "gate_expression": text(
                queue_row.get(
                    "gate_expression",
                    registry_row.get(
                        "gate_expression",
                        "",
                    ),
                )
            ),
            "manual_decision": (
                manual_decision
            ),
            "manual_reviewer": text(
                ledger_row.get(
                    "manual_reviewer",
                    "",
                )
            ),
            "manual_rationale": text(
                ledger_row.get(
                    "manual_rationale",
                    "",
                )
            ),
            "approval_version": text(
                ledger_row.get(
                    "approval_version",
                    "",
                )
            ),
            "board_rank": integer(
                queue_row.get(
                    "board_rank"
                )
            ),
            "board_score": number(
                queue_row.get(
                    "board_score"
                )
            ),
            "validation_score": number(
                queue_row.get(
                    "validation_score"
                )
            ),
            "fold_win_rate": number(
                queue_row.get(
                    "fold_win_rate"
                )
            ),
            "candidate_trade_count": integer(
                queue_row.get(
                    "candidate_trade_count"
                )
            ),
            "retention_ratio": number(
                queue_row.get(
                    "retention_ratio"
                )
            ),
            "mean_return_advantage": number(
                queue_row.get(
                    "mean_return_advantage"
                )
            ),
            "sharpe_advantage": number(
                queue_row.get(
                    "sharpe_advantage"
                )
            ),
            "drawdown_improvement": number(
                queue_row.get(
                    "drawdown_improvement"
                )
            ),
            "implementation_strategy": (
                "CREATE_RESEARCH_ONLY_WRAPPER"
            ),
            "parent_engine_file": (
                parent_file
            ),
            "variant_module_file": (
                variant_module_file
            ),
            "variant_test_file": (
                variant_test_file
            ),
            "plan_status": (
                DEFAULT_PLAN_STATUS
            ),
            "engineering_owner": "",
            "engineering_branch": "",
            "engineering_commit": "",
            "manual_implementation_required": (
                True
            ),
            "implementation_authorized": (
                False
            ),
            "production_eligible": False,
            "execution_instruction": False,
            "schema_version": (
                SCHEMA_VERSION
            ),
            "source": SOURCE,
        }

        specification_hash = hash_plan(
            core
        )

        rows.append({
            "plan_id": build_plan_id(
                variant_id
            ),
            "specification_hash": (
                specification_hash
            ),
            **core,
            "created_at": now,
            "last_synchronized_at": now,
        })

    return pd.DataFrame(
        rows,
        columns=PLAN_COLUMNS,
    ).sort_values(
        [
            "board_rank",
            "variant_id",
        ],
        kind="stable",
    ).reset_index(drop=True)


def index_by_variant(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "variant_id" not in frame.columns
    ):
        return {}

    return {
        text(
            row["variant_id"]
        ): row.to_dict()
        for _, row in frame.iterrows()
    }


def build_plan_id(
    variant_id: str,
) -> str:
    digest = hashlib.sha256(
        (
            f"{VERSION}|{variant_id}"
        ).encode("utf-8")
    ).hexdigest()[:16]

    return f"PLAN-{digest}"


def hash_plan(
    payload: dict,
) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def number(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )


def integer(
    value,
    *,
    default: int = 0,
) -> int:
    try:
        return int(
            float(value)
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def text(
    value,
) -> str:
    if value is None:
        return ""

    if (
        isinstance(value, float)
        and math.isnan(value)
    ):
        return ""

    return str(value)
