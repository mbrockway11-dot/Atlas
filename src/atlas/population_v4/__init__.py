
"""Atlas Population Intelligence v4 package."""

from atlas.population_v4.corpus import build_population_v4_corpus
from atlas.population_v4.features import build_population_feature_record
from atlas.population_v4.feature_index import build_population_feature_index
from atlas.population_v4.similarity import (
    build_similarity_matrix,
    compare_population_records,
    find_structural_neighbors,
)
from atlas.population_v4.archetypes import build_population_archetypes
from atlas.population_v4.cluster_report import build_population_cluster_report
from atlas.population_v4.clustering import build_hierarchical_clusters
from atlas.population_v4.outliers import build_population_outliers
from atlas.population_v4.neighbors import (
    find_neighbors_for_all,
    find_population_neighbors,
)

__all__ = [
    "build_population_v4_corpus",
    "build_population_feature_record",
    "build_population_feature_index",
    "build_similarity_matrix",
    "compare_population_records",
    "find_structural_neighbors",
    "find_neighbors_for_all",
    "find_population_neighbors",
    "build_hierarchical_clusters",
    "build_population_cluster_report",
    "build_population_archetypes",
    "build_population_outliers",
]
