"""Atlas measurement framework.

The measurement package exposes normalized structural measurements used by the
Identity Vector Engine. Each measurement family is independent and returns
bounded (0–1) values whenever possible.
"""

from atlas.measurement.coverage import (
    CoverageMeasurement,
    measure_coverage,
)

from atlas.measurement.organization import (
    OrganizationMeasurement,
    measure_organization,
)

from atlas.measurement.stability import (
    StabilityMeasurement,
    measure_stability,
)

from atlas.measurement.dynamics import (
    DynamicsMeasurement,
    measure_dynamics,
)

from atlas.measurement.structural_roles import (
    STRUCTURAL_ROLES,
    StructuralRoleMeasurement,
    measure_structural_roles,
)

__all__ = [
    # Coverage
    "CoverageMeasurement",
    "measure_coverage",

    # Organization
    "OrganizationMeasurement",
    "measure_organization",

    # Stability
    "StabilityMeasurement",
    "measure_stability",

    # Dynamics
    "DynamicsMeasurement",
    "measure_dynamics",

    # Structural Roles
    "STRUCTURAL_ROLES",
    "StructuralRoleMeasurement",
    "measure_structural_roles",
]