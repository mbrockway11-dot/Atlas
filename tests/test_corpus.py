from atlas.acf.builder import export_acf_profile
from atlas.corpus.builder import build_research_corpus


def test_build_research_corpus(tmp_path):
    profile_library = tmp_path / "profiles"
    output_directory = tmp_path / "corpus"

    for name in [
        "Michael Elvis Brockway",
        "Nikola Tesla",
        "Isaac Newton",
    ]:
        profile_dir = profile_library / name.lower().replace(" ", "_")
        profile_dir.mkdir(parents=True, exist_ok=True)

        export_acf_profile(
            name=name,
            output_path=profile_dir / "profile.acf.json",
        )

    result = build_research_corpus(
        profile_library=profile_library,
        output_directory=output_directory,
        normalization_mode="percentile",
    )

    assert result["profile_count"] == 3
    assert (output_directory / "vectors.csv").exists()
    assert (output_directory / "metadata.json").exists()
    assert (output_directory / "statistics.json").exists()