"""Deterministic Portfolio Optimizer v2."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from atlas.investment.portfolio_optimizer.constraints import (
    DEFAULT_CASH_FLOOR,
    DEFAULT_TARGET_VOLATILITY,
    MAX_ASSET_WEIGHT,
    MAX_CASH_WEIGHT,
    MAX_SELECTED_ASSETS,
    MIN_ASSET_WEIGHT,
    MIN_SELECTED_ASSETS,
    MIN_TARGET_VOLATILITY,
    MAX_TARGET_VOLATILITY,
    TURNOVER_PENALTY,
    clamp,
)
from atlas.investment.portfolio_optimizer.risk_model import (
    build_covariance_matrix,
    build_return_matrix,
    calculate_portfolio_risk,
)


def optimize_portfolio(
    *,
    ensemble_scores: pd.DataFrame,
    contributions: pd.DataFrame,
    market_history: pd.DataFrame,
    fusion_report: dict,
    current_portfolio: pd.DataFrame | None = None,
    approved_universe: pd.DataFrame | None = None,
) -> dict:
    """Build a bounded context-aware optimized portfolio."""
    candidates = build_candidates(
        ensemble_scores,
        contributions,
        approved_universe,
    )

    controls = extract_controls(
        fusion_report
    )

    if candidates.empty:
        portfolio = cash_only_portfolio(
            reason=(
                "No eligible positive-conviction "
                "assets were available."
            )
        )

        return {
            "portfolio": portfolio,
            "risk": empty_risk(),
            "controls": controls,
            "diagnostics": {
                "candidate_count": 0,
                "selected_assets": 0,
                "turnover": 0.0,
            },
        }

    candidates = candidates.head(
        MAX_SELECTED_ASSETS
    ).copy()

    assets = candidates[
        "asset"
    ].tolist()

    returns = build_return_matrix(
        market_history,
        assets,
    )

    covariance = build_covariance_matrix(
        returns,
        assets,
    )

    volatility = pd.Series(
        {
            asset: math.sqrt(
                max(
                    1e-10,
                    float(
                        covariance.loc[
                            asset,
                            asset,
                        ]
                    ),
                )
            )
            for asset in assets
        }
    )

    inverse_volatility = (
        1.0
        / volatility.replace(
            0.0,
            np.nan,
        )
    ).fillna(0.0)

    inverse_volatility = normalize(
        inverse_volatility
    )

    alpha_weights = normalize(
        candidates.set_index(
            "asset"
        )[
            "optimizer_score"
        ]
    )

    diversification_weights = (
        build_diversification_weights(
            covariance
        )
    )

    blended = (
        alpha_weights * 0.55
        + inverse_volatility * 0.25
        + diversification_weights * 0.20
    )

    current_weights = extract_current_weights(
        current_portfolio
    )

    if current_weights:
        current = pd.Series(
            {
                asset: current_weights.get(
                    asset,
                    0.0,
                )
                for asset in assets
            }
        )

        current = normalize(
            current
        )

        blended = (
            blended
            * (
                1.0
                - TURNOVER_PENALTY
            )
            + current
            * TURNOVER_PENALTY
        )

    blended = project_weights(
        blended,
        max_weight=MAX_ASSET_WEIGHT,
    )

    target_volatility = clamp(
        DEFAULT_TARGET_VOLATILITY
        * controls[
            "volatility_target_multiplier"
        ],
        MIN_TARGET_VOLATILITY,
        MAX_TARGET_VOLATILITY,
    )

    cash_floor = clamp(
        controls[
            "minimum_cash_weight"
        ],
        DEFAULT_CASH_FLOOR,
        MAX_CASH_WEIGHT,
    )

    risk_budget_multiplier = clamp(
        controls[
            "risk_budget_multiplier"
        ],
        0.50,
        1.10,
    )

    investable_limit = min(
        1.0 - cash_floor,
        risk_budget_multiplier,
    )

    preliminary = (
        blended * investable_limit
    )

    preliminary_risk = calculate_portfolio_risk(
        preliminary,
        covariance,
    )

    observed_volatility = float(
        preliminary_risk.get(
            "annualized_volatility",
            0.0,
        )
    )

    volatility_scale = (
        min(
            1.0,
            target_volatility
            / observed_volatility,
        )
        if observed_volatility > 1e-12
        else 1.0
    )

    risky_weights = (
        preliminary
        * volatility_scale
    )

    risky_weights = project_weights(
        risky_weights,
        max_weight=MAX_ASSET_WEIGHT,
        target_total=min(
            investable_limit,
            float(
                risky_weights.sum()
            ),
        ),
    )

    risky_weights = risky_weights[
        risky_weights
        >= MIN_ASSET_WEIGHT
    ]

    if len(risky_weights) < MIN_SELECTED_ASSETS:
        risky_weights = (
            preliminary.sort_values(
                ascending=False
            )
            .head(
                MIN_SELECTED_ASSETS
            )
        )

        risky_weights = project_weights(
            risky_weights,
            max_weight=MAX_ASSET_WEIGHT,
            target_total=min(
                investable_limit,
                float(
                    risky_weights.sum()
                ),
            ),
        )

    cash_weight = max(
        cash_floor,
        1.0
        - float(
            risky_weights.sum()
        ),
    )

    if (
        risky_weights.sum()
        + cash_weight
        > 1.0 + 1e-8
    ):
        risky_weights = (
            risky_weights
            * (
                1.0 - cash_weight
            )
            / float(
                risky_weights.sum()
            )
        )

    final_weights = risky_weights.copy()
    final_weights.loc["CASH"] = (
        1.0
        - float(
            risky_weights.sum()
        )
    )

    final_risk = calculate_portfolio_risk(
        final_weights,
        covariance,
    )

    portfolio = build_portfolio_rows(
        candidates,
        final_weights,
        volatility,
        final_risk,
    )

    turnover = calculate_turnover(
        final_weights,
        current_weights,
    )

    diagnostics = {
        "candidate_count": int(
            len(candidates)
        ),
        "selected_assets": int(
            len(risky_weights)
        ),
        "turnover": round(
            turnover,
            8,
        ),
        "target_volatility": round(
            target_volatility,
            8,
        ),
        "volatility_scale": round(
            volatility_scale,
            8,
        ),
        "investable_limit": round(
            investable_limit,
            8,
        ),
        "cash_floor": round(
            cash_floor,
            8,
        ),
        "weight_total": round(
            float(
                final_weights.sum()
            ),
            8,
        ),
    }

    return {
        "portfolio": portfolio,
        "risk": final_risk,
        "controls": controls,
        "diagnostics": diagnostics,
        "covariance": covariance,
    }


def build_candidates(
    scores: pd.DataFrame,
    contributions: pd.DataFrame,
    approved: pd.DataFrame | None,
) -> pd.DataFrame:
    if scores is None or scores.empty:
        return pd.DataFrame()

    frame = scores.copy()

    if "asset" not in frame.columns:
        return pd.DataFrame()

    approved_assets: set[str] | None = None

    if (
        approved is not None
        and not approved.empty
        and "asset" in approved.columns
    ):
        approved_assets = set(
            approved[
                "asset"
            ].dropna().astype(str)
        )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
    )

    if approved_assets is not None:
        frame = frame[
            frame["asset"].isin(
                approved_assets
            )
        ]

    score_column = first_column(
        frame,
        [
            "conviction",
            "ensemble_conviction",
            "ensemble_score",
            "final_alpha_score",
        ],
    )

    if score_column is None:
        return pd.DataFrame()

    frame["ensemble_conviction"] = (
        pd.to_numeric(
            frame[score_column],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(0.0, 1.0)
    )

    confidence_column = first_column(
        frame,
        [
            "confidence",
            "ensemble_confidence",
        ],
    )

    frame["ensemble_confidence"] = (
        pd.to_numeric(
            frame[
                confidence_column
            ],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(0.0, 1.0)
        if confidence_column
        else 0.0
    )

    contribution_summary = (
        summarize_contributions(
            contributions
        )
    )

    frame = frame.merge(
        contribution_summary,
        on="asset",
        how="left",
    )

    frame[
        "positive_engine_share"
    ] = frame[
        "positive_engine_share"
    ].fillna(0.0)

    frame[
        "contribution_concentration"
    ] = frame[
        "contribution_concentration"
    ].fillna(1.0)

    diversification_quality = (
        1.0
        - frame[
            "contribution_concentration"
        ].clip(
            0.0,
            1.0,
        )
    )

    frame["optimizer_score"] = (
        frame[
            "ensemble_conviction"
        ] * 0.55
        + frame[
            "ensemble_confidence"
        ] * 0.20
        + frame[
            "positive_engine_share"
        ] * 0.15
        + diversification_quality * 0.10
    )

    frame = frame[
        frame[
            "optimizer_score"
        ] > 0.0
    ]

    return frame.sort_values(
        [
            "optimizer_score",
            "asset",
        ],
        ascending=[
            False,
            True,
        ],
        kind="stable",
    ).drop_duplicates(
        subset=["asset"],
        keep="first",
    ).reset_index(drop=True)


def summarize_contributions(
    contributions: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "asset",
        "positive_engine_share",
        "contribution_concentration",
        "engine_count",
    ]

    if (
        contributions is None
        or contributions.empty
        or "asset" not in contributions.columns
    ):
        return pd.DataFrame(
            columns=columns
        )

    frame = contributions.copy()

    frame["weighted_contribution"] = pd.to_numeric(
        frame.get(
            "weighted_contribution",
            0.0,
        ),
        errors="coerce",
    ).fillna(0.0)

    frame["signed_contribution"] = pd.to_numeric(
        frame.get(
            "signed_contribution",
            0.0,
        ),
        errors="coerce",
    ).fillna(0.0)

    rows = []

    for asset, group in frame.groupby(
        "asset",
        sort=True,
    ):
        absolute = (
            group[
                "weighted_contribution"
            ].abs()
        )

        total = float(
            absolute.sum()
        )

        shares = (
            absolute / total
            if total > 1e-12
            else pd.Series(
                0.0,
                index=group.index,
            )
        )

        rows.append({
            "asset": str(asset),
            "positive_engine_share": round(
                float(
                    (
                        group[
                            "signed_contribution"
                        ] > 0
                    ).mean()
                ),
                8,
            ),
            "contribution_concentration": round(
                float(
                    (
                        shares ** 2
                    ).sum()
                ),
                8,
            ),
            "engine_count": int(
                group[
                    "engine_id"
                ].nunique()
                if "engine_id" in group.columns
                else len(group)
            ),
        })

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def build_diversification_weights(
    covariance: pd.DataFrame,
) -> pd.Series:
    assets = covariance.index.tolist()

    if not assets:
        return pd.Series(dtype=float)

    correlation = covariance.copy()

    volatility = np.sqrt(
        np.maximum(
            np.diag(
                covariance.to_numpy(
                    dtype=float
                )
            ),
            1e-12,
        )
    )

    denominator = np.outer(
        volatility,
        volatility,
    )

    values = covariance.to_numpy(
        dtype=float
    ) / denominator

    np.fill_diagonal(
        values,
        0.0,
    )

    average_correlation = np.nanmean(
        np.abs(values),
        axis=1,
    )

    scores = 1.0 / (
        1.0
        + average_correlation
    )

    return normalize(
        pd.Series(
            scores,
            index=assets,
        )
    )


def project_weights(
    weights: pd.Series,
    *,
    max_weight: float,
    target_total: float | None = None,
) -> pd.Series:
    """Project positive weights into capped simplex."""
    result = (
        pd.to_numeric(
            weights,
            errors="coerce",
        )
        .fillna(0.0)
        .clip(lower=0.0)
    )

    if result.empty:
        return result

    total = (
        float(result.sum())
        if target_total is None
        else max(
            0.0,
            float(target_total),
        )
    )

    if total <= 0:
        return result * 0.0

    result = normalize(
        result
    ) * total

    for _ in range(20):
        over = result > max_weight

        if not over.any():
            break

        excess = float(
            (
                result[over]
                - max_weight
            ).sum()
        )

        result.loc[over] = max_weight

        under = ~over

        available = (
            max_weight
            - result[under]
        ).clip(lower=0.0)

        capacity = float(
            available.sum()
        )

        if (
            excess <= 1e-12
            or capacity <= 1e-12
        ):
            break

        redistribution = (
            available
            / capacity
            * min(
                excess,
                capacity,
            )
        )

        result.loc[under] += redistribution

    return result


def build_portfolio_rows(
    candidates: pd.DataFrame,
    weights: pd.Series,
    volatility: pd.Series,
    risk: dict,
) -> pd.DataFrame:
    indexed = candidates.set_index(
        "asset"
    )

    rows = []

    risk_contributions = risk.get(
        "risk_contributions",
        {},
    )

    for asset, weight in (
        weights.drop(
            labels=["CASH"],
            errors="ignore",
        )
        .sort_values(
            ascending=False
        )
        .items()
    ):
        row = indexed.loc[asset]

        rows.append({
            "asset": asset,
            "target_weight": round(
                float(weight),
                8,
            ),
            "optimizer_score": round(
                float(
                    row.get(
                        "optimizer_score",
                        0.0,
                    )
                ),
                8,
            ),
            "ensemble_conviction": round(
                float(
                    row.get(
                        "ensemble_conviction",
                        0.0,
                    )
                ),
                8,
            ),
            "ensemble_confidence": round(
                float(
                    row.get(
                        "ensemble_confidence",
                        0.0,
                    )
                ),
                8,
            ),
            "positive_engine_share": round(
                float(
                    row.get(
                        "positive_engine_share",
                        0.0,
                    )
                ),
                8,
            ),
            "annualized_asset_volatility": round(
                float(
                    volatility.get(
                        asset,
                        0.0,
                    )
                ),
                8,
            ),
            "risk_contribution": round(
                float(
                    risk_contributions.get(
                        asset,
                        0.0,
                    )
                ),
                8,
            ),
            "reason": (
                "Optimized from ensemble conviction, "
                "engine breadth, inverse volatility, "
                "covariance diversification, and "
                "macro-regime controls."
            ),
            "source": (
                "portfolio_optimizer_v2"
            ),
        })

    rows.append({
        "asset": "CASH",
        "target_weight": round(
            float(
                weights.get(
                    "CASH",
                    1.0,
                )
            ),
            8,
        ),
        "optimizer_score": 0.0,
        "ensemble_conviction": 0.0,
        "ensemble_confidence": 0.0,
        "positive_engine_share": 0.0,
        "annualized_asset_volatility": 0.0,
        "risk_contribution": 0.0,
        "reason": (
            "Residual cash and bounded "
            "macro-regime risk reserve."
        ),
        "source": (
            "portfolio_optimizer_v2"
        ),
    })

    return pd.DataFrame(rows)


def extract_controls(
    fusion_report: dict,
) -> dict:
    context = (
        fusion_report.get(
            "fused_context",
            {},
        )
        or {}
    )

    controls = (
        context.get(
            "controls",
            {},
        )
        or {}
    )

    return {
        "fused_regime": context.get(
            "fused_regime",
            "UNKNOWN",
        ),
        "fusion_confidence": float(
            context.get(
                "confidence",
                0.0,
            )
            or 0.0
        ),
        "risk_budget_multiplier": float(
            controls.get(
                "risk_budget_multiplier",
                1.0,
            )
            or 1.0
        ),
        "minimum_cash_weight": float(
            controls.get(
                "minimum_cash_weight",
                DEFAULT_CASH_FLOOR,
            )
            or DEFAULT_CASH_FLOOR
        ),
        "conviction_ceiling": float(
            controls.get(
                "conviction_ceiling",
                1.0,
            )
            or 1.0
        ),
        "volatility_target_multiplier": float(
            controls.get(
                "volatility_target_multiplier",
                1.0,
            )
            or 1.0
        ),
        "turnover_multiplier": float(
            controls.get(
                "turnover_multiplier",
                1.0,
            )
            or 1.0
        ),
    }


def extract_current_weights(
    portfolio: pd.DataFrame | None,
) -> dict[str, float]:
    if (
        portfolio is None
        or portfolio.empty
        or not {
            "asset",
            "target_weight",
        }.issubset(
            portfolio.columns
        )
    ):
        return {}

    return {
        str(row["asset"]): float(
            row["target_weight"]
        )
        for _, row in portfolio.iterrows()
        if pd.notna(
            row.get("target_weight")
        )
    }


def calculate_turnover(
    weights: pd.Series,
    current: dict[str, float],
) -> float:
    if not current:
        return float(
            weights.drop(
                labels=["CASH"],
                errors="ignore",
            ).sum()
        )

    assets = set(
        weights.index
    ) | set(
        current
    )

    return 0.5 * sum(
        abs(
            float(
                weights.get(
                    asset,
                    0.0,
                )
            )
            - float(
                current.get(
                    asset,
                    0.0,
                )
            )
        )
        for asset in assets
    )


def normalize(
    values: pd.Series,
) -> pd.Series:
    values = (
        pd.to_numeric(
            values,
            errors="coerce",
        )
        .fillna(0.0)
        .clip(lower=0.0)
    )

    total = float(
        values.sum()
    )

    if total <= 1e-12:
        if len(values) == 0:
            return values

        return pd.Series(
            1.0 / len(values),
            index=values.index,
        )

    return values / total


def first_column(
    frame: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate

    return None


def cash_only_portfolio(
    *,
    reason: str,
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "asset": "CASH",
            "target_weight": 1.0,
            "optimizer_score": 0.0,
            "reason": reason,
            "source": (
                "portfolio_optimizer_v2"
            ),
        }
    ])


def empty_risk() -> dict:
    return {
        "annualized_volatility": 0.0,
        "diversification_ratio": 0.0,
        "effective_asset_count": 0.0,
        "largest_asset_weight": 0.0,
        "risk_contributions": {},
    }
