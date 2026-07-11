"""Run Macro-Regime Fusion v1."""

from __future__ import annotations

from atlas.investment.macro_regime_fusion import (
    build_macro_regime_fusion_report,
)


def main() -> None:
    report = (
        build_macro_regime_fusion_report()
    )

    print(report["success"])
    print(report["summary"])

    print(
        "Fused context:",
        report.get(
            "fused_context"
        ),
    )

    print("Engine modifiers:")

    for row in report.get(
        "engine_context_modifiers",
        [],
    ):
        print({
            "engine_id": row.get(
                "engine_id"
            ),
            "family": row.get(
                "family"
            ),
            "modifier": row.get(
                "effective_context_modifier"
            ),
        })

    print("Outputs:")

    for name, path in report.get(
        "outputs",
        {},
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
