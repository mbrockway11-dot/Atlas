"""Autonomous paper-only orchestration for Atlas investment workflows."""

from atlas.investment.orchestration.allowlist import (
    DEFAULT_APPROVED_COMMANDS,
    build_command_registry,
    validate_execution_plan,
)
from atlas.investment.orchestration.contracts import (
    ApprovedCommand,
    JobExecutionResult,
    ORCHESTRATION_CONTRACT_VERSION,
    OrchestrationPolicy,
    OrchestrationReport,
)
from atlas.investment.orchestration.engine import (
    execute_orchestration_plan,
)
from atlas.investment.orchestration.persistence import (
    LATEST_ORCHESTRATION_REPORT_JSON,
    ORCHESTRATION_CHECKPOINT_JSON,
    ORCHESTRATION_HISTORY_JSONL,
    load_orchestration_checkpoint,
    read_orchestration_history,
    validate_orchestration_history,
    write_orchestration_outputs,
)
from atlas.investment.orchestration.runner import (
    ProcessResult,
    ProcessRunner,
    SafeSubprocessRunner,
)
from atlas.investment.orchestration.service import (
    ORCHESTRATION_SERVICE_VERSION,
    run_orchestration_service,
)
from atlas.investment.orchestration.state import (
    ORCHESTRATION_RUNTIME_VERSION,
    OrchestrationRuntimeConfig,
    build_runtime_command,
    materialize_execution_plan,
    validate_runtime_files,
)


__all__ = [
    "ApprovedCommand",
    "DEFAULT_APPROVED_COMMANDS",
    "JobExecutionResult",
    "LATEST_ORCHESTRATION_REPORT_JSON",
    "ORCHESTRATION_CHECKPOINT_JSON",
    "ORCHESTRATION_CONTRACT_VERSION",
    "ORCHESTRATION_HISTORY_JSONL",
    "ORCHESTRATION_RUNTIME_VERSION",
    "ORCHESTRATION_SERVICE_VERSION",
    "OrchestrationPolicy",
    "OrchestrationReport",
    "OrchestrationRuntimeConfig",
    "ProcessResult",
    "ProcessRunner",
    "SafeSubprocessRunner",
    "build_command_registry",
    "build_runtime_command",
    "execute_orchestration_plan",
    "load_orchestration_checkpoint",
    "materialize_execution_plan",
    "read_orchestration_history",
    "run_orchestration_service",
    "validate_execution_plan",
    "validate_orchestration_history",
    "validate_runtime_files",
    "write_orchestration_outputs",
]
