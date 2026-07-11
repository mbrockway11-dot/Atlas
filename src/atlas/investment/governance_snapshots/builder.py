"""Historical Governance Snapshots v1 construction."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime

import pandas as pd

from atlas.investment.governance_snapshots.config import (
    SCHEMA_VERSION,
    SOURCE,
)


ENGINE_COLUMNS = [
    "effective_at",
    "captured_at",
    "snapshot_id",
    "schema_version",
    "engine_id",
    "family",
    "research_decision",
    "research_eligible",
    "promotion_score",
    "hard_failures",
    "learning_recommendation",
    "learning_reliability",
    "learning_weight_multiplier",
    "market_regime",
    "regime_confidence",
    "regime_suitability",
    "fused_regime",
    "fusion_confidence",
    "fusion_modifier",
    "base_governance_weight",
    "diversification_modifier",
    "combined_modifier",
    "final_governance_weight",
    "eligible",
    "source",
]


CONTEXT_COLUMNS = [
    "effective_at",
    "captured_at",
    "snapshot_id",
    "schema_version",
    "macro_regime",
    "macro_confidence",
    "macro_risk_pressure",
    "macro_liquidity_support",
    "market_regime",
    "primary_market_regime",
    "market_regime_confidence",
    "market_stability",
    "fused_regime",
    "fusion_confidence",
    "unified_risk_score",
    "unified_support_score",
    "risk_budget_multiplier",
    "minimum_cash_weight",
    "conviction_ceiling",
    "volatility_target_multiplier",
    "turnover_multiplier",
    "source",
]


def determine_effective_at(
    market_features: pd.DataFrame,
) -> pd.Timestamp:
    """Use latest canonical market date as snapshot effective time."""
    if (
        market_features is not None
        and not market_features.empty
    ):
        for column in [
            "timestamp",
            "date",
            "datetime",
            "time",
        ]:
            if column in market_features.columns:
                values = pd.to_datetime(
                    market_features[column],
                    errors="coerce",
                    utc=True,
                ).dropna()

                if not values.empty:
                    return values.max().normalize()

    return pd.Timestamp.now(
        tz="UTC"
    ).normalize()


def build_engine_snapshot(
    *,
    effective_at: pd.Timestamp,
    captured_at: str,
    research: pd.DataFrame,
    learning: pd.DataFrame,
    regime: pd.DataFrame,
    fusion: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    """Build one dated row per engine from canonical layers."""
    engine_ids: set[str] = set()

    for frame in [
        research,
        learning,
        regime,
        fusion,
        governance,
    ]:
        if (
            frame is not None
            and not frame.empty
            and "engine_id" in frame.columns
        ):
            engine_ids.update(
                frame[
                    "engine_id"
                ].dropna().astype(str)
            )

    if not engine_ids:
        return pd.DataFrame(
            columns=ENGINE_COLUMNS
        )

    research_map = index_rows(
        research
    )
    learning_map = index_rows(
        learning
    )
    regime_map = index_rows(
        regime
    )
    fusion_map = index_rows(
        fusion
    )
    governance_map = index_rows(
        governance
    )

    rows = []

    for engine_id in sorted(
        engine_ids
    ):
        research_row = research_map.get(
            engine_id,
            {},
        )
        learning_row = learning_map.get(
            engine_id,
            {},
        )
        regime_row = regime_map.get(
            engine_id,
            {},
        )
        fusion_row = fusion_map.get(
            engine_id,
            {},
        )
        governance_row = governance_map.get(
            engine_id,
            {},
        )

        decision = text(
            governance_row.get(
                "decision",
                research_row.get(
                    "decision",
                    "UNKNOWN",
                ),
            )
        ).upper()

        hard_failures = text(
            governance_row.get(
                "hard_failures",
                research_row.get(
                    "hard_failures",
                    "",
                ),
            )
        )

        eligible = boolean(
            governance_row.get(
                "eligible",
                decision in {
                    "PROMOTE",
                    "KEEP",
                }
                and not hard_failures,
            )
        )

        row = {
            "effective_at": (
                effective_at.isoformat()
            ),
            "captured_at": captured_at,
            "schema_version": (
                SCHEMA_VERSION
            ),
            "engine_id": engine_id,
            "family": text(
                governance_row.get(
                    "family",
                    research_row.get(
                        "family",
                        "unknown",
                    ),
                )
            ),
            "research_decision": (
                decision
            ),
            "research_eligible": (
                decision
                in {
                    "PROMOTE",
                    "KEEP",
                }
                and not hard_failures
            ),
            "promotion_score": number(
                research_row.get(
                    "promotion_score",
                    governance_row.get(
                        "promotion_score"
                    ),
                )
            ),
            "hard_failures": (
                hard_failures
            ),
            "learning_recommendation": text(
                learning_row.get(
                    "recommendation",
                    "",
                )
            ),
            "learning_reliability": number(
                learning_row.get(
                    "reliability"
                )
            ),
            "learning_weight_multiplier": number(
                learning_row.get(
                    "learning_weight_multiplier",
                    1.0,
                ),
                default=1.0,
            ),
            "market_regime": text(
                regime_row.get(
                    "market_regime",
                    "UNKNOWN",
                )
            ),
            "regime_confidence": number(
                regime_row.get(
                    "regime_confidence"
                )
            ),
            "regime_suitability": number(
                regime_row.get(
                    "effective_suitability"
                )
            ),
            "fused_regime": text(
                fusion_row.get(
                    "fused_regime",
                    "UNKNOWN",
                )
            ),
            "fusion_confidence": number(
                fusion_row.get(
                    "fusion_confidence"
                )
            ),
            "fusion_modifier": number(
                fusion_row.get(
                    "effective_context_modifier",
                    1.0,
                ),
                default=1.0,
            ),
            "base_governance_weight": number(
                governance_row.get(
                    "base_governance_weight"
                )
            ),
            "diversification_modifier": number(
                governance_row.get(
                    "diversification_modifier",
                    1.0,
                ),
                default=1.0,
            ),
            "combined_modifier": number(
                governance_row.get(
                    "combined_modifier",
                    1.0,
                ),
                default=1.0,
            ),
            "final_governance_weight": number(
                governance_row.get(
                    "governance_weight"
                )
            ),
            "eligible": eligible,
            "source": SOURCE,
        }

        row["snapshot_id"] = (
            fingerprint(row)
        )

        rows.append(row)

    return pd.DataFrame(
        rows,
        columns=ENGINE_COLUMNS,
    )


def build_context_snapshot(
    *,
    effective_at: pd.Timestamp,
    captured_at: str,
    macro_report: dict,
    regime_report: dict,
    fusion_report: dict,
) -> pd.DataFrame:
    """Build one global market-context snapshot."""
    macro = (
        macro_report.get(
            "macro_environment",
            {},
        )
        or {}
    )

    regime = (
        regime_report.get(
            "regime",
            {},
        )
        or {}
    )

    fusion = (
        fusion_report.get(
            "fused_context",
            {},
        )
        or {}
    )

    controls = (
        fusion.get(
            "controls",
            {},
        )
        or {}
    )

    row = {
        "effective_at": (
            effective_at.isoformat()
        ),
        "captured_at": captured_at,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "macro_regime": text(
            macro.get(
                "macro_regime",
                "UNKNOWN",
            )
        ),
        "macro_confidence": number(
            macro.get("confidence")
        ),
        "macro_risk_pressure": number(
            macro.get(
                "risk_pressure"
            )
        ),
        "macro_liquidity_support": number(
            macro.get(
                "liquidity_support"
            )
        ),
        "market_regime": text(
            regime.get(
                "regime",
                "UNKNOWN",
            )
        ),
        "primary_market_regime": text(
            regime.get(
                "primary_regime",
                "UNKNOWN",
            )
        ),
        "market_regime_confidence": number(
            regime.get("confidence")
        ),
        "market_stability": number(
            regime.get(
                "stability_score"
            )
        ),
        "fused_regime": text(
            fusion.get(
                "fused_regime",
                "UNKNOWN",
            )
        ),
        "fusion_confidence": number(
            fusion.get("confidence")
        ),
        "unified_risk_score": number(
            fusion.get(
                "unified_risk_score"
            )
        ),
        "unified_support_score": number(
            fusion.get(
                "unified_support_score"
            )
        ),
        "risk_budget_multiplier": number(
            controls.get(
                "risk_budget_multiplier",
                1.0,
            ),
            default=1.0,
        ),
        "minimum_cash_weight": number(
            controls.get(
                "minimum_cash_weight"
            )
        ),
        "conviction_ceiling": number(
            controls.get(
                "conviction_ceiling",
                1.0,
            ),
            default=1.0,
        ),
        "volatility_target_multiplier": number(
            controls.get(
                "volatility_target_multiplier",
                1.0,
            ),
            default=1.0,
        ),
        "turnover_multiplier": number(
            controls.get(
                "turnover_multiplier",
                1.0,
            ),
            default=1.0,
        ),
        "source": SOURCE,
    }

    row["snapshot_id"] = fingerprint(
        row
    )

    return pd.DataFrame(
        [row],
        columns=CONTEXT_COLUMNS,
    )


def index_rows(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "engine_id" not in frame.columns
    ):
        return {}

    return {
        str(
            row["engine_id"]
        ): row.to_dict()
        for _, row in frame.iterrows()
    }


def fingerprint(
    row: dict,
) -> str:
    payload = {
        key: value
        for key, value in row.items()
        if key not in {
            "snapshot_id",
            "captured_at",
        }
    }

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


def text(
    value,
) -> str:
    if value is None:
        return ""

    return str(value)


def boolean(
    value,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
        return value

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
    }


def captured_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()
