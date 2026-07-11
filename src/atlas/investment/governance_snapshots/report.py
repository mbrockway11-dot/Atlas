"""Historical Governance Snapshots v1 orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.governance_snapshots.builder import (
    build_context_snapshot,
    build_engine_snapshot,
    captured_now,
    determine_effective_at,
)
from atlas.investment.governance_snapshots.config import (
    CONTEXT_SNAPSHOTS_CSV,
    ENGINE_SNAPSHOTS_CSV,
    MANIFEST_CSV,
    OUTPUT_DIR,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_VERSION,
)
from atlas.investment.governance_snapshots.loader import (
    load_snapshot_inputs,
)
from atlas.investment.governance_snapshots.storage import (
    snapshot_coverage,
    upsert_context_snapshots,
    upsert_engine_snapshots,
)


def build_governance_snapshots_report() -> dict[str, Any]:
    """Capture current real governance state as a dated snapshot."""
    inputs = load_snapshot_inputs()

    effective_at = determine_effective_at(
        inputs["market_features"]
    )

    captured_at = captured_now()

    engine_snapshot = build_engine_snapshot(
        effective_at=effective_at,
        captured_at=captured_at,
        research=inputs[
            "research_decisions"
        ],
        learning=inputs[
            "learning_recommendations"
        ],
        regime=inputs[
            "regime_suitability"
        ],
        fusion=inputs[
            "fusion_modifiers"
        ],
        governance=inputs[
            "ensemble_governance"
        ],
    )

    context_snapshot = build_context_snapshot(
        effective_at=effective_at,
        captured_at=captured_at,
        macro_report=inputs[
            "macro_report"
        ],
        regime_report=inputs[
            "regime_report"
        ],
        fusion_report=inputs[
            "fusion_report"
        ],
    )

    engine_history = upsert_engine_snapshots(
        engine_snapshot,
        ENGINE_SNAPSHOTS_CSV,
    )

    context_history = upsert_context_snapshots(
        context_snapshot,
        CONTEXT_SNAPSHOTS_CSV,
    )

    coverage = snapshot_coverage(
        engine_history
    )

    eligible_count = int(
        engine_snapshot[
            "eligible"
        ].astype(bool).sum()
        if not engine_snapshot.empty
        else 0
    )

    report = {
        "success": bool(
            not engine_snapshot.empty
        ),
        "version": (
            "historical_governance_snapshots_v1"
        ),
        "schema_version": (
            SCHEMA_VERSION
        ),
        "summary": (
            "Historical Governance Snapshots v1 "
            f"captured {len(engine_snapshot)} engine row(s) "
            f"for {effective_at.isoformat()} with "
            f"{eligible_count} eligible engine(s)."
        ),
        "effective_at": (
            effective_at.isoformat()
        ),
        "captured_at": captured_at,
        "current_engine_rows": int(
            len(engine_snapshot)
        ),
        "current_context_rows": int(
            len(context_snapshot)
        ),
        "eligible_engine_count": (
            eligible_count
        ),
        "coverage": coverage,
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "append_only_history": True,
            "idempotent_per_effective_date": True,
            "fabricates_historical_state": False,
            "point_in_time_resolvable": True,
            "deterministic_given_inputs": True,
        },
        "outputs": {
            "engine_snapshots_csv": str(
                ENGINE_SNAPSHOTS_CSV
            ),
            "context_snapshots_csv": str(
                CONTEXT_SNAPSHOTS_CSV
            ),
            "manifest_csv": str(
                MANIFEST_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_manifest(
        report
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(
            report,
            engine_snapshot,
            context_snapshot,
        ),
        encoding="utf-8",
    )

    return report


def write_manifest(
    report: dict,
) -> None:
    row = {
        "effective_at": report[
            "effective_at"
        ],
        "captured_at": report[
            "captured_at"
        ],
        "schema_version": report[
            "schema_version"
        ],
        "engine_rows": report[
            "current_engine_rows"
        ],
        "context_rows": report[
            "current_context_rows"
        ],
        "eligible_engine_count": report[
            "eligible_engine_count"
        ],
        "engine_snapshot_dates": report[
            "coverage"
        ][
            "snapshot_dates"
        ],
        "success": report[
            "success"
        ],
    }

    old = pd.DataFrame()

    if (
        MANIFEST_CSV.exists()
        and MANIFEST_CSV.stat().st_size > 0
    ):
        try:
            old = pd.read_csv(
                MANIFEST_CSV
            )
        except Exception:
            old = pd.DataFrame()

    history = pd.concat(
        [
            old,
            pd.DataFrame([
                row
            ]),
        ],
        ignore_index=True,
    )

    history[
        "effective_at"
    ] = pd.to_datetime(
        history["effective_at"],
        errors="coerce",
        utc=True,
    )

    history = history.sort_values(
        [
            "effective_at",
            "captured_at",
        ],
        kind="stable",
    ).drop_duplicates(
        subset=["effective_at"],
        keep="last",
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    history.to_csv(
        MANIFEST_CSV,
        index=False,
    )


def build_markdown(
    report: dict,
    engines: pd.DataFrame,
    context: pd.DataFrame,
) -> str:
    lines = [
        "# Historical Governance Snapshots v1",
        "",
        report["summary"],
        "",
        "## Coverage",
        "",
        (
            "- Snapshot dates: "
            f"`{report['coverage']['snapshot_dates']}`"
        ),
        (
            "- Engine rows: "
            f"`{report['coverage']['engine_rows']}`"
        ),
        (
            "- First effective date: "
            f"`{report['coverage']['first_effective_at']}`"
        ),
        (
            "- Last effective date: "
            f"`{report['coverage']['last_effective_at']}`"
        ),
        "",
        "## Current Engine Governance",
        "",
    ]

    for _, row in engines.iterrows():
        lines.append(
            "- "
            f"`{row.get('engine_id')}` "
            f"decision=`{row.get('research_decision')}` "
            f"eligible=`{row.get('eligible')}` "
            f"weight=`{row.get('final_governance_weight')}` "
            f"learning=`{row.get('learning_weight_multiplier')}` "
            f"regime=`{row.get('regime_suitability')}` "
            f"fusion=`{row.get('fusion_modifier')}`"
        )

    lines.extend([
        "",
        "## Current Context",
        "",
    ])

    if not context.empty:
        row = context.iloc[0]

        lines.extend([
            (
                "- Macro regime: "
                f"`{row.get('macro_regime')}`"
            ),
            (
                "- Market regime: "
                f"`{row.get('market_regime')}`"
            ),
            (
                "- Fused regime: "
                f"`{row.get('fused_regime')}`"
            ),
            (
                "- Minimum cash weight: "
                f"`{row.get('minimum_cash_weight')}`"
            ),
        ])

    lines.extend([
        "",
        "## Important Limitation",
        "",
        (
            "This system begins capturing real governance state "
            "from installation onward. It does not manufacture "
            "governance snapshots for dates before the capture "
            "system existed."
        ),
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(
            report["contract"],
            indent=2,
        ),
        "```",
        "",
    ])

    return "\n".join(lines)
