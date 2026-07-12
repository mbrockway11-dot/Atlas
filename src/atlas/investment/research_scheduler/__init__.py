"""Atlas Research Scheduler v1."""

from atlas.investment.research_scheduler.canonical_registry import (
    JOB_MAP,
    JOBS,
    ResearchJobSpec,
    install_canonical_registry,
)

install_canonical_registry()

from atlas.investment.research_scheduler.fingerprints import (  # noqa: E402
    apply_content_fingerprints,
    hash_file,
    load_fingerprint_state,
    write_fingerprint_state,
)
from atlas.investment.research_scheduler.freshness import (  # noqa: E402
    inspect_all_artifacts,
)
from atlas.investment.research_scheduler.incremental import (  # noqa: E402
    apply_incremental_freshness,
    propagate_dirty_set,
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
    "apply_content_fingerprints",
    "apply_incremental_freshness",
    "build_dependency_graph",
    "build_research_schedule",
    "build_research_scheduler_report",
    "hash_file",
    "inspect_all_artifacts",
    "load_fingerprint_state",
    "propagate_dirty_set",
    "write_fingerprint_state",
    "topological_order",
]
