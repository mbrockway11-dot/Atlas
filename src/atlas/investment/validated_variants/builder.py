"""Validated variant specification construction."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime

import pandas as pd

from atlas.investment.validated_variants.config import (
    IMPLEMENTATION_STATUS,
    PRODUCTION_STATUS,
    RESEARCH_STATUS,
    REVIEW_STATUS,
    SCHEMA_VERSION,
    SUPPORTED_HYPOTHESIS_TYPES,
    VALID_DECISION,
    VERSION,
)


REGISTRY_COLUMNS = [
    "variant_id",
    "specification_hash",
    "schema_version",
    "registry_version",
    "hypothesis_id",
    "hypothesis_type",
    "parent_engine_id",
    "parent_engine_family",
    "variant_name",
    "gate_mode",
    "feature",
    "target_state",
    "gate_expression",
    "research_status",
    "review_status",
    "implementation_status",
    "production_status",
    "validation_score",
    "valid_fold_count",
    "baseline_trade_count",
    "candidate_trade_count",
    "retention_ratio",
    "fold_win_rate",
    "mean_return_advantage",
    "profit_factor_advantage",
    "sharpe_advantage",
    "drawdown_improvement",
    "conditions_passed",
    "hard_failures",
    "thesis",
    "proposed_test",
    "validation_requirement",
    "created_at",
    "last_observed_at",
    "immutable",
    "manual_approval_required",
    "execution_instruction",
    "source",
]


def build_variant_specifications(
    validated: pd.DataFrame,
    hypothesis_library: pd.DataFrame,
) -> pd.DataFrame:
    """Convert validated hypotheses into immutable specifications."""
    if validated is None or validated.empty:
        return pd.DataFrame(
            columns=REGISTRY_COLUMNS
        )

    required = {
        "hypothesis_id",
        "hypothesis_type",
        "engine_id",
        "feature",
        "state",
        "decision",
    }

    if not required.issubset(
        validated.columns
    ):
        return pd.DataFrame(
            columns=REGISTRY_COLUMNS
        )

    frame = validated.copy()

    frame["decision"] = (
        frame["decision"]
        .astype(str)
        .str.upper()
    )

    frame["hypothesis_type"] = (
        frame["hypothesis_type"]
        .astype(str)
        .str.upper()
    )

    frame = frame[
        frame["decision"].eq(
            VALID_DECISION
        )
        & frame[
            "hypothesis_type"
        ].isin(
            SUPPORTED_HYPOTHESIS_TYPES
        )
    ]

    if frame.empty:
        return pd.DataFrame(
            columns=REGISTRY_COLUMNS
        )

    library_map = build_library_map(
        hypothesis_library
    )

    observed_at = datetime.now(
        UTC
    ).isoformat()

    rows = []

    for _, row in frame.iterrows():
        hypothesis_id = text(
            row.get("hypothesis_id")
        )

        hypothesis_type = text(
            row.get("hypothesis_type")
        ).upper()

        engine_id = text(
            row.get("engine_id")
        )

        family = text(
            row.get(
                "family",
                "unknown",
            )
        )

        feature = text(
            row.get("feature")
        )

        state = text(
            row.get("state")
        ).upper()

        library_row = library_map.get(
            hypothesis_id,
            {},
        )

        gate_mode = determine_gate_mode(
            hypothesis_type
        )

        gate_expression = build_gate_expression(
            feature=feature,
            state=state,
            gate_mode=gate_mode,
        )

        variant_id = build_variant_id(
            parent_engine_id=engine_id,
            hypothesis_type=hypothesis_type,
            feature=feature,
            state=state,
        )

        specification_core = {
            "variant_id": variant_id,
            "schema_version": SCHEMA_VERSION,
            "registry_version": VERSION,
            "hypothesis_id": hypothesis_id,
            "hypothesis_type": hypothesis_type,
            "parent_engine_id": engine_id,
            "parent_engine_family": family,
            "variant_name": build_variant_name(
                engine_id=engine_id,
                gate_mode=gate_mode,
                feature=feature,
                state=state,
            ),
            "gate_mode": gate_mode,
            "feature": feature,
            "target_state": state,
            "gate_expression": gate_expression,
            "research_status": RESEARCH_STATUS,
            "review_status": REVIEW_STATUS,
            "implementation_status": (
                IMPLEMENTATION_STATUS
            ),
            "production_status": (
                PRODUCTION_STATUS
            ),
            "validation_score": number(
                row.get(
                    "validation_score"
                )
            ),
            "valid_fold_count": integer(
                row.get(
                    "valid_fold_count"
                )
            ),
            "baseline_trade_count": integer(
                row.get(
                    "baseline_trade_count"
                )
            ),
            "candidate_trade_count": integer(
                row.get(
                    "candidate_trade_count"
                )
            ),
            "retention_ratio": number(
                row.get(
                    "retention_ratio"
                )
            ),
            "fold_win_rate": number(
                row.get(
                    "fold_win_rate"
                )
            ),
            "mean_return_advantage": number(
                row.get(
                    "mean_return_advantage"
                )
            ),
            "profit_factor_advantage": number(
                row.get(
                    "profit_factor_advantage"
                )
            ),
            "sharpe_advantage": number(
                row.get(
                    "sharpe_advantage"
                )
            ),
            "drawdown_improvement": number(
                row.get(
                    "drawdown_improvement"
                )
            ),
            "conditions_passed": text(
                row.get(
                    "conditions_passed"
                )
            ),
            "hard_failures": text(
                row.get(
                    "hard_failures"
                )
            ),
            "thesis": text(
                library_row.get(
                    "thesis",
                    "",
                )
            ),
            "proposed_test": text(
                library_row.get(
                    "proposed_test",
                    "",
                )
            ),
            "validation_requirement": text(
                library_row.get(
                    "validation_requirement",
                    "",
                )
            ),
            "immutable": True,
            "manual_approval_required": True,
            "execution_instruction": False,
            "source": VERSION,
        }

        specification_hash = hash_specification(
            specification_core
        )

        rows.append({
            **specification_core,
            "specification_hash": (
                specification_hash
            ),
            "created_at": observed_at,
            "last_observed_at": observed_at,
        })

    return pd.DataFrame(
        rows,
        columns=REGISTRY_COLUMNS,
    ).sort_values(
        [
            "parent_engine_id",
            "feature",
            "target_state",
            "variant_id",
        ],
        kind="stable",
    ).reset_index(drop=True)


def determine_gate_mode(
    hypothesis_type: str,
) -> str:
    if (
        hypothesis_type
        == "FAILURE_MODE_GATE"
    ):
        return "EXCLUDE_WHEN"

    if (
        hypothesis_type
        == "CONDITIONAL_OPPORTUNITY"
    ):
        return "INCLUDE_ONLY_WHEN"

    return "UNSUPPORTED"


def build_gate_expression(
    *,
    feature: str,
    state: str,
    gate_mode: str,
) -> str:
    if gate_mode == "EXCLUDE_WHEN":
        return (
            f"ALLOW_SIGNAL = "
            f"NOT ({feature} == {state!r})"
        )

    if gate_mode == "INCLUDE_ONLY_WHEN":
        return (
            f"ALLOW_SIGNAL = "
            f"({feature} == {state!r})"
        )

    return "ALLOW_SIGNAL = FALSE"


def build_variant_id(
    *,
    parent_engine_id: str,
    hypothesis_type: str,
    feature: str,
    state: str,
) -> str:
    payload = "|".join([
        parent_engine_id,
        hypothesis_type,
        feature,
        state,
    ])

    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]

    return f"VAR-{digest}"


def build_variant_name(
    *,
    engine_id: str,
    gate_mode: str,
    feature: str,
    state: str,
) -> str:
    cleaned_engine = (
        engine_id.replace(
            "_v1",
            "",
        )
    )

    mode = (
        "exclude"
        if gate_mode
        == "EXCLUDE_WHEN"
        else "only"
    )

    return (
        f"{cleaned_engine}__"
        f"{mode}__"
        f"{feature}__"
        f"{state.lower()}__v1"
    )


def hash_specification(
    specification: dict,
) -> str:
    payload = json.dumps(
        specification,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


def build_library_map(
    library: pd.DataFrame,
) -> dict[str, dict]:
    if (
        library is None
        or library.empty
        or "hypothesis_id"
        not in library.columns
    ):
        return {}

    return {
        text(
            row["hypothesis_id"]
        ): row.to_dict()
        for _, row in library.iterrows()
    }


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
