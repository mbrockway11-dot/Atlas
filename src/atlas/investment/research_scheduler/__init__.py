"""Atlas Research Scheduler v1."""

from atlas.investment.research_scheduler.canonical_registry import (
    JOB_MAP,
    JOBS,
    ResearchJobSpec,
    install_canonical_registry,
)

install_canonical_registry()

from atlas.investment.research_scheduler.freshness import (  # noqa: E402
    inspect_all_artifacts,
)
from atlas.investment.research_scheduler.report import (  # noqa: E402
    build_research_scheduler_report,
)
from atlas.investment.research_scheduler.scheduler import (  # noqa: E402
    build_dependency_graph,
    build_research_schedule,
    topological_order,
)


__all__ = [
    "JOB_MAP",
    "JOBS",
    "ResearchJobSpec",
    "build_dependency_graph",
    "build_research_schedule",
    "build_research_scheduler_report",
    "inspect_all_artifacts",
    "topological_order",
]
