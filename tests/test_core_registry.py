from dataclasses import dataclass

import pytest

from atlas.core.context import ResearchContext
from atlas.core.manifest import load_enabled_plugins
from atlas.core.pipeline import run_core_pipeline
from atlas.core.registry import PluginRegistry


@dataclass(frozen=True)
class ExamplePlugin:
    name: str
    order: int
    depends_on: tuple[str, ...] = ()

    def execute(self, context: ResearchContext) -> ResearchContext:
        return context.with_data(self.name, True).with_provenance(
            [
                {
                    "section": self.name,
                    "source": "tests.ExamplePlugin",
                    "role": "test plugin",
                }
            ]
        )


@dataclass(frozen=True)
class FailingPlugin:
    name: str = "failing"
    order: int = 10
    depends_on: tuple[str, ...] = ()

    def execute(self, context: ResearchContext) -> ResearchContext:
        raise RuntimeError("intentional failure")


def sample_context() -> ResearchContext:
    return ResearchContext(
        profile_key="alpha",
        display_name="Alpha",
        profile_dir="output/library/profiles/alpha",
    )


def test_context_is_immutable():
    context = sample_context()
    updated = context.with_data("identity", {"name": "Alpha"})

    assert "identity" not in context.data
    assert updated.data["identity"]["name"] == "Alpha"


def test_registry_orders_dependencies_before_dependents():
    registry = PluginRegistry()
    registry.register(ExamplePlugin(name="b", order=1, depends_on=("a",)))
    registry.register(ExamplePlugin(name="a", order=99))

    ordered = registry.ordered()

    assert [plugin.name for plugin in ordered] == ["a", "b"]


def test_registry_detects_duplicate_plugin_names():
    registry = PluginRegistry()
    registry.register(ExamplePlugin(name="a", order=1))

    with pytest.raises(ValueError):
        registry.register(ExamplePlugin(name="a", order=2))


def test_registry_detects_circular_dependencies():
    registry = PluginRegistry()
    registry.register(ExamplePlugin(name="a", order=1, depends_on=("b",)))
    registry.register(ExamplePlugin(name="b", order=2, depends_on=("a",)))

    with pytest.raises(ValueError):
        registry.ordered()


def test_core_pipeline_runs_plugins_and_records_failures():
    registry = PluginRegistry()
    registry.register(FailingPlugin())
    registry.register(ExamplePlugin(name="good", order=20))

    result = run_core_pipeline(sample_context(), registry=registry)

    assert result.data["good"] is True
    assert any("Plugin failing failed" in warning for warning in result.warnings)


def test_manifest_loader_reads_enabled_plugins(tmp_path):
    manifest = tmp_path / "plugins.yaml"
    manifest.write_text(
        """
plugins:
  identity: true
  intelligence: yes
  experimental: false
""",
        encoding="utf-8",
    )

    enabled = load_enabled_plugins(manifest)

    assert enabled == {"identity", "intelligence"}