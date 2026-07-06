
"""Atlas Population Intelligence v4 package."""

from atlas.population_v4.corpus import build_population_v4_corpus
from atlas.population_v4.features import build_population_feature_record
from atlas.population_v4.feature_index import build_population_feature_index
from atlas.population_v4.similarity import (
    build_similarity_matrix,
    compare_population_records,
    find_structural_neighbors,
)
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
]
