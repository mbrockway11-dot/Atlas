"""Stable read-only Atlas State API v1."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from atlas.investment.state_api.config import (
    ALLOWED_SECTIONS,
)
from atlas.investment.state_api.errors import (
    StateComponentNotFoundError,
    StateSectionNotFoundError,
)
from atlas.investment.state_api.loader import (
    load_compiled_state,
)


def get_current_state(
    path: Path | str | None = None,
    *,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Return a defensive copy of the current state."""
    return load_compiled_state(
        path,
        use_cache=use_cache,
    )


def get_state_hash(
    path: Path | str | None = None,
) -> str:
    """Return the canonical compiled-state hash."""
    return str(
        get_current_state(path)[
            "state_hash"
        ]
    )


def get_state_metadata(
    path: Path | str | None = None,
) -> dict[str, Any]:
    """Return state metadata without section payloads."""
    state = get_current_state(path)

    return {
        key: copy.deepcopy(
            state.get(key)
        )
        for key in (
            "success",
            "version",
            "schema_version",
            "generated_at",
            "state_hash",
            "summary",
            "validation",
            "contract",
            "source",
        )
        if key in state
    }


def list_sections(
    path: Path | str | None = None,
) -> list[str]:
    """List canonical state sections."""
    sections = get_current_state(
        path
    )["sections"]

    return [
        section
        for section in ALLOWED_SECTIONS
        if section in sections
    ]


def get_section(
    section: str,
    path: Path | str | None = None,
    *,
    required: bool = True,
) -> dict[str, Any]:
    """Return one canonical section."""
    normalized = str(
        section
    ).strip()

    sections = get_current_state(
        path
    )["sections"]

    if normalized not in sections:
        if required:
            raise StateSectionNotFoundError(
                "Atlas state section was not found: "
                f"{normalized}"
            )

        return {}

    payload = sections[
        normalized
    ]

    if not isinstance(
        payload,
        dict,
    ):
        if required:
            raise StateSectionNotFoundError(
                "Atlas state section is malformed: "
                f"{normalized}"
            )

        return {}

    return copy.deepcopy(payload)


def list_components(
    section: str | None = None,
    path: Path | str | None = None,
) -> list[str]:
    """List component IDs globally or within one section."""
    state = get_current_state(path)
    sections = state["sections"]

    if section is not None:
        return sorted(
            get_section(
                section,
                path,
            ).keys()
        )

    components = []

    for section_payload in (
        sections.values()
    ):
        if isinstance(
            section_payload,
            dict,
        ):
            components.extend(
                section_payload.keys()
            )

    return sorted(
        set(components)
    )


def get_component(
    component_id: str,
    *,
    section: str | None = None,
    path: Path | str | None = None,
    required: bool = True,
) -> Any:
    """Return one compiled component payload."""
    component = str(
        component_id
    ).strip()

    if section is not None:
        section_payload = get_section(
            section,
            path,
            required=required,
        )

        if component not in (
            section_payload
        ):
            if required:
                raise StateComponentNotFoundError(
                    "Atlas component was not found: "
                    f"{section}.{component}"
                )

            return None

        return copy.deepcopy(
            section_payload[
                component
            ]
        )

    state = get_current_state(path)

    matches = []

    for section_name, section_payload in (
        state["sections"].items()
    ):
        if (
            isinstance(
                section_payload,
                dict,
            )
            and component
            in section_payload
        ):
            matches.append(
                (
                    section_name,
                    section_payload[
                        component
                    ],
                )
            )

    if not matches:
        if required:
            raise StateComponentNotFoundError(
                "Atlas component was not found: "
                f"{component}"
            )

        return None

    if len(matches) > 1:
        raise StateComponentNotFoundError(
            "Atlas component ID is ambiguous; "
            "specify its section: "
            f"{component}"
        )

    return copy.deepcopy(
        matches[0][1]
    )


def get_market_context(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "market_context",
        path,
    )


def get_alpha_state(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "alpha",
        path,
    )


def get_research_state(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "research",
        path,
    )


def get_ensemble_state(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "ensemble",
        path,
    )


def get_learning_state(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "learning",
        path,
    )


def get_governance_state(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "governance",
        path,
    )


def get_variant_state(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "variants",
        path,
    )


def get_portfolio_state(
    path: Path | str | None = None,
) -> dict[str, Any]:
    return get_section(
        "portfolio",
        path,
    )
