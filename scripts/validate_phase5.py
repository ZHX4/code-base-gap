#!/usr/bin/env python3
"""Structural validation for Phase 5 modules and report contract."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "code_base_gap" / "phase5"
SCHEMA = ROOT / "spec" / "schemas" / "phase5-deterministic-scan.schema.json"
REQUIRED = {"__init__.py", "models.py", "runner.py", "fingerprint.py", "sarif.py", "builtin.py", "adapters.py", "pipeline.py", "cli.py"}


def main() -> int:
    actual = {p.name for p in PKG.glob("*.py")}
    missing = REQUIRED - actual
    if missing:
        raise SystemExit(f"missing Phase 5 modules: {sorted(missing)}")
    for path in PKG.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SystemExit("wrong Phase 5 JSON Schema dialect")
    if schema.get("$id") != "https://code-base-gap.dev/schema/phase5-deterministic-scan.schema.json":
        raise SystemExit("wrong Phase 5 schema id")
    if set(schema["$defs"]["finding"]["properties"]["severity"]["enum"]) != {"critical", "high", "medium", "low", "info", "unknown"}:
        raise SystemExit("severity contract mismatch")
    print("Phase 5 structural validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
