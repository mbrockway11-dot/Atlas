"""Atlas comparison framework."""

from .compare import (
    IdentityComparison,
    build_comparison_interpretation,
    build_feature_difference_rows,
    build_feature_family_summary,
    build_planet_difference_summary,
    classify_difference,
    compare_profiles,
    comparison_feature_columns,
    identity_comparison_to_dict,
    infer_planet_from_feature,
)
from .feature_registry import (
    FEATURE_REGISTRY_VERSION,
    FEATURE_RULES,
    FeatureRule,
    feature_family,
    feature_is_registered,
    feature_weight,
    registered_features,
)
from .planet_matrix import (
    PLANETS,
    PlanetAgreementMatrix,
    PlanetAgreementRow,
    compare_planet_agreement,
)

__all__ = [
    "IdentityComparison",
    "build_comparison_interpretation",
    "build_feature_difference_rows",
    "build_feature_family_summary",
    "build_planet_difference_summary",
    "classify_difference",
    "compare_profiles",
    "comparison_feature_columns",
    "identity_comparison_to_dict",
    "infer_planet_from_feature",
    "FEATURE_REGISTRY_VERSION",
    "FEATURE_RULES",
    "FeatureRule",
    "feature_family",
    "feature_is_registered",
    "feature_weight",
    "registered_features",
    "PLANETS",
    "PlanetAgreementMatrix",
    "PlanetAgreementRow",
    "compare_planet_agreement",
]
