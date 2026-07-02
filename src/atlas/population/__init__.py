"""Atlas population intelligence."""

from atlas.population.index import (
    POPULATION_INDEX_VERSION,
    PopulationIndex,
    PopulationRecord,
    build_population_index,
    build_population_record,
)

__all__ = [
    "POPULATION_INDEX_VERSION",
    "PopulationIndex",
    "PopulationRecord",
    "build_population_index",
    "build_population_record",
    "POPULATION_SIMILARITY_VERSION",
    "PopulationSimilarity",
    "compare_fingerprint_to_record",
    "find_similar_profiles",
    "similarity_from_distance",
    "vector_distance",
    "POPULATION_SEARCH_VERSION",
    "PopulationSearchResult",
    "search_population",
]

from atlas.population.similarity import (
    POPULATION_SIMILARITY_VERSION,
    PopulationSimilarity,
    compare_fingerprint_to_record,
    find_similar_profiles,
    similarity_from_distance,
    vector_distance,
)


from atlas.population.search import (
    POPULATION_SEARCH_VERSION,
    PopulationSearchResult,
    search_population,
)
