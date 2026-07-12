"""Validated Variant Registry v1 orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.validated_variants.builder import (
    build_variant_specifications,
)
from atlas.investment.validated_variants.config import (
    CONFLICTS_CSV,
    MANIFEST_CSV,
    OUTPUT_DIR,
    REGISTRY_CSV,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_VERSION,
    SPECIFICATIONS_JSONL,
    VERSION,
)
from atlas.investment.validated_variants.loader import (
    load_variant_registry_inputs,
)
from atlas.investment.validated_variants.storage import (
    merge_registry,
    write_jsonl,
)


def build_validated_variant_registry_report() -> dict[str, Any]:
    """Build and persist immutable validated variant specifications."""
    inputs = load_variant_registry_inputs()

    incoming = build_variant_specifications(
        inputs["validated_hypotheses"],
        inputs["hypothesis_library"],
    )

    registry, conflicts, merge_stats = (
        merge_registry(
            incoming=incoming,
            existing_path=REGISTRY_CSV,
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    registry.to_csv(
        REGISTRY_CSV,
        index=False,
    )

    conflicts.to_csv(
        CONFLICTS_CSV,
        index=False,
    )

    write_jsonl(
        registry,
        SPECIFICATIONS_JSONL,
    )

    generated_at = datetime.now(
        UTC
    ).isoformat()

    report = {
        "success": bool(
            not registry.empty
            and conflicts.empty
        ),
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": generated_at,
        "summary": (
            "Validated Variant Registry v1 contains "
            f"{len(registry)} immutable research "
            f"variant specification(s), inserted "
            f"{merge_stats['inserted_rows']} new "
            f"record(s), and detected "
            f"{len(conflicts)} conflict(s)."
        ),
        "counts": {
            "validated_input_rows": int(
                len(
                    inputs[
                        "validated_hypotheses"
                    ]
                )
            ),
            "incoming_specifications": int(
                len(incoming)
            ),
            "registry_rows": int(
                len(registry)
            ),
            "conflict_rows": int(
                len(conflicts)
            ),
            **merge_stats,
        },
        "variants": (
            registry.to_dict(
                orient="records"
            )
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "immutable_specifications": True,
            "existing_specs_can_be_overwritten": False,
            "changes_engine_code": False,
            "changes_engine_registry": False,
            "changes_research_governance": False,
            "changes_ensemble_weights": False,
            "production_activation": False,
            "manual_review_required": True,
            "manual_implementation_required": True,
            "deterministic_variant_ids": True,
        },
        "outputs": {
            "registry_csv": str(
                REGISTRY_CSV
            ),
            "specifications_jsonl": str(
                SPECIFICATIONS_JSONL
            ),
            "manifest_csv": str(
                MANIFEST_CSV
            ),
            "conflicts_csv": str(
                CONFLICTS_CSV
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
            report
        ),
        encoding="utf-8",
    )

    return report


def write_manifest(
    report: dict,
) -> None:
    row = {
        "generated_at": report[
            "generated_at"
        ],
        "version": report[
            "version"
        ],
        "schema_version": report[
            "schema_version"
        ],
        "registry_rows": report[
            "counts"
        ][
            "registry_rows"
        ],
        "inserted_rows": report[
            "counts"
        ][
            "inserted_rows"
        ],
        "unchanged_rows": report[
            "counts"
        ][
            "unchanged_rows"
        ],
        "conflict_rows": report[
            "counts"
        ][
            "conflict_rows"
        ],
        "success": report[
            "success"
        ],
    }

    existing = pd.DataFrame()

    if (
        MANIFEST_CSV.exists()
        and MANIFEST_CSV.stat().st_size > 0
    ):
        try:
            existing = pd.read_csv(
                MANIFEST_CSV
            )
        except Exception:
            existing = pd.DataFrame()

    manifest = pd.concat(
        [
            existing,
            pd.DataFrame([
                row
            ]),
        ],
        ignore_index=True,
    )

    manifest.to_csv(
        MANIFEST_CSV,
        index=False,
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Validated Variant Registry v1",
        "",
        report["summary"],
        "",
        "## Registered Variants",
        "",
    ]

    for variant in report.get(
        "variants",
        [],
    ):
        lines.extend([
            (
                f"### {variant.get('variant_id')}"
            ),
            "",
            (
                f"- Name: "
                f"`{variant.get('variant_name')}`"
            ),
            (
                f"- Parent engine: "
                f"`{variant.get('parent_engine_id')}`"
            ),
            (
                f"- Hypothesis: "
                f"`{variant.get('hypothesis_id')}`"
            ),
            (
                f"- Gate mode: "
                f"`{variant.get('gate_mode')}`"
            ),
            (
                f"- Gate expression: "
                f"`{variant.get('gate_expression')}`"
            ),
            (
                f"- Validation score: "
                f"`{variant.get('validation_score')}`"
            ),
            (
                f"- Fold win rate: "
                f"`{variant.get('fold_win_rate')}`"
            ),
            (
                f"- Trade retention: "
                f"`{variant.get('retention_ratio')}`"
            ),
            (
                f"- Review status: "
                f"`{variant.get('review_status')}`"
            ),
            (
                f"- Implementation: "
                f"`{variant.get('implementation_status')}`"
            ),
            (
                f"- Production status: "
                f"`{variant.get('production_status')}`"
            ),
            "",
        ])

    lines.extend([
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
