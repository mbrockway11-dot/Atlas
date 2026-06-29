from dataclasses import dataclass

from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.intelligence.pipeline import run_intelligence_pipeline
from atlas.intelligence.plugins import PipelineContext
from atlas.intelligence.profile import AtlasProfile
from atlas.services.atlas_profile_service import atlas_profile_cache_path


@dataclass(frozen=True)
class ExamplePlugin:
    name: str = "example"
    order: int = 20

    def execute(self, profile: AtlasProfile, context: PipelineContext) -> AtlasProfile:
        return (
            profile.with_section(
                "example",
                {
                    "ok": True,
                    "metric": context.config.neighbor_limit,
                },
            )
            .with_evidence(
                [
                    {
                        "claim": "example_claim",
                        "source": "tests.ExamplePlugin",
                        "value": {"ok": True},
                        "weight": 0.1,
                    }
                ]
            )
            .with_provenance(
                [
                    {
                        "section": "example",
                        "source": "tests.ExamplePlugin",
                        "role": "Validates plugin execution.",
                    }
                ]
            )
        )


@dataclass(frozen=True)
class FailingPlugin:
    name: str = "failing"
    order: int = 10

    def execute(self, profile: AtlasProfile, context: PipelineContext) -> AtlasProfile:
        raise RuntimeError("intentional failure")


def sample_profile() -> AtlasProfile:
    return AtlasProfile(
        profile_key="alpha",
        display_name="Alpha",
        profile_dir="output/library/profiles/alpha",
    )


def test_atlas_profile_section_updates_are_immutable():
    profile = sample_profile()
    updated = profile.with_section("identity", {"name": "Alpha"})

    assert "identity" not in profile.sections
    assert updated.sections["identity"]["name"] == "Alpha"


def test_pipeline_executes_plugins_in_order_and_adds_sections():
    result = run_intelligence_pipeline(
        sample_profile(),
        config=IntelligenceEngineConfig(neighbor_limit=7),
        plugins=[ExamplePlugin()],
    )

    assert result.sections["example"]["ok"] is True
    assert result.sections["example"]["metric"] == 7
    assert result.evidence[0]["claim"] == "example_claim"
    assert result.provenance[0]["section"] == "example"


def test_pipeline_records_plugin_failures_as_warnings():
    result = run_intelligence_pipeline(
        sample_profile(),
        plugins=[FailingPlugin(), ExamplePlugin()],
    )

    assert any("Plugin failing failed" in warning for warning in result.warnings)
    assert "example" in result.sections


def test_atlas_profile_cache_path_is_json():
    path = atlas_profile_cache_path("folder/profile")
    assert path.name == "folder_profile.json"
    assert "atlas_profile" in str(path)