"""Strict command allowlist for Atlas autonomous paper orchestration."""

from __future__ import annotations

from typing import Iterable, Mapping

from atlas.investment.orchestration.contracts import (
    ApprovedCommand,
)


DEFAULT_APPROVED_COMMANDS = (
    ApprovedCommand(
        job_name=(
            "MARKET_DATA_REFRESH"
        ),
        argv_prefix=(
            "python",
            "scripts/build_coinbase_market_snapshot.py",
        ),
        timeout_seconds=60,
        allow_additional_arguments=True,
    ),
    ApprovedCommand(
        job_name=(
            "SHADOW_PIPELINE"
        ),
        argv_prefix=(
            "python",
            "scripts/run_shadow_portfolio_pipeline.py",
        ),
        timeout_seconds=180,
        allow_additional_arguments=True,
    ),
    ApprovedCommand(
        job_name=(
            "EXECUTION_ANALYTICS"
        ),
        argv_prefix=(
            "python",
            "scripts/build_execution_analytics.py",
        ),
        timeout_seconds=120,
        allow_additional_arguments=False,
    ),
    ApprovedCommand(
        job_name=(
            "PERFORMANCE_LEDGER"
        ),
        argv_prefix=(
            "python",
            "scripts/record_shadow_performance.py",
        ),
        timeout_seconds=120,
        allow_additional_arguments=True,
    ),
    ApprovedCommand(
        job_name=(
            "SYSTEM_AUDIT"
        ),
        argv_prefix=(
            "python",
            "scripts/audit_shadow_performance_ledger.py",
        ),
        timeout_seconds=120,
        allow_additional_arguments=False,
    ),
)


def build_command_registry(
    commands: Iterable[
        ApprovedCommand
    ] = DEFAULT_APPROVED_COMMANDS,
) -> dict[str, ApprovedCommand]:
    """Build and validate the command registry."""
    registry: dict[
        str,
        ApprovedCommand
    ] = {}

    for command in commands:
        if command.job_name in registry:
            raise ValueError(
                "DUPLICATE_APPROVED_COMMAND:"
                + command.job_name
            )

        if not command.paper_only:
            raise ValueError(
                "NON_PAPER_COMMAND_FORBIDDEN:"
                + command.job_name
            )

        registry[
            command.job_name
        ] = command

    return registry


def validate_execution_plan(
    execution_plan: Iterable[
        Mapping[str, object]
    ],
    *,
    registry: Mapping[
        str,
        ApprovedCommand
    ],
) -> dict[str, object]:
    """Validate every planned command against the strict allowlist."""
    errors: list[str] = []
    normalized_rows: list[
        dict[str, object]
    ] = []

    seen: set[str] = set()

    for index, raw_row in enumerate(
        execution_plan
    ):
        row = dict(
            raw_row
        )

        job_name = str(
            row.get(
                "name",
                "",
            )
        ).strip().upper()

        raw_command = row.get(
            "command",
            (),
        )

        if not isinstance(
            raw_command,
            (
                list,
                tuple,
            ),
        ):
            errors.append(
                "COMMAND_NOT_SEQUENCE:"
                + str(index)
            )
            continue

        command = tuple(
            str(value)
            for value
            in raw_command
        )

        if not job_name:
            errors.append(
                "JOB_NAME_MISSING:"
                + str(index)
            )
            continue

        if job_name in seen:
            errors.append(
                "DUPLICATE_PLAN_JOB:"
                + job_name
            )

        seen.add(
            job_name
        )

        approved = registry.get(
            job_name
        )

        if approved is None:
            errors.append(
                "JOB_NOT_ALLOWLISTED:"
                + job_name
            )
            continue

        if not bool(
            row.get(
                "paper_only",
                False,
            )
        ):
            errors.append(
                "PLAN_JOB_NOT_PAPER_ONLY:"
                + job_name
            )

        if not command:
            errors.append(
                "COMMAND_EMPTY:"
                + job_name
            )
            continue

        prefix = approved.argv_prefix

        if command[:len(prefix)] != prefix:
            errors.append(
                "COMMAND_PREFIX_MISMATCH:"
                + job_name
            )
            continue

        if (
            not approved
            .allow_additional_arguments
            and len(command)
            != len(prefix)
        ):
            errors.append(
                "COMMAND_ARGUMENTS_FORBIDDEN:"
                + job_name
            )
            continue

        if any(
            contains_forbidden_token(
                value
            )
            for value in command
        ):
            errors.append(
                "COMMAND_TOKEN_FORBIDDEN:"
                + job_name
            )
            continue

        normalized_rows.append({
            "name": job_name,
            "command": command,
            "paper_only": True,
            "timeout_seconds": (
                approved.timeout_seconds
            ),
        })

    return {
        "valid": not errors,
        "errors": errors,
        "rows": normalized_rows,
        "count": len(
            normalized_rows
        ),
    }


def contains_forbidden_token(
    value: str,
) -> bool:
    """Reject shell syntax and credential-oriented arguments."""
    text = str(
        value
    )

    forbidden_fragments = (
        "&&",
        "||",
        ";",
        "|",
        ">",
        "<",
        "`",
        "$(",
        "\n",
        "\r",
        "--api-key",
        "--api-secret",
        "--private-key",
        "--live",
        "--live-execution",
    )

    lowered = text.lower()

    return any(
        fragment in lowered
        for fragment
        in forbidden_fragments
    )


__all__ = [
    "DEFAULT_APPROVED_COMMANDS",
    "build_command_registry",
    "validate_execution_plan",
]
