
"""Changes since the previous Investment Intelligence report."""

from __future__ import annotations


def build_change_summary(
    prior: dict,
    current_confidence: dict,
    current_portfolio: dict,
    current_assets: list[dict],
) -> dict:
    if not prior:
        return {
            "has_prior_report": False,
            "changes": [
                "This is the first Investment Intelligence snapshot."
            ],
        }

    changes = []

    prior_confidence = (
        prior.get("confidence", {}) or {}
    ).get("overall_confidence")

    current_confidence_value = current_confidence.get(
        "overall_confidence"
    )

    if prior_confidence is not None:
        difference = round(
            float(current_confidence_value)
            - float(prior_confidence),
            6,
        )

        if difference:
            changes.append(
                f"Overall confidence changed by {difference:+.4f}."
            )

    prior_portfolio = (
        prior.get("portfolio_explanation", {}) or {}
    )

    for key, label in [
        ("risky_weight", "Risky exposure"),
        ("cash_weight", "Cash exposure"),
        ("drawdown", "Drawdown"),
    ]:
        previous = prior_portfolio.get(key)
        current = current_portfolio.get(key)

        if previous is None or current is None:
            continue

        delta = round(float(current) - float(previous), 6)

        if delta:
            changes.append(
                f"{label} changed by {delta:+.4%}."
            )

    prior_assets = {
        row.get("asset"): row
        for row in prior.get("asset_explanations", []) or []
    }

    for row in current_assets:
        asset = row.get("asset")
        prior_row = prior_assets.get(asset)

        if not prior_row:
            changes.append(
                f"{asset} was added to the intelligence snapshot."
            )
            continue

        old_target = prior_row.get("target_weight")
        new_target = row.get("target_weight")

        if old_target is None or new_target is None:
            continue

        delta = round(float(new_target) - float(old_target), 6)

        if delta:
            changes.append(
                f"{asset} target weight changed by {delta:+.4%}."
            )

    if not changes:
        changes.append(
            "No material portfolio-intelligence changes detected."
        )

    return {
        "has_prior_report": True,
        "changes": changes,
    }
