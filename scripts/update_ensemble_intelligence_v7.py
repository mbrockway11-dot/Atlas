"""Run and audit Ensemble Intelligence v7."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.alpha_ensemble.contributions import (
    build_contribution_ledger,
)
from atlas.investment.alpha_ensemble.governance import (
    build_engine_governance,
)
from atlas.investment.alpha_ensemble.loader import (
    load_alpha_ensemble_inputs,
)
from atlas.investment.alpha_ensemble.report import (
    build_alpha_ensemble_report,
)


OUT_DIR = Path(
    "output/investment_alpha_ensemble"
)

GOVERNANCE_CSV = (
    OUT_DIR
    / "ensemble_v7_engine_governance.csv"
)

CONTRIBUTIONS_CSV = (
    OUT_DIR
    / "ensemble_v7_contribution_ledger.csv"
)

AUDIT_JSON = (
    OUT_DIR
    / "ensemble_v7_audit.json"
)

AUDIT_MD = (
    OUT_DIR
    / "ensemble_v7_audit.md"
)


def main() -> None:
    inputs = load_alpha_ensemble_inputs()

    governance = build_engine_governance(
        inputs.get("research_decisions"),
        learning_recommendations=inputs.get(
            "engine_learning_recommendations"
        ),
        regime_suitability=inputs.get(
            "engine_regime_suitability"
        ),
        context_modifiers=inputs.get(
            "engine_context_modifiers"
        ),
    )

    contributions = build_contribution_ledger(
        inputs.get(
            "alpha_engine_signals"
        ),
        governance,
    )

    ensemble = build_alpha_ensemble_report()

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    governance.to_csv(
        GOVERNANCE_CSV,
        index=False,
    )

    contributions.to_csv(
        CONTRIBUTIONS_CSV,
        index=False,
    )

    eligible = governance[
        governance["eligible"]
    ]

    audit = {
        "success": bool(
            ensemble.get(
                "success",
                False,
            )
        ),
        "version": (
            "ensemble_intelligence_v7"
        ),
        "summary": (
            "Ensemble Intelligence v7 evaluated "
            f"{len(governance)} engine(s), admitted "
            f"{len(eligible)}, and produced "
            f"{len(contributions)} contribution row(s)."
        ),
        "counts": {
            "engine_rows": len(
                governance
            ),
            "eligible_engines": len(
                eligible
            ),
            "contribution_rows": len(
                contributions
            ),
            "contribution_assets": (
                contributions[
                    "asset"
                ].nunique()
                if not contributions.empty
                else 0
            ),
        },
        "governance_weight_total": round(
            float(
                eligible[
                    "governance_weight"
                ].sum()
            ),
            8,
        ),
        "fused_context": (
            inputs.get(
                "macro_regime_fusion",
                {},
            )
            or {}
        ).get(
            "fused_context",
            {},
        ),
        "contract": {
            "research_lab_admission_gate": True,
            "learning_bounded": True,
            "regime_bounded": True,
            "macro_regime_fusion_bounded": True,
            "diversification_aware": True,
            "contribution_ledger": True,
            "execution_instruction": False,
        },
        "outputs": {
            "governance_csv": str(
                GOVERNANCE_CSV
            ),
            "contributions_csv": str(
                CONTRIBUTIONS_CSV
            ),
            "audit_json": str(
                AUDIT_JSON
            ),
            "audit_markdown": str(
                AUDIT_MD
            ),
        },
    }

    AUDIT_JSON.write_text(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    AUDIT_MD.write_text(
        build_markdown(
            audit,
            governance,
            contributions,
        ),
        encoding="utf-8",
    )

    print(audit["success"])
    print(audit["summary"])
    print(
        "Governance weight total:",
        audit[
            "governance_weight_total"
        ],
    )

    print("Eligible governance:")

    for _, row in eligible.iterrows():
        print({
            "engine_id": row.get(
                "engine_id"
            ),
            "decision": row.get(
                "decision"
            ),
            "base": row.get(
                "base_governance_weight"
            ),
            "learning": row.get(
                "learning_modifier"
            ),
            "regime": row.get(
                "regime_modifier"
            ),
            "fusion": row.get(
                "fusion_modifier"
            ),
            "diversification": row.get(
                "diversification_modifier"
            ),
            "final": row.get(
                "governance_weight"
            ),
        })

    print("Outputs:")

    for name, path in audit[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


def build_markdown(
    audit: dict,
    governance,
    contributions,
) -> str:
    lines = [
        "# Ensemble Intelligence v7",
        "",
        audit["summary"],
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(
            audit["contract"],
            indent=2,
        ),
        "```",
        "",
        "## Eligible Engine Governance",
        "",
    ]

    for _, row in governance[
        governance["eligible"]
    ].iterrows():
        lines.append(
            "- "
            f"`{row.get('engine_id')}` "
            f"decision=`{row.get('decision')}` "
            f"weight=`{row.get('governance_weight')}` "
            f"learning=`{row.get('learning_modifier')}` "
            f"regime=`{row.get('regime_modifier')}` "
            f"fusion=`{row.get('fusion_modifier')}` "
            f"diversification="
            f"`{row.get('diversification_modifier')}`"
        )

    lines.extend([
        "",
        "## Top Asset Contributions",
        "",
    ])

    if not contributions.empty:
        for asset, group in contributions.groupby(
            "asset",
            sort=True,
        ):
            lines.append(
                f"### {asset}"
            )
            lines.append("")

            for _, row in group.head(5).iterrows():
                lines.append(
                    "- "
                    f"`{row.get('engine_id')}` "
                    f"weighted="
                    f"`{row.get('weighted_contribution')}` "
                    f"share="
                    f"`{row.get('contribution_share')}` "
                    f"direction="
                    f"`{row.get('direction')}`"
                )

            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
