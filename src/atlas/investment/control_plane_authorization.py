"""Role-based authorization policy for Atlas Control Plane operators.

Roles are resolved from backend configuration. Dashboard users cannot select or
elevate their own role.

Configuration:

    ATLAS_OPERATOR_ROLES_JSON

Example:

    {
      "Michael Brockway": "ADMINISTRATOR",
      "Alice Reviewer": "REVIEWER",
      "Bob Approver": "APPROVER",
      "Carol Dispatcher": "DISPATCHER"
    }

Unknown or missing identities receive the VIEWER role.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping


OPERATOR_ROLES_ENV = (
    "ATLAS_OPERATOR_ROLES_JSON"
)

DEFAULT_ROLE = "VIEWER"

VALID_ROLES = {
    "VIEWER",
    "REVIEWER",
    "APPROVER",
    "DISPATCHER",
    "ADMINISTRATOR",
}

PERMISSIONS = {
    "VIEW_HEALTH",
    "VIEW_REMEDIATION",
    "VIEW_PROVENANCE",
    "VIEW_AUDIT",
    "RUN_PREFLIGHT",
    "CREATE_APPROVAL",
    "DISPATCH_APPROVAL",
    "RECONCILE_DISPATCH",
    "MANAGE_POLICY",
}

ROLE_PERMISSIONS = {
    "VIEWER": {
        "VIEW_HEALTH",
        "VIEW_PROVENANCE",
        "VIEW_AUDIT",
    },
    "REVIEWER": {
        "VIEW_HEALTH",
        "VIEW_REMEDIATION",
        "VIEW_PROVENANCE",
        "VIEW_AUDIT",
        "RUN_PREFLIGHT",
    },
    "APPROVER": {
        "VIEW_HEALTH",
        "VIEW_REMEDIATION",
        "VIEW_PROVENANCE",
        "VIEW_AUDIT",
        "RUN_PREFLIGHT",
        "CREATE_APPROVAL",
    },
    "DISPATCHER": {
        "VIEW_HEALTH",
        "VIEW_REMEDIATION",
        "VIEW_PROVENANCE",
        "VIEW_AUDIT",
        "RUN_PREFLIGHT",
        "DISPATCH_APPROVAL",
        "RECONCILE_DISPATCH",
    },
    "ADMINISTRATOR": set(
        PERMISSIONS
    ),
}

HIGH_RISK_STEP_THRESHOLD = 3


@dataclass(frozen=True)
class AuthorizationDecision:
    """One immutable operator authorization decision."""

    allowed: bool
    operator_id: str
    role: str
    permission: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "operator_id": (
                self.operator_id
            ),
            "role": self.role,
            "permission": (
                self.permission
            ),
            "reason": self.reason,
        }


def load_operator_roles(
    raw_json: str | None = None,
) -> dict[str, str]:
    """Load normalized operator-role assignments."""
    raw = (
        raw_json
        if raw_json is not None
        else os.environ.get(
            OPERATOR_ROLES_ENV,
            "",
        )
    )

    if not raw.strip():
        return {}

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(
        payload,
        Mapping,
    ):
        return {}

    result: dict[str, str] = {}

    for operator_id, role in payload.items():
        identity = str(
            operator_id
        ).strip()

        normalized_role = str(
            role
        ).strip().upper()

        if (
            identity
            and normalized_role
            in VALID_ROLES
        ):
            result[
                identity.casefold()
            ] = normalized_role

    return result


def resolve_operator_role(
    operator_id: str,
    *,
    assignments: Mapping[
        str,
        str,
    ] | None = None,
) -> str:
    """Resolve one operator role, defaulting to VIEWER."""
    identity = str(
        operator_id
    ).strip()

    if not identity:
        return DEFAULT_ROLE

    roles = (
        {
            str(key).casefold(): str(
                value
            ).upper()
            for key, value
            in assignments.items()
        }
        if assignments is not None
        else load_operator_roles()
    )

    role = roles.get(
        identity.casefold(),
        DEFAULT_ROLE,
    )

    return (
        role
        if role in VALID_ROLES
        else DEFAULT_ROLE
    )


def permissions_for_role(
    role: str,
) -> set[str]:
    return set(
        ROLE_PERMISSIONS.get(
            str(role).upper(),
            ROLE_PERMISSIONS[
                DEFAULT_ROLE
            ],
        )
    )


def authorize_operator(
    *,
    operator_id: str,
    permission: str,
    assignments: Mapping[
        str,
        str,
    ] | None = None,
) -> AuthorizationDecision:
    """Authorize one operator permission using backend role policy."""
    normalized_permission = str(
        permission
    ).strip().upper()

    role = resolve_operator_role(
        operator_id,
        assignments=assignments,
    )

    if normalized_permission not in (
        PERMISSIONS
    ):
        return AuthorizationDecision(
            allowed=False,
            operator_id=str(
                operator_id
            ).strip(),
            role=role,
            permission=(
                normalized_permission
            ),
            reason=(
                "UNKNOWN_PERMISSION"
            ),
        )

    allowed = bool(
        normalized_permission
        in permissions_for_role(
            role
        )
    )

    return AuthorizationDecision(
        allowed=allowed,
        operator_id=str(
            operator_id
        ).strip(),
        role=role,
        permission=(
            normalized_permission
        ),
        reason=(
            "AUTHORIZED"
            if allowed
            else "ROLE_PERMISSION_DENIED"
        ),
    )


def require_permission(
    *,
    operator_id: str,
    permission: str,
) -> dict[str, Any]:
    """Raise when the backend policy denies an operation."""
    decision = authorize_operator(
        operator_id=operator_id,
        permission=permission,
    )

    if not decision.allowed:
        raise PermissionError(
            "Operator authorization denied: "
            f"{decision.operator_id or '(missing)'} "
            f"role={decision.role} "
            f"permission={decision.permission} "
            f"reason={decision.reason}"
        )

    return decision.to_dict()


def evaluate_separation_of_duties(
    *,
    approved_by: str,
    dispatched_by: str,
    approved_job_count: int,
    high_risk_threshold: int = (
        HIGH_RISK_STEP_THRESHOLD
    ),
) -> dict[str, Any]:
    """Require different approver and dispatcher identities for high risk."""
    approver = str(
        approved_by
    ).strip()

    dispatcher = str(
        dispatched_by
    ).strip()

    high_risk = bool(
        int(approved_job_count)
        > int(high_risk_threshold)
    )

    same_operator = bool(
        approver
        and dispatcher
        and approver.casefold()
        == dispatcher.casefold()
    )

    allowed = bool(
        not high_risk
        or not same_operator
    )

    return {
        "allowed": allowed,
        "high_risk": high_risk,
        "threshold": int(
            high_risk_threshold
        ),
        "approved_job_count": int(
            approved_job_count
        ),
        "approved_by": approver,
        "dispatched_by": dispatcher,
        "same_operator": (
            same_operator
        ),
        "reason": (
            "SEPARATION_OF_DUTIES_SATISFIED"
            if allowed
            else (
                "HIGH_RISK_APPROVER_DISPATCHER_"
                "MUST_DIFFER"
            )
        ),
    }


def build_operator_capabilities(
    operator_id: str,
) -> dict[str, Any]:
    """Build dashboard-safe capability information."""
    role = resolve_operator_role(
        operator_id
    )

    permissions = sorted(
        permissions_for_role(
            role
        )
    )

    return {
        "operator_id": str(
            operator_id
        ).strip(),
        "role": role,
        "permissions": permissions,
        "can_run_preflight": (
            "RUN_PREFLIGHT"
            in permissions
        ),
        "can_create_approval": (
            "CREATE_APPROVAL"
            in permissions
        ),
        "can_dispatch": (
            "DISPATCH_APPROVAL"
            in permissions
        ),
        "can_reconcile": (
            "RECONCILE_DISPATCH"
            in permissions
        ),
        "policy_configured": bool(
            load_operator_roles()
        ),
    }


__all__ = [
    "DEFAULT_ROLE",
    "HIGH_RISK_STEP_THRESHOLD",
    "OPERATOR_ROLES_ENV",
    "PERMISSIONS",
    "ROLE_PERMISSIONS",
    "VALID_ROLES",
    "AuthorizationDecision",
    "authorize_operator",
    "build_operator_capabilities",
    "evaluate_separation_of_duties",
    "load_operator_roles",
    "permissions_for_role",
    "require_permission",
    "resolve_operator_role",
]
