"""Signed, expiring approvals for Atlas remediation plans.

Approvals authorize one exact remediation-plan hash. They do not authorize
arbitrary execution or future versions of a plan.

The signing secret is supplied through ``ATLAS_APPROVAL_SECRET`` and is never
written to disk.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping


APPROVAL_VERSION = "1.0.0"
APPROVAL_SECRET_ENV = (
    "ATLAS_APPROVAL_SECRET"
)

OUTPUT_DIR = Path(
    "output/atlas_control_plane"
)

REMEDIATION_PLAN_JSON = (
    OUTPUT_DIR
    / "remediation_plan.json"
)

APPROVAL_JSON = (
    OUTPUT_DIR
    / "remediation_approval.json"
)


def canonical_plan_payload(
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the immutable subset covered by approval."""
    execution_steps = [
        {
            "step": int(
                item.get(
                    "step",
                    0,
                )
            ),
            "job_id": str(
                item.get(
                    "job_id",
                    "",
                )
            ),
            "dependencies": str(
                item.get(
                    "dependencies",
                    "",
                )
            ),
            "command": str(
                item.get(
                    "command",
                    "",
                )
            ),
            "output_path": str(
                item.get(
                    "output_path",
                    "",
                )
            ),
        }
        for item in plan.get(
            "execution_steps",
            [],
        )
        if isinstance(item, Mapping)
    ]

    execution = plan.get(
        "execution",
        {},
    )

    if not isinstance(
        execution,
        Mapping,
    ):
        execution = {}

    return {
        "plan_version": str(
            plan.get(
                "version",
                "",
            )
        ),
        "plan_status": str(
            plan.get(
                "plan_status",
                "",
            )
        ),
        "source_health_status": str(
            plan.get(
                "source_health_status",
                "",
            )
        ),
        "execution_mode": str(
            execution.get(
                "mode",
                "NONE",
            )
        ),
        "execution_steps": (
            execution_steps
        ),
    }


def remediation_plan_hash(
    plan: Mapping[str, Any],
) -> str:
    """Hash the exact executable plan content."""
    encoded = json.dumps(
        canonical_plan_payload(plan),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def approval_signature_payload(
    approval: Mapping[str, Any],
) -> dict[str, Any]:
    """Return approval fields covered by the HMAC signature."""
    return {
        "version": str(
            approval.get(
                "version",
                "",
            )
        ),
        "approval_id": str(
            approval.get(
                "approval_id",
                "",
            )
        ),
        "plan_hash": str(
            approval.get(
                "plan_hash",
                "",
            )
        ),
        "approved_by": str(
            approval.get(
                "approved_by",
                "",
            )
        ),
        "approved_at": str(
            approval.get(
                "approved_at",
                "",
            )
        ),
        "expires_at": str(
            approval.get(
                "expires_at",
                "",
            )
        ),
        "execution_mode": str(
            approval.get(
                "execution_mode",
                "",
            )
        ),
        "approved_job_ids": list(
            approval.get(
                "approved_job_ids",
                [],
            )
        ),
        "max_steps": int(
            approval.get(
                "max_steps",
                0,
            )
        ),
        "nonce": str(
            approval.get(
                "nonce",
                "",
            )
        ),
    }


def sign_approval(
    approval: Mapping[str, Any],
    *,
    secret: str,
) -> str:
    """Create an HMAC-SHA256 approval signature."""
    encoded = json.dumps(
        approval_signature_payload(
            approval
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hmac.new(
        secret.encode("utf-8"),
        encoded,
        hashlib.sha256,
    ).hexdigest()


def create_approval(
    plan: Mapping[str, Any],
    *,
    approved_by: str,
    ttl_minutes: int = 30,
    max_steps: int | None = None,
    secret: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Create a signed approval for one exact remediation plan."""
    signing_secret = (
        secret
        or os.environ.get(
            APPROVAL_SECRET_ENV,
            "",
        )
    )

    if not signing_secret:
        raise ValueError(
            f"{APPROVAL_SECRET_ENV} is required."
        )

    if not approved_by.strip():
        raise ValueError(
            "approved_by is required."
        )

    if str(
        plan.get(
            "plan_status",
            "",
        )
    ) != "READY":
        raise ValueError(
            "Only READY remediation plans "
            "can be approved."
        )

    execution = plan.get(
        "execution",
        {},
    )

    if not isinstance(
        execution,
        Mapping,
    ):
        execution = {}

    if not bool(
        execution.get(
            "executable",
            False,
        )
    ):
        raise ValueError(
            "Remediation plan is not executable."
        )

    steps = [
        item
        for item in plan.get(
            "execution_steps",
            [],
        )
        if isinstance(item, Mapping)
    ]

    if not steps:
        raise ValueError(
            "Remediation plan has no execution steps."
        )

    approved_steps = (
        len(steps)
        if max_steps is None
        else min(
            max(1, int(max_steps)),
            len(steps),
        )
    )

    approved_job_ids = [
        str(item["job_id"])
        for item in steps[
            :approved_steps
        ]
    ]

    reference_time = (
        now
        or datetime.now(UTC)
    )

    approval = {
        "version": APPROVAL_VERSION,
        "approval_id": (
            "APPROVAL-"
            + secrets.token_hex(12)
        ),
        "plan_hash": (
            remediation_plan_hash(
                plan
            )
        ),
        "approved_by": (
            approved_by.strip()
        ),
        "approved_at": (
            reference_time.isoformat()
        ),
        "expires_at": (
            reference_time
            + timedelta(
                minutes=max(
                    1,
                    int(ttl_minutes),
                )
            )
        ).isoformat(),
        "execution_mode": str(
            execution.get(
                "mode",
                "EXECUTE",
            )
        ),
        "approved_job_ids": (
            approved_job_ids
        ),
        "max_steps": approved_steps,
        "nonce": secrets.token_hex(16),
        "used": False,
        "used_at": "",
        "dispatch_run_id": "",
    }

    approval["signature"] = (
        sign_approval(
            approval,
            secret=signing_secret,
        )
    )

    return approval


def validate_approval(
    *,
    plan: Mapping[str, Any],
    approval: Mapping[str, Any],
    secret: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate signature, plan hash, expiry, status, and approved jobs."""
    signing_secret = (
        secret
        or os.environ.get(
            APPROVAL_SECRET_ENV,
            "",
        )
    )

    errors: list[str] = []

    if not signing_secret:
        errors.append(
            "APPROVAL_SECRET_MISSING"
        )

    expected_plan_hash = (
        remediation_plan_hash(
            plan
        )
    )

    if str(
        approval.get(
            "plan_hash",
            "",
        )
    ) != expected_plan_hash:
        errors.append(
            "PLAN_HASH_MISMATCH"
        )

    signature = str(
        approval.get(
            "signature",
            "",
        )
    )

    if signing_secret:
        expected_signature = (
            sign_approval(
                approval,
                secret=signing_secret,
            )
        )

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):
            errors.append(
                "SIGNATURE_INVALID"
            )

    reference_time = (
        now
        or datetime.now(UTC)
    )

    try:
        expires_at = (
            datetime.fromisoformat(
                str(
                    approval.get(
                        "expires_at",
                        "",
                    )
                ).replace(
                    "Z",
                    "+00:00",
                )
            )
        )

        if reference_time >= expires_at:
            errors.append(
                "APPROVAL_EXPIRED"
            )
    except ValueError:
        errors.append(
            "APPROVAL_EXPIRY_INVALID"
        )

    if bool(
        approval.get(
            "used",
            False,
        )
    ):
        errors.append(
            "APPROVAL_ALREADY_USED"
        )

    if str(
        plan.get(
            "plan_status",
            "",
        )
    ) != "READY":
        errors.append(
            "PLAN_NOT_READY"
        )

    plan_job_ids = [
        str(item.get("job_id", ""))
        for item in plan.get(
            "execution_steps",
            [],
        )
        if isinstance(item, Mapping)
    ]

    approved_job_ids = [
        str(value)
        for value in approval.get(
            "approved_job_ids",
            [],
        )
    ]

    if not approved_job_ids:
        errors.append(
            "NO_APPROVED_JOBS"
        )

    if approved_job_ids != plan_job_ids[
        :len(approved_job_ids)
    ]:
        errors.append(
            "APPROVED_JOB_ORDER_MISMATCH"
        )

    if int(
        approval.get(
            "max_steps",
            0,
        )
    ) != len(approved_job_ids):
        errors.append(
            "MAX_STEPS_MISMATCH"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "plan_hash": (
            expected_plan_hash
        ),
        "approved_job_ids": (
            approved_job_ids
        ),
        "approved_by": str(
            approval.get(
                "approved_by",
                "",
            )
        ),
        "approval_id": str(
            approval.get(
                "approval_id",
                "",
            )
        ),
    }


def write_approval(
    approval: Mapping[str, Any],
    path: Path = APPROVAL_JSON,
) -> None:
    """Write approval atomically."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(approval),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def load_json(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            str(path)
        )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(payload, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return payload


def mark_approval_used(
    approval: Mapping[str, Any],
    *,
    run_id: str,
    path: Path = APPROVAL_JSON,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Consume an approval after dispatch begins."""
    updated = dict(approval)

    updated["used"] = True
    updated["used_at"] = (
        now
        or datetime.now(UTC)
    ).isoformat()
    updated["dispatch_run_id"] = (
        str(run_id)
    )

    write_approval(
        updated,
        path,
    )

    return updated


__all__ = [
    "APPROVAL_JSON",
    "APPROVAL_SECRET_ENV",
    "APPROVAL_VERSION",
    "REMEDIATION_PLAN_JSON",
    "approval_signature_payload",
    "create_approval",
    "load_json",
    "mark_approval_used",
    "remediation_plan_hash",
    "sign_approval",
    "validate_approval",
    "write_approval",
]
