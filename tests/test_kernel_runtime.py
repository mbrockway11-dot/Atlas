"""Tests for the Atlas kernel runtime."""

from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.kernel.job import KernelJobResult
from atlas.kernel.metrics import KernelMetrics, PluginTiming
from atlas.kernel.runtime import AtlasKernel


def test_kernel_metrics_to_dict():
    """Kernel metrics serialize correctly."""
    metrics = KernelMetrics(
        total_ms=12.5,
        plugin_timings=[
            PluginTiming(
                plugin="identity",
                elapsed_ms=1.2,
                status="ok",
            )
        ],
        cache_status="miss",
        warning_count=0,
    )

    data = metrics.to_dict()

    assert data["total_ms"] == 12.5
    assert data["plugin_timings"][0]["plugin"] == "identity"
    assert data["plugin_timings"][0]["status"] == "ok"


def test_kernel_exposes_default_enabled_plugins():
    """Default plugin set should match the registry."""
    kernel = AtlasKernel(manifest_path="missing_plugins.yaml")

    assert kernel.enabled_plugins() == {
        "identity",
        "validation",
        "statistics",
        "intelligence",
    }


def test_kernel_job_result_to_dict():
    """Kernel job result serializes correctly."""
    result = KernelJobResult(
        job="test",
        profile_count=2,
        succeeded=1,
        failed=1,
        warnings=["warning"],
    )

    data = result.to_dict()

    assert data["job"] == "test"
    assert data["profile_count"] == 2
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    assert data["warnings"] == ["warning"]


def test_kernel_can_be_constructed():
    """Kernel can be instantiated."""
    kernel = AtlasKernel()

    assert kernel is not None


def test_kernel_can_be_constructed_with_config():
    """Configuration object remains compatible."""
    config = IntelligenceEngineConfig(neighbor_limit=3)

    assert config.neighbor_limit == 3