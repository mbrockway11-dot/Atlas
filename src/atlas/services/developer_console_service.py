"""Developer Console service layer."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from atlas.kernel import AtlasKernel
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


DASHBOARD_DIR = Path("dashboard/pages")
SERVICES_DIR = Path("src/atlas/services")
PLUGIN_ORDER = [
    "identity",
    "research_session",
    "temporal",
    "validation",
    "statistics",
    "topology",
    "intelligence",
]


def build_developer_console_payload() -> dict[str, Any]:
    """Build Developer Console status payload."""
    return {
        "success": True,
        "system": build_system_status(),
        "kernel": build_kernel_status(),
        "plugins": build_plugin_status(),
        "services": build_service_inventory(),
        "dashboards": build_dashboard_inventory(),
        "corpus": build_corpus_status(),
        "audit": run_dashboard_audit(),
    }


def build_system_status() -> dict[str, Any]:
    """Return general system status."""
    profiles = list_saved_profiles()

    return {
        "saved_profiles": len(profiles),
        "profile_library_dir": str(LIBRARY_DIR),
        "kernel_available": kernel_available(),
        "developer_console": "active",
    }


def build_kernel_status() -> dict[str, Any]:
    """Return kernel status."""
    try:
        kernel = AtlasKernel()
        return {
            "available": True,
            "class": kernel.__class__.__name__,
            "defaults": {
                "enabled_plugins": PLUGIN_ORDER,
            },
        }
    except Exception as exc:
        return {
            "available": False,
            "error": str(exc),
            "defaults": {
                "enabled_plugins": PLUGIN_ORDER,
            },
        }


def build_plugin_status() -> dict[str, Any]:
    """Return plugin status."""
    return {
        "count": len(PLUGIN_ORDER),
        "default_order": PLUGIN_ORDER,
        "plugins": [
            {
                "name": name,
                "order": index + 1,
                "enabled_by_default": True,
            }
            for index, name in enumerate(PLUGIN_ORDER)
        ],
    }


def build_service_inventory() -> dict[str, Any]:
    """Return service-layer inventory."""
    if not SERVICES_DIR.exists():
        return {
            "exists": False,
            "count": 0,
            "services": [],
        }

    service_files = sorted(SERVICES_DIR.glob("*_service.py"))

    return {
        "exists": True,
        "count": len(service_files),
        "services": [
            {
                "name": path.stem,
                "path": str(path),
            }
            for path in service_files
        ],
    }


def build_dashboard_inventory() -> dict[str, Any]:
    """Return dashboard page inventory."""
    if not DASHBOARD_DIR.exists():
        return {
            "exists": False,
            "count": 0,
            "pages": [],
        }

    page_files = sorted(
        path
        for path in DASHBOARD_DIR.glob("*.py")
        if path.name != "__init__.py"
    )

    return {
        "exists": True,
        "count": len(page_files),
        "pages": [
            {
                "name": path.stem,
                "path": str(path),
                "direct_backend_imports": detect_direct_backend_imports(path),
            }
            for path in page_files
        ],
    }


def build_corpus_status() -> dict[str, Any]:
    """Return corpus/profile artifact completeness."""
    profiles = list_saved_profiles()

    artifact_names = [
        "profile.acf.json",
        "profile.intake.json",
        "profile_interpretation.json",
        "research_session.json",
    ]

    artifact_counts = {name: 0 for name in artifact_names}
    missing_counts = {name: 0 for name in artifact_names}

    for profile_key in profiles:
        profile_dir = LIBRARY_DIR / profile_key

        for artifact in artifact_names:
            if (profile_dir / artifact).exists():
                artifact_counts[artifact] += 1
            else:
                missing_counts[artifact] += 1

    return {
        "profile_count": len(profiles),
        "artifact_counts": artifact_counts,
        "missing_counts": missing_counts,
        "interpretation_ready": artifact_counts["profile_interpretation.json"],
        "research_session_ready": artifact_counts["research_session.json"],
    }


def run_dashboard_audit() -> dict[str, Any]:
    """Run dashboard audit script and capture result."""
    script = Path("scripts/audit_dashboard_atlas_profile.py")

    if not script.exists():
        return {
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": "Audit script not found.",
        }

    result = subprocess.run(
        ["python", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )

    return {
        "available": True,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def detect_direct_backend_imports(path: Path) -> list[str]:
    """Detect direct backend imports inside dashboard pages."""
    forbidden_patterns = [
        "from atlas.research",
        "import atlas.research",
        "atlas.research",
        "from atlas.temporal",
        "import atlas.temporal",
        "atlas.temporal",
        "from atlas.graph",
        "import atlas.graph",
        "atlas.graph",
        "from atlas.calibration",
        "import atlas.calibration",
        "atlas.calibration",
        "from atlas.acf",
        "import atlas.acf",
        "atlas.acf",
    ]

    text = path.read_text(encoding="utf-8")

    return [pattern for pattern in forbidden_patterns if pattern in text]


def kernel_available() -> bool:
    """Return whether AtlasKernel can initialize."""
    try:
        AtlasKernel()
        return True
    except Exception:
        return False