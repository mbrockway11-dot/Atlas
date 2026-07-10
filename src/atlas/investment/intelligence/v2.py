
"""Investment Intelligence v2 extension."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from atlas.common.io import (
    safe_read_csv,
    safe_read_json,
)
from atlas.investment.intelligence.market_context import (
    build_market_context,
)
from atlas.investment.intelligence.repository_context import (
    build_repository_context,
)
from atlas.investment.intelligence.reconciliation import (
    build_reconciled_snapshot,
)
from atlas.investment.intelligence.report import (
    build_investment_intelligence_report as build_v1,
)


REPORT_JSON = Path(
    "output/investment_intelligence/"
    "investment_intelligence_report.json"
)
REPORT_MD = Path(
    "output/investment_intelligence/"
    "investment_intelligence_report.md"
)
OPPORTUNITY_CSV = Path(
    "output/investment_intelligence/"
    "opportunity_map.csv"
)


def build_investment_intelligence_v2_report() -> dict:
    report = build_v1()

    universe = safe_read_json(
        Path(
            "output/investment_market_universe/"
            "market_universe_report.json"
        )
    )

    repository = safe_read_json(
        Path(
            "output/investment_price_repository/"
            "price_repository_report.json"
        )
    )

    features = safe_read_csv(
        Path(
            "output/investment_alpha/"
            "market_features.csv"
        )
    )

    rankings = safe_read_csv(
        Path(
            "output/investment_alpha/"
            "cross_sectional_alpha_latest.csv"
        )
    )

    if rankings.empty:
        rankings = safe_read_csv(
            Path(
                "output/investment_alpha/"
                "cross_sectional_alpha_rankings.csv"
            )
        )

    market_context = build_market_context(
        features,
        rankings,
    )

    repository_context = (
        build_repository_context(
            repository
        )
    )

    opportunity_map = build_opportunity_map(
        features,
        rankings,
    )

    universe_context = {
        "configured_assets": len(
            universe.get(
                "configured_assets",
                [],
            )
        ),
        "approved_assets": universe.get(
            "approved_assets",
            [],
        ),
        "rejected_assets": universe.get(
            "rejected_assets",
            [],
        ),
        "approved_count": len(
            universe.get(
                "approved_assets",
                [],
            )
        ),
        "research_asset_count": (
            market_context.get(
                "asset_count",
                0,
            )
        ),
    }

    reconciliation = build_reconciled_snapshot()

    report["version"] = (
        "investment_intelligence_v2_1"
    )
    report["reconciliation"] = reconciliation

    # Reconciliation owns all current/target/trade explanations.
    report["trade_explanations"] = reconciliation.get(
        "canonical_trades",
        [],
    )

    portfolio_explanation = (
        report.get("portfolio_explanation", {}) or {}
    )
    reconciled_portfolio = (
        reconciliation.get("portfolio", {}) or {}
    )

    portfolio_explanation["risky_weight"] = (
        reconciled_portfolio.get(
            "current_risky_weight",
            portfolio_explanation.get("risky_weight", 0.0),
        )
    )
    portfolio_explanation["cash_weight"] = (
        reconciled_portfolio.get(
            "current_cash_weight",
            portfolio_explanation.get("cash_weight", 0.0),
        )
    )
    portfolio_explanation["target_risky_weight"] = (
        reconciled_portfolio.get(
            "target_risky_weight",
            0.0,
        )
    )
    portfolio_explanation["target_cash_weight"] = (
        reconciled_portfolio.get(
            "target_cash_weight",
            0.0,
        )
    )
    portfolio_explanation["rebalance_order_count"] = len(
        report["trade_explanations"]
    )
    portfolio_explanation["snapshot_fingerprint"] = (
        reconciliation.get("snapshot_fingerprint")
    )
    portfolio_explanation["state_consistent"] = (
        reconciliation.get("state_consistent")
    )

    if report["trade_explanations"]:
        action_text = (
            f"{len(report['trade_explanations'])} reconciled "
            "portfolio action(s) are required."
        )
    else:
        action_text = (
            "No reconciled portfolio action is required; current "
            "weights match the latest canonical targets."
        )

    portfolio_explanation["explanation"] = (
        f"The reconciled portfolio is "
        f"{portfolio_explanation['risky_weight']:.2%} invested "
        f"with {portfolio_explanation['cash_weight']:.2%} in cash. "
        f"The canonical target is "
        f"{portfolio_explanation['target_risky_weight']:.2%} risky "
        f"and {portfolio_explanation['target_cash_weight']:.2%} cash. "
        f"{action_text}"
    )

    report["portfolio_explanation"] = portfolio_explanation

    reconciled_by_asset = {
        row.get("asset"): row
        for row in reconciliation.get(
            "asset_reconciliation",
            [],
        )
    }

    for row in report.get("asset_explanations", []):
        reconciled = reconciled_by_asset.get(
            row.get("asset")
        )

        if not reconciled:
            continue

        row["current_weight"] = reconciled[
            "current_weight"
        ]
        row["target_weight"] = reconciled[
            "canonical_target_weight"
        ]
        row["weight_delta"] = reconciled[
            "canonical_delta"
        ]
        row["target_source"] = (
            reconciled["canonical_target_source"]
        )
        row["snapshot_fingerprint"] = (
            reconciliation.get("snapshot_fingerprint")
        )

        delta = row["weight_delta"]

        if abs(delta) <= reconciliation["tolerance"]:
            allocation_text = (
                "Current exposure matches the reconciled target."
            )
        elif delta > 0:
            allocation_text = (
                f"Increase exposure by approximately {delta:.2%}."
            )
        else:
            allocation_text = (
                f"Reduce exposure by approximately {abs(delta):.2%}."
            )

        row["explanation"] = (
            f"{row['asset']} has ensemble conviction "
            f"{row.get('ensemble_score', 0.0):.3f}. "
            f"{allocation_text}"
        )
    report["market_context"] = market_context
    report["repository_context"] = (
        repository_context
    )
    report["universe_context"] = (
        universe_context
    )
    report["opportunity_map"] = (
        opportunity_map
    )
    report["research_execution_boundary"] = {
        "research_universe_count": (
            universe_context[
                "research_asset_count"
            ]
        ),
        "execution_remains_controlled_by": [
            "approved_universe",
            "adaptive_portfolio",
            "risk_engine",
            "trade_safety",
            "execution_engine",
        ],
        "intelligence_is_terminal": True,
        "execution_scope_changed": False,
    }

    report["v2_recommendations"] = (
        build_v2_recommendations(
            market_context,
            repository_context,
        )
    )

    confidence = (
        report.get("confidence", {}) or {}
    )

    base_confidence = float(
        confidence.get(
            "overall_confidence",
            0.0,
        )
    )

    coverage = float(
        repository_context.get(
            "coverage_ratio",
            0.0,
        )
    )

    adjusted = (
        base_confidence * 0.85
        + coverage * 0.15
    )

    confidence[
        "repository_adjusted_confidence"
    ] = round(adjusted, 6)

    report["summary"] = (
        "Investment Intelligence v2.1 assessed "
        f"{market_context.get('asset_count', 0)} "
        "research asset(s), identified market state "
        f"{market_context.get('market_state')}, "
        f"measured segmented-data coverage at {coverage:.1%}, "
        f"and reconciled portfolio state with "
        f"{len(report.get('trade_explanations', []))} "
        "canonical action(s)."
    )
    report["text_summary"] = report[
        "summary"
    ]

    write_v2_outputs(report)
    return report


def build_opportunity_map(
    features: pd.DataFrame,
    rankings: pd.DataFrame,
) -> list[dict]:
    if features is None or features.empty:
        return []

    frame = features.copy()

    if (
        rankings is not None
        and not rankings.empty
        and "asset" in rankings.columns
    ):
        rank_columns = [
            column
            for column in [
                "asset",
                "final_alpha_score",
                "final_rank",
                "ensemble_confidence",
                "ensemble_confirmed",
            ]
            if column in rankings.columns
        ]

        frame = frame.merge(
            rankings[rank_columns].drop_duplicates(
                subset=["asset"],
                keep="last",
            ),
            on="asset",
            how="left",
        )

    rows = []

    for _, row in frame.iterrows():
        score = numeric(
            row.get(
                "final_alpha_score",
                row.get(
                    "cross_sectional_score",
                    0.0,
                ),
            )
        )

        trend = str(
            row.get(
                "trend_state",
                "UNKNOWN",
            )
        )

        volatility = numeric(
            row.get("volatility_30d")
        )

        if score > 0.10 and trend == "UPTREND":
            label = "HIGH_PRIORITY_RESEARCH"
        elif score > 0.0:
            label = "WATCH"
        elif trend == "DOWNTREND":
            label = "AVOID_OR_HEDGE_RESEARCH"
        else:
            label = "NEUTRAL"

        rows.append({
            "asset": row.get("asset"),
            "opportunity_label": label,
            "alpha_score": score,
            "rank": numeric(
                row.get(
                    "final_rank",
                    row.get(
                        "cross_sectional_rank",
                        0,
                    ),
                )
            ),
            "trend_state": trend,
            "return_30d": numeric(
                row.get("return_30d")
            ),
            "volatility_30d": volatility,
            "ensemble_confidence": numeric(
                row.get(
                    "ensemble_confidence"
                )
            ),
            "research_only": True,
        })

    return sorted(
        rows,
        key=lambda item: (
            -item["alpha_score"],
            item["asset"],
        ),
    )


def build_v2_recommendations(
    market: dict,
    repository: dict,
) -> list[str]:
    recommendations = []

    if repository.get(
        "coverage_ratio",
        0.0,
    ) < 0.80:
        recommendations.append(
            "Do not promote intraday models until "
            "segmented repository coverage exceeds 80%."
        )

    concentration = (
        market.get(
            "rank_concentration",
            {},
        ) or {}
    )

    if concentration.get("label") in {
        "HIGHLY_CONCENTRATED",
        "CONCENTRATED",
    }:
        recommendations.append(
            "Leadership is concentrated; avoid treating "
            "the full universe as equally supported."
        )

    if market.get("market_state") == (
        "BROAD_RISK_OFF"
    ):
        recommendations.append(
            "Preserve cash and restrict new long exposure."
        )

    if not recommendations:
        recommendations.append(
            "Continue paper observation across all "
            "approved assets and timeframes."
        )

    return recommendations


def write_v2_outputs(report: dict) -> None:
    REPORT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        report.get("opportunity_map", [])
    ).to_csv(
        OPPORTUNITY_CSV,
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

    lines = [
        "# Investment Intelligence v2.1",
        "",
        report.get("summary", ""),
        "",
        "## Market Context",
        "",
        "```json",
        json.dumps(
            report.get(
                "market_context",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
        "## Price Repository",
        "",
        "```json",
        json.dumps(
            report.get(
                "repository_context",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
        "## Reconciliation",
        "",
        "```json",
        json.dumps(
            report.get(
                "reconciliation",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
        "## V2.1 Recommendations",
        "",
    ]

    for recommendation in report.get(
        "v2_recommendations",
        [],
    ):
        lines.append(
            f"- {recommendation}"
        )

    REPORT_MD.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def numeric(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
