from atlas.corpus.search import CorpusSearch


def test_load_search():
    corpus = CorpusSearch()

    assert corpus.profile_count > 0


def test_contains():
    corpus = CorpusSearch()

    assert corpus.contains("Michael Elvis Brockway")


def test_profile_names():
    corpus = CorpusSearch()

    names = corpus.profile_names()

    assert isinstance(names, list)
    assert len(names) > 0


def test_search():
    corpus = CorpusSearch()

    results = corpus.search(
        "Michael Elvis Brockway",
        top_n=5,
    )

    assert len(results) == 5