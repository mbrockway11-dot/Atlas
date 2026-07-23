"""Deprecated alias — use scripts/compile_identity_vectors_batch.py.

Kept only so existing invocations keep working. Delegates to the canonical
batch compiler CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compile_identity_vectors_batch import main  # noqa: E402


if __name__ == "__main__":
    print(
        "[deprecated] use scripts/compile_identity_vectors_batch.py",
        file=sys.stderr,
    )
    sys.exit(main())
