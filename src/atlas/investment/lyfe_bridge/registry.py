"""
Atlas Strategy Registry.

Discovers and validates external strategy decisions without
routing them to risk, approval, portfolio, or execution.

Expected directory structure:

root/
    V32_AB/
        latest_strategy_decision.json
        latest_strategy_decision.manifest.json
    V33_TOPOLOGY/
        latest_strategy_decision.json
        latest_strategy_decision.manifest.json
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .adapter import (
    import_lyfe_strategy_decision,
)
from .contracts import (
    AtlasStrategyInstruction,
)


DEFAULT_DECISION_FILENAME = (
    "latest_strategy_decision.json"
)


@dataclass(frozen=True, slots=True)
class StrategyRegistryFailure:
    strategy_directory: str
    decision_path: str | None
    error_type: str
    error_message: str


@dataclass(frozen=True, slots=True)
class RegisteredStrategy:
    registry_key: str
    strategy_directory: str
    decision_path: str
    instruction: AtlasStrategyInstruction


@dataclass(frozen=True, slots=True)
class StrategyRegistrySnapshot:
    root_directory: str
    registered: tuple[
        RegisteredStrategy,
        ...,
    ] = field(
        default_factory=tuple
    )
    failures: tuple[
        StrategyRegistryFailure,
        ...,
    ] = field(
        default_factory=tuple
    )

    @property
    def registered_count(self) -> int:
        return len(
            self.registered
        )

    @property
    def failure_count(self) -> int:
        return len(
            self.failures
        )

    @property
    def is_clean(self) -> bool:
        return self.failure_count == 0


def strategy_registry_key(
    instruction: AtlasStrategyInstruction,
) -> str:
    return (
        f"{instruction.source_system}:"
        f"{instruction.strategy_id}:"
        f"{instruction.strategy_version}"
    )


def discover_strategy_directories(
    root_directory: str | Path,
) -> list[Path]:
    root = Path(
        root_directory
    )

    if not root.exists():
        raise FileNotFoundError(
            root
        )

    if not root.is_dir():
        raise NotADirectoryError(
            root
        )

    return sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir()
        ),
        key=lambda path: path.name.lower(),
    )


def load_registered_strategy(
    strategy_directory: str | Path,
    *,
    decision_filename: str = (
        DEFAULT_DECISION_FILENAME
    ),
) -> RegisteredStrategy:
    strategy_directory = Path(
        strategy_directory
    )

    decision_path = (
        strategy_directory
        / decision_filename
    )

    if not decision_path.exists():
        raise FileNotFoundError(
            decision_path
        )

    instruction = (
        import_lyfe_strategy_decision(
            decision_path
        )
    )

    key = strategy_registry_key(
        instruction
    )

    return RegisteredStrategy(
        registry_key=key,
        strategy_directory=str(
            strategy_directory
        ),
        decision_path=str(
            decision_path
        ),
        instruction=instruction,
    )


def build_strategy_registry(
    root_directory: str | Path,
    *,
    decision_filename: str = (
        DEFAULT_DECISION_FILENAME
    ),
    strict: bool = False,
) -> StrategyRegistrySnapshot:
    root = Path(
        root_directory
    )

    registered: list[
        RegisteredStrategy
    ] = []

    failures: list[
        StrategyRegistryFailure
    ] = []

    seen_keys: set[str] = set()

    for strategy_directory in (
        discover_strategy_directories(
            root
        )
    ):
        decision_path = (
            strategy_directory
            / decision_filename
        )

        try:
            item = load_registered_strategy(
                strategy_directory,
                decision_filename=(
                    decision_filename
                ),
            )

            if item.registry_key in seen_keys:
                raise ValueError(
                    "Duplicate strategy registry key: "
                    f"{item.registry_key}"
                )

            seen_keys.add(
                item.registry_key
            )

            registered.append(
                item
            )

        except Exception as exc:
            failure = StrategyRegistryFailure(
                strategy_directory=str(
                    strategy_directory
                ),
                decision_path=(
                    str(decision_path)
                    if decision_path.exists()
                    else None
                ),
                error_type=type(
                    exc
                ).__name__,
                error_message=str(
                    exc
                ),
            )

            if strict:
                raise RuntimeError(
                    "Strategy registry discovery "
                    f"failed for {strategy_directory}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            failures.append(
                failure
            )

    registered.sort(
        key=lambda item: (
            item.registry_key,
            item.instruction.signal_timestamp_utc,
            item.instruction.instruction_id,
        )
    )

    failures.sort(
        key=lambda item: (
            item.strategy_directory,
            item.error_type,
            item.error_message,
        )
    )

    return StrategyRegistrySnapshot(
        root_directory=str(
            root
        ),
        registered=tuple(
            registered
        ),
        failures=tuple(
            failures
        ),
    )


def registry_instruction_map(
    snapshot: StrategyRegistrySnapshot,
) -> dict[
    str,
    AtlasStrategyInstruction,
]:
    return {
        item.registry_key:
            item.instruction
        for item in snapshot.registered
    }


def summarize_strategy_registry(
    snapshot: StrategyRegistrySnapshot,
) -> dict:
    return {
        "root_directory":
            snapshot.root_directory,
        "registered_count":
            snapshot.registered_count,
        "failure_count":
            snapshot.failure_count,
        "is_clean":
            snapshot.is_clean,
        "registry_keys": [
            item.registry_key
            for item in snapshot.registered
        ],
        "failures": [
            {
                "strategy_directory":
                    failure.strategy_directory,
                "decision_path":
                    failure.decision_path,
                "error_type":
                    failure.error_type,
                "error_message":
                    failure.error_message,
            }
            for failure in snapshot.failures
        ],
    }
