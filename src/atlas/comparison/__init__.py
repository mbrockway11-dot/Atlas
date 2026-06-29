"""Atlas comparison framework."""

from .compare import (
    IdentityComparison,
    build_comparison_interpretation,
    build_planet_difference_summary,
    classify_difference,
    compare_profiles,
    identity_comparison_to_dict,
    infer_planet_from_feature,
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
    "build_planet_difference_summary",
    "classify_difference",
    "compare_profiles",
    "identity_comparison_to_dict",
    "infer_planet_from_feature",
    "PLANETS",
    "PlanetAgreementMatrix",
    "PlanetAgreementRow",
    "compare_planet_agreement",
]