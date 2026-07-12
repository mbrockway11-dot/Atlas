"""Run Validated Variant Registry v1."""

from __future__ import annotations

from atlas.investment.validated_variants import (
    build_validated_variant_registry_report,
)


def main() -> None:
    report = (
        build_validated_variant_registry_report()
    )

    print(report["success"])
    print(report["summary"])

    print(
        "Counts:",
        report.get("counts"),
    )

    print("Registered variants:")

    for variant in report.get(
        "variants",
        [],
    ):
        print({
            "variant_id": variant.get(
                "variant_id"
            ),
            "variant_name": variant.get(
                "variant_name"
            ),
            "parent_engine": variant.get(
                "parent_engine_id"
            ),
            "gate_mode": variant.get(
                "gate_mode"
            ),
            "feature": variant.get(
                "feature"
            ),
            "state": variant.get(
                "target_state"
            ),
            "review_status": variant.get(
                "review_status"
            ),
            "implementation_status": variant.get(
                "implementation_status"
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
