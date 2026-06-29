from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.kernel.job import KernelJobResult
from atlas.kernel.metrics import KernelMetrics, PluginTiming
from atlas.kernel.runtime import AtlasKernel


def test_kernel_metrics_to_dict():
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


def test_kernel_exposes_default_enabled_plugins():
    kernel = AtlasKernel(manifest_path="missing_plugins.yaml")

    assert kernel.enabled_plugins() == {"identity", "intelligence"}


def test_kernel_job_result_to_dict():
    result = KernelJobResult(
        job="test",
        profile_count=2,
        succeeded=1,
        failed=1,
        warnings=["x"],
    )

    data = result.to_dict()

    assert data["job"] == "test"
    assert data["failed"] == 1


def test_kernel_can_be_constructed_with_config():
    kernel = AtlasKernel()
    config = IntelligenceEngineConfig(neighbor_limit=3)

    assert kernel is not None
    assert config.neighbor_limit == 3