
"""Population batch compiler."""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.population.compiler.checkpoint import (
    DEFAULT_CHECKPOINT_PATH,
    load_checkpoint,
    mark_compiled,
    mark_failed,
    mark_skipped,
    save_checkpoint,
)
from atlas.population.compiler.validator import payload_exists, validate_intake


def load_profile_keys(names_path: str | Path) -> list[str]:
    path = Path(names_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing names file: {path}")

    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def compile_population_batch(
    profile_keys: list[str],
    *,
    limit: int | None = None,
    force: bool = False,
    checkpoint_path: str | Path = DEFAULT_CHECKPOINT_PATH,
) -> dict[str, Any]:
    if limit is not None:
        profile_keys = profile_keys[:limit]

    checkpoint = load_checkpoint(checkpoint_path)
    compiled_set = set(checkpoint.get("compiled_keys", []))

    attempted = 0
    compiled = 0
    skipped = 0
    failed = 0
    elapsed_values = []

    for index, profile_key in enumerate(profile_keys, start=1):
        if not force and profile_key in compiled_set and payload_exists(profile_key):
            print(f"[{index}/{len(profile_keys)}] SKIP checkpoint: {profile_key}")
            checkpoint = mark_skipped(checkpoint, profile_key)
            skipped += 1
            save_checkpoint(checkpoint, checkpoint_path)
            continue

        if not force and payload_exists(profile_key):
            print(f"[{index}/{len(profile_keys)}] SKIP existing payload: {profile_key}")
            checkpoint = mark_skipped(checkpoint, profile_key)
            skipped += 1
            save_checkpoint(checkpoint, checkpoint_path)
            continue

        valid = validate_intake(profile_key)
        if not valid.get("success"):
            print(f"[{index}/{len(profile_keys)}] FAIL validation: {profile_key}")
            checkpoint = mark_failed(checkpoint, profile_key, valid)
            failed += 1
            save_checkpoint(checkpoint, checkpoint_path)
            continue

        print(f"[{index}/{len(profile_keys)}] COMPILE: {profile_key}")
        attempted += 1

        try:
            started = time.time()
            result = compile_canonical_profile(profile_key, force=force)
            elapsed = round(time.time() - started, 4)

            if result.get("success"):
                compiled += 1
                elapsed_values.append(elapsed)
                checkpoint = mark_compiled(checkpoint, profile_key)
                print(f"  compiled in {elapsed}s")
            else:
                failed += 1
                checkpoint = mark_failed(
                    checkpoint,
                    profile_key,
                    {
                        "success": False,
                        "status": "compile_failed",
                        "profile_key": profile_key,
                        "summary": result.get("summary", ""),
                        "metrics": result.get("metrics", {}),
                    },
                )
                print(f"  failed: {result.get('summary')}")

        except Exception as exc:
            failed += 1
            checkpoint = mark_failed(
                checkpoint,
                profile_key,
                {
                    "success": False,
                    "status": "exception",
                    "profile_key": profile_key,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            print(f"  exception: {exc}")

        save_checkpoint(checkpoint, checkpoint_path)

    report = {
        "success": len(checkpoint.get("failed", {})) == 0,
        "total_keys": len(profile_keys),
        "attempted_this_run": attempted,
        "compiled_this_run": compiled,
        "skipped_this_run": skipped,
        "failed_this_run": failed,
        "tracked_compiled": len(checkpoint.get("compiled_keys", [])),
        "tracked_failed": len(checkpoint.get("failed", {})),
        "average_compile_seconds": round(sum(elapsed_values) / len(elapsed_values), 4) if elapsed_values else 0.0,
        "checkpoint": checkpoint,
        "summary": (
            f"Population Compiler processed {len(profile_keys)} key(s). "
            f"Compiled this run: {compiled}. Skipped: {skipped}. Failed: {failed}."
        ),
    }

    save_checkpoint(checkpoint, checkpoint_path)
    return report
