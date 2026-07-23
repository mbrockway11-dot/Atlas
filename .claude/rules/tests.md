---
paths:
  - "tests/**/*.py"
---

# Testing rules

- Run tests with the venv interpreter: `.venv/Scripts/python.exe -m pytest`.
  A bare `python` misses native deps and fails at collection — that is the
  environment, not the test.
- Baseline is 1,558 passing. State the before/after count when you touch tests.
- Follow the existing harness: `monkeypatch.setattr` to point compilers at a
  temp library, `monkeypatch.chdir` to isolate the `output/` tree. Never write
  into the real `output/` from a test.
- Parity tests (`test_compiled_runtime_parity.py`) assert bit-exact equality,
  not approximate. Keep it that way; do not loosen to `pytest.approx` to make a
  change pass — a non-zero delta there is a real regression.
- Cover the rejection paths, not just the happy path: unsupported schema,
  count mismatch, damaged artifact, unsafe profile key.
