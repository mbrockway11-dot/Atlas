"""Tests for population corpus builder."""

from __future__ import annotations

from atlas.population import (
    build_population_corpus,
    search_population,
)


def test_build_population_corpus_single_profile():
    result = build_population_corpus(
        ["nikola_tesla"],
        evaluation_date="2026-07-02",
        forecast_days=3,
    )

    payload = result.to_dict()

    assert result.success_count == 1
    assert result.failure_count == 0
    assert result.index.count == 1
    assert result.successes == ("nikola_tesla",)
    assert payload["summary"]["index_count"] == 1


def test_population_corpus_index_can_be_searched():
    result = build_population_corpus(
        ["nikola_tesla"],
        evaluation_date="2026-07-02",
        forecast_days=3,
    )

    record = result.index.find_profile("nikola_tesla")
    assert record is not None

    # Rehydrate query fingerprint from the indexed record shape through corpus payload.
    from atlas.population.corpus import structural_fingerprint_from_payload

    query = structural_fingerprint_from_payload(
        {
            "version": "0.1",
            "profile_key": record.profile_key,
            "vector": record.vector,
            "labels": record.labels,
            "structural_hash": record.structural_hash,
            "metadata": record.metadata,
        }
    )

    search = search_population(
        index=result.index,
        fingerprint=query,
        minimum_similarity=0.9,
    )

    assert search.count == 1
    assert search.matches[0].profile_key == "nikola_tesla"


def test_build_population_corpus_respects_limit():
    result = build_population_corpus(
        ["nikola_tesla", "missing_profile"],
        evaluation_date="2026-07-02",
        forecast_days=3,
        limit=1,
    )

    assert result.metadata["requested_count"] == 1
    assert result.success_count == 1
    assert result.failure_count == 0
