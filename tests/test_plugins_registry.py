from atlas.core.context import ResearchContext
from atlas.core.pipeline import run_core_pipeline
from atlas.plugins.registry import build_default_registry, default_enabled_plugins


def sample_context() -> ResearchContext:
    return ResearchContext(
        profile_key="alpha",
        display_name="Alpha",
        profile_dir="output/library/profiles/alpha",
    )


def test_default_registry_contains_identity_and_intelligence():
    registry = build_default_registry()

    assert registry.names() == ["identity", "intelligence"]


def test_default_enabled_plugins_are_declared():
    assert default_enabled_plugins() == {"identity", "intelligence"}


def test_default_registry_orders_identity_before_intelligence():
    registry = build_default_registry()
    ordered = registry.ordered(enabled={"identity", "intelligence"})

    assert [plugin.name for plugin in ordered] == ["identity", "intelligence"]


def test_identity_plugin_can_run_alone():
    registry = build_default_registry()

    result = run_core_pipeline(
        sample_context(),
        registry=registry,
        enabled={"identity"},
    )

    assert result.data["identity"]["display_name"] == "Alpha"
    assert any(item["section"] == "identity" for item in result.provenance)