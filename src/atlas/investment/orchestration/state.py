"""Runtime configuration for Atlas autonomous paper orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


ORCHESTRATION_RUNTIME_VERSION = "1.0.0"


@dataclass(frozen=True)
class OrchestrationRuntimeConfig:
    """Runtime arguments injected into approved orchestration commands."""

    targets_file: Path
    market_symbols: tuple[str, ...] = (
        "BTC-USD",
        "ETH-USD",
        "SOL-USD",
    )
    initial_cash: float = 10_000.0
    minimum_cash_weight: float = 0.34
    maximum_total_turnover: float = 0.25
    maximum_order_notional: float = 2_500.0
    maximum_asset_notional: float = 5_000.0
    maximum_gross_exposure: float = 10_000.0
    maximum_intents: int | None = None
    fee_bps: float = 8.0
    slippage_bps: float = 5.0

    def __post_init__(self) -> None:
        targets_file = Path(
            self.targets_file
        )

        symbols = tuple(
            str(symbol)
            .strip()
            .upper()
            for symbol
            in self.market_symbols
            if str(symbol).strip()
        )

        if not symbols:
            raise ValueError(
                "ORCHESTRATION_MARKET_SYMBOLS_REQUIRED"
            )

        if float(
            self.initial_cash
        ) <= 0:
            raise ValueError(
                "ORCHESTRATION_INITIAL_CASH_INVALID"
            )

        for name, value in (
            (
                "minimum_cash_weight",
                self.minimum_cash_weight,
            ),
            (
                "maximum_total_turnover",
                self.maximum_total_turnover,
            ),
        ):
            number = float(
                value
            )

            if not 0.0 <= number <= 1.0:
                raise ValueError(
                    "ORCHESTRATION_WEIGHT_INVALID:"
                    + name
                )

        for name, value in (
            (
                "maximum_order_notional",
                self.maximum_order_notional,
            ),
            (
                "maximum_asset_notional",
                self.maximum_asset_notional,
            ),
            (
                "maximum_gross_exposure",
                self.maximum_gross_exposure,
            ),
        ):
            if float(value) <= 0:
                raise ValueError(
                    "ORCHESTRATION_LIMIT_INVALID:"
                    + name
                )

        if (
            self.maximum_intents
            is not None
            and int(
                self.maximum_intents
            )
            <= 0
        ):
            raise ValueError(
                "ORCHESTRATION_MAXIMUM_INTENTS_INVALID"
            )

        if float(
            self.fee_bps
        ) < 0:
            raise ValueError(
                "ORCHESTRATION_FEE_BPS_INVALID"
            )

        if float(
            self.slippage_bps
        ) < 0:
            raise ValueError(
                "ORCHESTRATION_SLIPPAGE_BPS_INVALID"
            )

        object.__setattr__(
            self,
            "targets_file",
            targets_file,
        )

        object.__setattr__(
            self,
            "market_symbols",
            symbols,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)

        payload["targets_file"] = str(
            self.targets_file
        )

        payload["market_symbols"] = list(
            self.market_symbols
        )

        return payload


def materialize_execution_plan(
    decision: Mapping[
        str,
        Any,
    ],
    *,
    runtime: OrchestrationRuntimeConfig,
) -> dict[str, Any]:
    """Inject controlled runtime arguments into a scheduler command plan."""
    payload = dict(
        decision
    )

    raw_plan = payload.get(
        "execution_plan",
        [],
    )

    if not isinstance(
        raw_plan,
        list,
    ):
        raise ValueError(
            "ORCHESTRATION_EXECUTION_PLAN_NOT_LIST"
        )

    materialized_rows: list[
        dict[str, Any]
    ] = []

    for raw_row in raw_plan:
        if not isinstance(
            raw_row,
            Mapping,
        ):
            raise ValueError(
                "ORCHESTRATION_PLAN_ROW_NOT_OBJECT"
            )

        row = dict(
            raw_row
        )

        name = str(
            row.get(
                "name",
                "",
            )
        ).strip().upper()

        command = build_runtime_command(
            name,
            runtime=runtime,
        )

        materialized_rows.append({
            **row,
            "name": name,
            "command": command,
            "paper_only": True,
        })

    payload[
        "execution_plan"
    ] = materialized_rows

    payload[
        "runtime_configuration"
    ] = runtime.to_dict()

    payload[
        "runtime_contract"
    ] = {
        "arguments_materialized": True,
        "arbitrary_commands_allowed": False,
        "paper_only": True,
        "live_execution": False,
        "credentials_used": False,
    }

    return payload


def build_runtime_command(
    job_name: str,
    *,
    runtime: OrchestrationRuntimeConfig,
) -> list[str]:
    """Build the exact approved argv sequence for one job."""
    normalized = str(
        job_name
    ).strip().upper()

    if normalized == (
        "MARKET_DATA_REFRESH"
    ):
        return [
            "python",
            "scripts/build_coinbase_market_snapshot.py",
            "--symbols",
            ",".join(
                runtime.market_symbols
            ),
        ]

    if normalized == (
        "SHADOW_PIPELINE"
    ):
        command = [
            "python",
            "scripts/run_shadow_portfolio_pipeline.py",
            "--targets-file",
            str(
                runtime.targets_file
            ),
            "--initial-cash",
            number_text(
                runtime.initial_cash
            ),
            "--minimum-cash-weight",
            number_text(
                runtime.minimum_cash_weight
            ),
            "--maximum-total-turnover",
            number_text(
                runtime.maximum_total_turnover
            ),
            "--maximum-order-notional",
            number_text(
                runtime.maximum_order_notional
            ),
            "--maximum-asset-notional",
            number_text(
                runtime.maximum_asset_notional
            ),
            "--maximum-gross-exposure",
            number_text(
                runtime.maximum_gross_exposure
            ),
            "--fee-bps",
            number_text(
                runtime.fee_bps
            ),
            "--slippage-bps",
            number_text(
                runtime.slippage_bps
            ),
        ]

        if runtime.maximum_intents is not None:
            command.extend([
                "--maximum-intents",
                str(
                    int(
                        runtime.maximum_intents
                    )
                ),
            ])

        return command

    if normalized == (
        "EXECUTION_ANALYTICS"
    ):
        return [
            "python",
            "scripts/build_execution_analytics.py",
        ]

    if normalized == (
        "PERFORMANCE_LEDGER"
    ):
        return [
            "python",
            "scripts/record_shadow_performance.py",
        ]

    if normalized == (
        "SYSTEM_AUDIT"
    ):
        return [
            "python",
            "scripts/audit_shadow_performance_ledger.py",
        ]

    raise KeyError(
        "ORCHESTRATION_JOB_UNSUPPORTED:"
        + normalized
    )


def validate_runtime_files(
    runtime: OrchestrationRuntimeConfig,
    *,
    project_root: Path,
) -> dict[str, Any]:
    """Validate local runtime files before command execution."""
    errors: list[str] = []

    targets_path = resolve_project_path(
        runtime.targets_file,
        project_root=project_root,
    )

    if not targets_path.exists():
        errors.append(
            "TARGETS_FILE_MISSING:"
            + str(
                targets_path
            )
        )

    if targets_path.exists() and not (
        targets_path.is_file()
    ):
        errors.append(
            "TARGETS_PATH_NOT_FILE:"
            + str(
                targets_path
            )
        )

    required_scripts = (
        "scripts/build_coinbase_market_snapshot.py",
        "scripts/run_shadow_portfolio_pipeline.py",
        "scripts/build_execution_analytics.py",
        "scripts/record_shadow_performance.py",
        "scripts/audit_shadow_performance_ledger.py",
    )

    missing_scripts = []

    for relative_path in (
        required_scripts
    ):
        candidate = (
            project_root
            / relative_path
        )

        if not candidate.is_file():
            missing_scripts.append(
                relative_path
            )

    errors.extend(
        "ORCHESTRATION_SCRIPT_MISSING:"
        + value
        for value in missing_scripts
    )

    return {
        "valid": not errors,
        "errors": errors,
        "targets_path": str(
            targets_path
        ),
        "required_scripts": list(
            required_scripts
        ),
    }


def resolve_project_path(
    path: Path,
    *,
    project_root: Path,
) -> Path:
    candidate = Path(
        path
    )

    if candidate.is_absolute():
        return candidate

    return (
        project_root
        / candidate
    ).resolve()


def number_text(
    value: float,
) -> str:
    return format(
        float(value),
        ".12g",
    )


__all__ = [
    "ORCHESTRATION_RUNTIME_VERSION",
    "OrchestrationRuntimeConfig",
    "build_runtime_command",
    "materialize_execution_plan",
    "validate_runtime_files",
]
