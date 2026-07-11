"""Macro Intelligence v1 orchestration and outputs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.macro_intelligence.classifier import (
    classify_macro_environment,
)
from atlas.investment.macro_intelligence.features import (
    calculate_series_features,
)
from atlas.investment.macro_intelligence.provider import (
    fetch_series,
)
from atlas.investment.macro_intelligence.registry import (
    MACRO_SERIES,
)


OUT_DIR = Path(
    "output/investment_macro_intelligence"
)

REPORT_JSON = (
    OUT_DIR
    / "macro_intelligence_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "macro_intelligence_report.md"
)

INDICATORS_CSV = (
    OUT_DIR
    / "macro_indicators.csv"
)

FETCH_STATUS_CSV = (
    OUT_DIR
    / "macro_fetch_status.csv"
)

HISTORY_CSV = (
    OUT_DIR
    / "macro_regime_history.csv"
)


def build_macro_intelligence_report() -> dict[str, Any]:
    """Fetch, analyze, classify, and persist macro intelligence."""
    indicators: list[dict] = []
    fetch_status: list[dict] = []

    for key, definition in (
        MACRO_SERIES.items()
    ):
        frame, metadata = fetch_series(
            definition["series_id"]
        )

        features = (
            calculate_series_features(
                frame,
                transform=definition[
                    "transform"
                ],
            )
        )

        indicators.append({
            "key": key,
            **definition,
            **features,
            "source": (
                "public_economic_series"
            ),
        })

        fetch_status.append({
            "key": key,
            **metadata,
            "row_count": int(
                len(frame)
            ),
        })

    macro = classify_macro_environment(
        indicators
    )

    successful_series = sum(
        bool(
            row.get(
                "network_success"
            )
            or row.get(
                "used_cache"
            )
        )
        for row in fetch_status
    )

    report = {
        "success": (
            successful_series >= 5
        ),
        "version": (
            "macro_intelligence_v1"
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Macro Intelligence v1 classified "
            f"the environment as "
            f"{macro.get('macro_regime')} "
            f"with confidence "
            f"{macro.get('confidence')} using "
            f"{successful_series}/"
            f"{len(MACRO_SERIES)} available series."
        ),
        "macro_environment": macro,
        "indicators": indicators,
        "fetch_status": fetch_status,
        "counts": {
            "registered_series": len(
                MACRO_SERIES
            ),
            "available_series": (
                successful_series
            ),
            "network_series": sum(
                bool(
                    row.get(
                        "network_success"
                    )
                )
                for row in fetch_status
            ),
            "cached_series": sum(
                bool(
                    row.get(
                        "used_cache"
                    )
                )
                for row in fetch_status
            ),
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "uses_real_observations": True,
            "permits_cached_observations": True,
            "deterministic_given_inputs": True,
            "influences_execution": False,
        },
        "outputs": {
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
            "indicators_csv": str(
                INDICATORS_CSV
            ),
            "fetch_status_csv": str(
                FETCH_STATUS_CSV
            ),
            "history_csv": str(
                HISTORY_CSV
            ),
        },
    }

    write_outputs(report)

    return report


def write_outputs(
    report: dict[str, Any],
) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        report["indicators"]
    ).to_csv(
        INDICATORS_CSV,
        index=False,
    )

    pd.DataFrame(
        report["fetch_status"]
    ).to_csv(
        FETCH_STATUS_CSV,
        index=False,
    )

    macro = report[
        "macro_environment"
    ]

    history_row = {
        "generated_at": report[
            "generated_at"
        ],
        "macro_regime": macro.get(
            "macro_regime"
        ),
        "confidence": macro.get(
            "confidence"
        ),
        "risk_pressure": macro.get(
            "risk_pressure"
        ),
        "liquidity_support": macro.get(
            "liquidity_support"
        ),
        "inflation_pressure": macro.get(
            "inflation_pressure"
        ),
        "growth_stress": macro.get(
            "growth_stress"
        ),
        "policy_restriction": macro.get(
            "policy_restriction"
        ),
        "credit_stress": macro.get(
            "credit_stress"
        ),
    }

    previous = pd.DataFrame()

    if (
        HISTORY_CSV.exists()
        and HISTORY_CSV.stat().st_size > 0
    ):
        try:
            previous = pd.read_csv(
                HISTORY_CSV
            )
        except Exception:
            previous = pd.DataFrame()

    history = pd.concat(
        [
            previous,
            pd.DataFrame([
                history_row
            ]),
        ],
        ignore_index=True,
    )

    history.to_csv(
        HISTORY_CSV,
        index=False,
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
        build_markdown(report),
        encoding="utf-8",
    )


def build_markdown(
    report: dict[str, Any],
) -> str:
    macro = report[
        "macro_environment"
    ]

    lines = [
        "# Macro Intelligence v1",
        "",
        report["summary"],
        "",
        "## Current Macro Environment",
        "",
        (
            "- Regime: "
            f"`{macro.get('macro_regime')}`"
        ),
        (
            "- Confidence: "
            f"`{macro.get('confidence')}`"
        ),
        (
            "- Risk pressure: "
            f"`{macro.get('risk_pressure')}`"
        ),
        (
            "- Liquidity support: "
            f"`{macro.get('liquidity_support')}`"
        ),
        (
            "- Inflation pressure: "
            f"`{macro.get('inflation_pressure')}`"
        ),
        (
            "- Growth stress: "
            f"`{macro.get('growth_stress')}`"
        ),
        (
            "- Policy restriction: "
            f"`{macro.get('policy_restriction')}`"
        ),
        (
            "- Credit stress: "
            f"`{macro.get('credit_stress')}`"
        ),
        "",
        "## Reason Codes",
        "",
    ]

    for reason in macro.get(
        "reason_codes",
        [],
    ):
        lines.append(
            f"- `{reason}`"
        )

    lines.extend([
        "",
        "## Indicators",
        "",
    ])

    for row in report[
        "indicators"
    ]:
        lines.append(
            "- "
            f"`{row.get('key')}` "
            f"date=`{row.get('observation_date')}` "
            f"value=`{row.get('latest_value')}` "
            f"transformed=`{row.get('transformed_value')}` "
            f"z=`{row.get('z_score')}` "
            f"trend=`{row.get('trend')}`"
        )

    lines.extend([
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
