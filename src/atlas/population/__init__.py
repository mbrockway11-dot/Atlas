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
    "POPULATION_ARCHIVE_VERSION",
    "load_population_index",
    "population_index_from_json",
    "population_index_to_json",
    "save_population_index",
    "POPULATION_CORPUS_VERSION",
    "PopulationCorpusResult",
    "build_population_corpus",
    "structural_fingerprint_from_payload",
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


from atlas.population.archive import (
    POPULATION_ARCHIVE_VERSION,
    load_population_index,
    population_index_from_json,
    population_index_to_json,
    save_population_index,
)


from atlas.population.corpus import (
    POPULATION_CORPUS_VERSION,
    PopulationCorpusResult,
    build_population_corpus,
    structural_fingerprint_from_payload,
)
