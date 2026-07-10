
"""Market Features v2.

Approved Market Universe assets are analyzed for research and ranking.
Execution permissions remain controlled by downstream safety and universe
eligibility gates.
"""

from atlas.investment.alpha.market_features.report import (
    build_market_feature_report,
)

__all__ = ["build_market_feature_report"]
