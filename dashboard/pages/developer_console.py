"""Atlas Developer Console dashboard page."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd
import streamlit as st

from atlas.kernel import AtlasKernel
from atlas.plugins.registry import build_default_registry
from atlas.services.profile_service import list_profile_keys


def render_developer_console_page() -> None:
    """Render Atlas developer console."""
    st.header("Developer Console")
    st.caption("System health, plugin registry, cache, Git, and architecture audit visibility.")

    tab_system, tab_plugins, tab_cache, tab_git, tab_audit = st.tabs(
        [
            "System",
            "Plugins",
            "Cache",
            "Git",
            "Architecture Audit",
        ]
    )

    with tab_system:
        render_system_status()

    with tab_plugins:
        render_plugins()

    with tab_cache:
        render_cache_status()

    with tab_git:
        render_git_status()

    with tab_audit:
        render_architecture_audit()


def render_system_status() -> None:
    """Render system status."""
    st.markdown("## System Status")

    profile_keys = list_profile_keys()

    c1, c2, c3 = st.columns(3)
    c1.metric("Saved profiles", len(profile_keys))
    c2.metric("Kernel", "available")
    c3.metric("Developer console", "active")

    st.markdown("### Kernel Defaults")
    kernel = AtlasKernel()
    st.json(
        {
            "manifest_path": kernel.manifest_path,
            "enabled_plugins": sorted(kernel.enabled_plugins()),
        }
    )


def render_plugins() -> None:
    """Render plugin registry."""
    st.markdown("## Plugin Registry")

    registry = build_default_registry()
    plugins = registry.ordered()

    rows = []
    for plugin in plugins:
        rows.append(
            {
                "name": plugin.name,
                "order": plugin.order,
                "depends_on": ", ".join(plugin.depends_on),
                "class": type(plugin).__name__,
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_cache_status() -> None:
    """Render cache status."""
    st.markdown("## Cache Status")

    cache_dirs = [
        Path("output/cache/intelligence"),
        Path("output/cache/atlas_profile"),
    ]

    rows = []
    for cache_dir in cache_dirs:
        files = list(cache_dir.glob("*.json")) if cache_dir.exists() else []
        rows.append(
            {
                "cache": str(cache_dir),
                "exists": cache_dir.exists(),
                "json_files": len(files),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_git_status() -> None:
    """Render Git status."""
    st.markdown("## Git Status")

    commit = run_command(["git", "log", "--oneline", "-1"])
    status = run_command(["git", "status", "--short"])
    branch = run_command(["git", "branch", "--show-current"])

    st.markdown("### Branch")
    st.code(branch or "unknown")

    st.markdown("### Latest Commit")
    st.code(commit or "unknown")

    st.markdown("### Working Tree")
    st.code(status or "clean")


def render_architecture_audit() -> None:
    """Render architecture audit files."""
    st.markdown("## Architecture Audit")

    audit_dir = Path("architecture_audit")

    if not audit_dir.exists():
        st.info("No architecture_audit directory found.")
        return

    files = sorted(audit_dir.glob("*"))

    st.markdown("### Files")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "file": file.name,
                    "size_bytes": file.stat().st_size,
                }
                for file in files
                if file.is_file()
            ]
        ),
        width="stretch",
    )

    inventory_path = audit_dir / "module_inventory.json"
    if inventory_path.exists():
        try:
            data = json.loads(inventory_path.read_text(encoding="utf-8"))
            st.markdown("### Inventory Summary")
            st.json(data.get("summary", {}))
        except json.JSONDecodeError:
            st.warning("module_inventory.json could not be parsed.")


def run_command(command: list[str]) -> str:
    """Run a local command safely for developer diagnostics."""
    try:
        completed = subprocess.run(
            command,
            cwd=Path("."),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return completed.stdout.strip() or completed.stderr.strip()
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
