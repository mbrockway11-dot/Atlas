"""Run Research Variant Implementation Planner v1."""

from __future__ import annotations

from atlas.investment.variant_implementation_planner import (
    build_variant_implementation_planner_report,
)


def main() -> None:
    report = (
        build_variant_implementation_planner_report()
    )

    print(report["success"])
    print(report["summary"])
    print(
        "Counts:",
        report.get("counts"),
    )

    print("Plans:")

    for plan in report.get(
        "plans",
        [],
    ):
        print({
            "plan_id": plan.get(
                "plan_id"
            ),
            "variant_id": plan.get(
                "variant_id"
            ),
            "variant_name": plan.get(
                "variant_name"
            ),
            "parent_engine": plan.get(
                "parent_engine_id"
            ),
            "status": plan.get(
                "plan_status"
            ),
            "variant_file": plan.get(
                "variant_module_file"
            ),
            "test_file": plan.get(
                "variant_test_file"
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
