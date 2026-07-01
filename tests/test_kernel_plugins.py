from atlas.core.context import ResearchContext
from atlas.kernel.runtime import AtlasKernel
from atlas.plugins.registry import build_default_registry, default_enabled_plugins


def sample_context() -> ResearchContext:
    return ResearchContext(
        profile_key="alpha",
        display_name="Alpha",
        profile_dir="output/library/profiles/alpha",
    )


def test_default_registry_contains_kernel_plugins():
    registry = build_default_registry()

    assert registry.names() == [
        "identity",
        "intelligence",
        "research_session",
        "statistics",
        "temporal",
        "topology",
        "validation",
    ]


def test_default_enabled_plugins_include_full_kernel_set():
    assert default_enabled_plugins() == {
        "identity",
        "research_session",
        "temporal",
        "validation",
        "statistics",
        "topology",
        "intelligence",
    }


def test_default_registry_dependency_order():
    registry = build_default_registry()
    ordered = registry.ordered(enabled=default_enabled_plugins())

    assert [plugin.name for plugin in ordered] == [
        "identity",
        "research_session",
        "temporal",
        "validation",
        "statistics",
        "topology",
        "intelligence",
    ]


def test_kernel_can_run_identity_only_pipeline():
    kernel = AtlasKernel(manifest_path="missing_plugins.yaml")
    context = sample_context()

    result, metrics = kernel.run_context(context, enabled={"identity"})

    assert result.data["identity"]["display_name"] == "Alpha"
    assert metrics.plugin_timings[0].plugin == "identity"
    assert metrics.plugin_timings[0].status == "ok"


def test_kernel_records_failure_for_unavailable_profile_pipeline():
    kernel = AtlasKernel(manifest_path="missing_plugins.yaml")
    context = sample_context()

    result, metrics = kernel.run_context(
        context,
        enabled={"identity", "intelligence"},
    )

    assert "identity" in result.data
    assert metrics.plugin_timings