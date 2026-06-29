"""Atlas research public API."""

from atlas.research.attractor_metrics import (
    build_attractor_signature,
    build_layer_attractor_metrics,
    empty_attractor_metrics,
    extract_layer_attractor,
    graph_density,
)

from atlas.research.baselines import (
    build_population_baselines,
    get_metric_baseline,
)

from atlas.research.coherence_metrics import (
    build_layer_coherence_metrics,
    classify_coherence,
    score_edge_coherence,
    score_node_coherence,
)

from atlas.research.distributions import (
    build_metric_distributions,
    percentile,
    summarize_distribution,
)

from atlas.research.feature_correlation import (
    build_feature_correlation_audit,
    classify_correlation,
    pearson_correlation,
)

from atlas.research.feature_importance import (
    compare_profile_feature_importance,
    pair_layers,
    summarize_feature_importance,
)

from atlas.research.feature_variance import (
    AUDIT_FEATURES,
    build_feature_variance_audit,
    classify_variance,
)

from atlas.research.graph_metrics import (
    build_layer_graph_metrics,
)

from atlas.research.matrix import (
    build_profile_matrix_rows,
    build_research_matrix,
)

from atlas.research.planetary_vectors import (
    build_planetary_vectors,
)

from atlas.research.population import (
    RESEARCH_METRICS,
    build_population_statistics,
    summarize_metrics,
)

from atlas.research.schema import (
    ATTRACTOR_METADATA,
    ATTRACTOR_STATISTICS,
    CANONICAL_RESEARCH_COLUMNS,
    COHERENCE_STATISTICS,
    CONSTRUCTION_METADATA,
    DEPRECATED_COLUMNS,
    GRAPH_STATISTICS,
    IDENTITY_PERSISTENCE,
    INFORMATION_MEASURES,
    MEASUREMENT_COLUMNS,
    PRIMARY_TOPOLOGY,
    REDUCTION_STATISTICS,
    SUBTYPE_METADATA,
    TRANSITIONAL_METRICS,
    audit_research_row,
    audit_research_rows,
    classify_column,
    clean_research_row,
    clean_research_rows,
)

from atlas.research.vectors import (
    PRIMARY_METRICS,
    build_layer_vector,
    build_profile_vectors,
)

from atlas.research.zscores import (
    CALIBRATED_METRICS,
    compute_layer_zscores,
    compute_profile_zscores,
)


__all__ = [
    # Attractor metrics
    "build_attractor_signature",
    "build_layer_attractor_metrics",
    "empty_attractor_metrics",
    "extract_layer_attractor",
    "graph_density",

    # Baselines
    "build_population_baselines",
    "get_metric_baseline",

    # Coherence metrics
    "build_layer_coherence_metrics",
    "classify_coherence",
    "score_edge_coherence",
    "score_node_coherence",

    # Distributions
    "build_metric_distributions",
    "summarize_distribution",
    "percentile",

    # Feature correlation
    "build_feature_correlation_audit",
    "pearson_correlation",
    "classify_correlation",

    # Feature importance
    "compare_profile_feature_importance",
    "pair_layers",
    "summarize_feature_importance",

    # Feature variance
    "AUDIT_FEATURES",
    "build_feature_variance_audit",
    "classify_variance",

    # Graph metrics
    "build_layer_graph_metrics",

    # Matrix
    "build_profile_matrix_rows",
    "build_research_matrix",

    # Planetary vectors
    "build_planetary_vectors",

    # Population
    "RESEARCH_METRICS",
    "build_population_statistics",
    "summarize_metrics",

    # Schema / audit
    "ATTRACTOR_METADATA",
    "ATTRACTOR_STATISTICS",
    "CANONICAL_RESEARCH_COLUMNS",
    "COHERENCE_STATISTICS",
    "CONSTRUCTION_METADATA",
    "DEPRECATED_COLUMNS",
    "GRAPH_STATISTICS",
    "IDENTITY_PERSISTENCE",
    "INFORMATION_MEASURES",
    "MEASUREMENT_COLUMNS",
    "PRIMARY_TOPOLOGY",
    "REDUCTION_STATISTICS",
    "SUBTYPE_METADATA",
    "TRANSITIONAL_METRICS",
    "audit_research_row",
    "audit_research_rows",
    "classify_column",
    "clean_research_row",
    "clean_research_rows",

    # Vectors
    "PRIMARY_METRICS",
    "build_layer_vector",
    "build_profile_vectors",

    # Z-scores
    "CALIBRATED_METRICS",
    "compute_layer_zscores",
    "compute_profile_zscores",
]