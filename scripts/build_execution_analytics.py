"""Build G.13 execution analytics from the latest shadow-cycle records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.investment.execution.analytics import (
    build_execution_analytics,
)
from atlas.investment.execution.shadow_loop import (
    SHADOW_REPORT_JSON,
)
from atlas.investment.execution.shadow_pipeline import (
    SHADOW_PIPELINE_REPORT_JSON,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Build read-only Atlas execution analytics."
        )
    )

    parser.add_argument(
        "--shadow-report",
        default=str(
            SHADOW_REPORT_JSON
        ),
    )

    parser.add_argument(
        "--pipeline-report",
        default=str(
            SHADOW_PIPELINE_REPORT_JSON
        ),
    )

    return parser.parse_args()


def load_optional(
    path: Path,
) -> dict:
    if not path.exists():
        return {}

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "REPORT_MUST_BE_OBJECT:"
            + str(path)
        )

    return payload


def main() -> int:
    args = parse_args()

    shadow_path = Path(
        args.shadow_report
    )

    if not shadow_path.exists():
        raise FileNotFoundError(
            str(shadow_path)
        )

    shadow_report = load_optional(
        shadow_path
    )

    pipeline_report = (
        load_optional(
            Path(
                args.pipeline_report
            )
        )
    )

    report = build_execution_analytics(
        shadow_report,
        pipeline_report=(
            pipeline_report
        ),
        write_outputs=True,
    )

    summary = report["summary"]
    utilization = report[
        "utilization"
    ]

    print(
        "ATLAS EXECUTION ANALYTICS "
        + (
            "READY"
            if report["success"]
            else "FAILED"
        )
    )

    print(
        "Analytics ID:",
        report["analytics_id"],
    )

    print(
        "Cycle ID:",
        report["cycle_id"],
    )

    print(
        "Orders analyzed:",
        summary["order_count"],
    )

    print(
        "Full fill rate:",
        summary["full_fill_rate"],
    )

    print(
        "Gross fill notional:",
        summary[
            "gross_fill_notional"
        ],
    )

    print(
        "Fees:",
        summary["fee_cost"],
    )

    print(
        "Slippage cost:",
        summary[
            "slippage_cost"
        ],
    )

    print(
        "Total execution cost:",
        summary[
            "total_execution_cost"
        ],
    )

    print(
        "Weighted slippage bps:",
        summary[
            "weighted_slippage_bps"
        ],
    )

    print(
        "Weighted shortfall bps:",
        summary[
            "weighted_implementation_shortfall_bps"
        ],
    )

    print(
        "Execution cost / equity bps:",
        utilization[
            "execution_cost_bps_of_starting_equity"
        ],
    )

    print(
        "Reconciliation success rate:",
        summary[
            "reconciliation_success_rate"
        ],
    )

    print(
        "Errors:",
        report["errors"],
    )

    return (
        0
        if report["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
