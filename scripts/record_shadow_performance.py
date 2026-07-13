"""Record the latest verified G.12/G.13 cycle in the G.14 ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.investment.execution.analytics import (
    EXECUTION_ANALYTICS_JSON,
)
from atlas.investment.execution.performance_ledger import (
    append_performance_observation,
    build_performance_observation,
    rebuild_performance_outputs,
)
from atlas.investment.execution.shadow_pipeline import (
    SHADOW_PIPELINE_REPORT_JSON,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Record verified shadow performance "
            "in the append-only historical ledger."
        )
    )

    parser.add_argument(
        "--analytics-report",
        default=str(
            EXECUTION_ANALYTICS_JSON
        ),
    )

    parser.add_argument(
        "--pipeline-report",
        default=str(
            SHADOW_PIPELINE_REPORT_JSON
        ),
    )

    parser.add_argument(
        "--rolling-window",
        type=int,
        default=5,
    )

    return parser.parse_args()


def load_object(
    path: Path,
) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            str(path)
        )

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

    analytics = load_object(
        Path(
            args.analytics_report
        )
    )

    pipeline = load_object(
        Path(
            args.pipeline_report
        )
    )

    observation = (
        build_performance_observation(
            analytics_report=analytics,
            pipeline_report=pipeline,
        )
    )

    append_result = (
        append_performance_observation(
            observation
        )
    )

    rebuild = (
        rebuild_performance_outputs(
            rolling_window=(
                args.rolling_window
            )
        )
    )

    success = bool(
        rebuild["success"]
    )

    print(
        "ATLAS SHADOW PERFORMANCE "
        + (
            "RECORDED"
            if append_result[
                "appended"
            ]
            else (
                "ALREADY RECORDED"
                if append_result[
                    "duplicate"
                ]
                else "FAILED"
            )
        )
    )

    print(
        "Observation ID:",
        observation[
            "observation_id"
        ],
    )

    print(
        "Analytics ID:",
        observation[
            "analytics_id"
        ],
    )

    print(
        "Cycle ID:",
        observation[
            "cycle_id"
        ],
    )

    print(
        "Appended:",
        append_result[
            "appended"
        ],
    )

    print(
        "Duplicate:",
        append_result[
            "duplicate"
        ],
    )

    print(
        "Ledger records:",
        append_result[
            "record_count"
        ],
    )

    print(
        "Ledger valid:",
        rebuild[
            "validation"
        ][
            "valid"
        ],
    )

    print(
        "Summary:",
        rebuild[
            "summary"
        ],
    )

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
